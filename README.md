# LLM Multi-Agent 2D Simulation

## 概要

LLMエージェントの**創発性**と**自律性**を発現させることを目的とした2次元空間マルチエージェントシミュレーション。エージェントには生の数値データ（占有率、火災の強度・距離等）のみを提供し、行動指示や定性的評価（「危険」「快適」等）は一切与えない。エージェント自身が状況を解釈し、意思決定・コミュニケーションを通じて集団的な行動パターンが創発する様子を観察する。

**フィールドに複数の場所（デフォルトでは左側と右側にバーが1つずつ）が存在し、各場所は独立した収容上限（capacity）を持つ。シミュレーション途中で火災イベントも発生する。**


https://github.com/user-attachments/assets/e405f2c3-9518-489d-87c3-c155d7fca38b

デモ動画：火災近傍では、単純な退避にとどまらず、合流指示・物資確保・他者待機・監視などの創発的な判断が観察された。

### Fire Event（火事イベント）

シミュレーションの途中で、指定位置（またはランダムな位置）に複数の火事を発生させることができます。火事には以下の特徴があります:

- **知覚モデルB（距離依存）**: 火事の知覚半径（`radius`）内にいるエージェントのみが火事情報を直接受け取る。半径外のエージェントはプロンプトに火事情報が一切含まれず、他エージェントからのメッセージ経由でのみ間接的に知る
- **定量情報のみ**: エージェントに与えられるのは火事の位置、強度（0.0-1.0）、半径、自分との距離のみ。「危険」「避難すべき」等の定性的な記述は一切含まれない
- **時間不変**: 火事の強度・位置は発生後変化しない
- **発生前は無情報**: 火事が発生するステップより前のプロンプトには、火事に関するセクションは存在しない

この設計により、エージェントが定量情報のみからどのような行動（回避、情報伝達、無視等）を創発的に生み出すかを観察できます。

各エージェントには**ペルソナ（性別: male/female）**がランダムに割り当てられ、LLMプロンプトや近隣エージェント情報に性別が含まれます。エージェントは相手の性別を認識した上でコミュニケーションや意思決定を行います。

さらに、任意で**経済レイヤー**を有効化できます。このレイヤーでは、LLMによる自動化で仕事が段階的に失われ、失職したエージェントは通常の賃金だけでなく、秩序維持・火災下の協調・混雑緩和などによって得られる**structure credits（構造持続通貨）**でも生活できます。これにより、「逃げる」「集まる」だけでなく、「情報を整理する」「他者の選択肢を増やす」行為がシミュレーション内で経済的意味を持ちます。

## 必要な環境

- Python 3.8以上
- Ollama または外部LLM CLI
- 必要なPythonパッケージ（requirements.txt参照）
- FFmpeg（動画生成を行う場合のみ）

## セットアップ

### 1. 仮想環境の作成とセットアップ

#### macOS/Linux の場合:
```bash
# セットアップスクリプトを実行（推奨）
chmod +x setup_mac.sh
./setup_mac.sh

# または手動でセットアップ
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Windows の場合:
```cmd
REM セットアップスクリプトを実行（推奨）
setup_win.bat

REM または手動でセットアップ
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 仮想環境の有効化

#### macOS/Linux:
```bash
source venv/bin/activate
```

#### Windows:
```cmd
venv\Scripts\activate.bat
```

### 3. LLMバックエンドのセットアップ

このプロジェクトは `llm.provider` でバックエンドを切り替えられます。

- `ollama`: 既存どおり Ollama API を使用
- `command`: 任意のCLIコマンドを subprocess 経由で実行

まずは最も安定している `ollama` の設定方法を説明します。

#### `provider: ollama` の場合

#### Ollamaのインストール
   - [Ollama](https://ollama.ai/)をインストール

#### Ollamaサーバーの起動

Ollamaは通常、インストール時に自動的にバックグラウンドサービスとして起動します。しかし、手動で起動する必要がある場合や、APIサーバーとして明示的に起動したい場合は、以下の手順を実行してください:

**方法1: 別のターミナルで手動起動（推奨）**
```bash
# 新しいターミナルを開いて実行
ollama serve
```

これにより、デフォルトで`http://localhost:11434`でサーバーが起動します。

**方法2: バックグラウンドで起動（macOS/Linux）**
```bash
ollama serve &
```

**Ollamaサーバーの状態確認**
```bash
# サーバーが起動しているか確認
curl http://localhost:11434/api/tags
```

正常に起動していれば、モデルリストがJSON形式で返されます。

#### モデルのダウンロードと選択

**利用可能なモデルの確認**:
```bash
# Ollamaにダウンロード済みのモデル一覧を表示
ollama list
```

**モデルのダウンロード**:
```bash
# 使用するモデルをダウンロード（例: llama3.2）
ollama pull llama3.2

# または他のモデルを使用する場合
ollama pull llama3.1
ollama pull mistral
ollama pull qwen2.5
```

**モデルの選択**:
- シミュレーションは`config.yaml`の`llm.model`で指定されたモデルを使用します
- **重要**: `config.yaml`の`llm.model`を、ご自身の環境にインストール済みのモデル名に変更してください:

```yaml
llm:
  model: "llama3.2"  # 使用したいモデル名に変更（ollama list で確認）
```

**モデル名の指定方法**:
- **推奨**: `ollama list`で表示される形式をそのまま使用（例: `qwen2.5:latest`）
- **省略可能**: タグが`:latest`の場合は、タグを省略しても動作します（例: `qwen2.5`）
- **例**:
  - `qwen2.5:latest` ✅ （推奨）
  - `qwen2.5` ✅ （`:latest`を省略）
  - `llama3.2:latest` ✅
  - `llama3.2` ✅
  - `gpt-oss:20b` ✅ （特定のタグを指定）

**注意**: 
- `config.yaml`の`llm.model`で指定したモデル名と一致するモデルが使用されます
- 指定したモデルが存在しない場合、シミュレーション開始時にエラーメッセージが表示されます
- 複数のモデルがダウンロードされていても、`config.yaml`で指定した1つのモデルのみが使用されます
- `ollama list`で表示される`NAME`列の値をそのまま使用するのが最も確実です

### 4. 設定ファイルの確認
   - `config.yaml`でパラメータを確認・調整
   - `provider: ollama` を使う場合は、**特に `llm.model` を、ご自身の環境にインストール済みのモデル名に変更してください**（`ollama list` で確認できます）
   - `provider: command` を使う場合は、実行したいCLIコマンドを `llm.command` に設定してください

#### `provider: command` の場合

`command` バックエンドでは、外部CLIを1回のプロンプト呼び出しとして使えます。各エージェントの1推論ごとにコマンドを起動するため、Ollamaよりオーバーヘッドは大きめです。

最小構成は以下です。

```yaml
llm:
  provider: "command"
  command:
    - "your-cli"
    - "{prompt}"
```

`{prompt}` を `command` に含めると、その位置にプロンプト文字列が埋め込まれます。`{prompt}` を使わない場合は、デフォルトで最後の引数として追加されます。CLIが標準入力から受け取る場合は `prompt_mode: "stdin"` を使います。

Claude Code CLI を使う例:

```yaml
llm:
  provider: "command"
  command:
    - "claude"
    - "-p"
    - "--output-format"
    - "json"
    - "{prompt}"
  response_format: "json"
  response_json_field: "result"
  timeout_seconds: 180
```

このリポジトリには、すぐ試せる Claude Code CLI 用の設定ファイルも含めています。

- `config.claude.smoke.yaml`: 小さく安全に試すための設定
- `config.claude.yaml`: 通常サイズの設定

初回は以下を推奨します。

```bash
claude --version
python main.py --config config.claude.smoke.yaml
```

`claude` が未認証なら、事前に `claude login` を実行してください。

Codex CLI を使う例:

このリポジトリには、Codex 用のラッパースクリプト [scripts/run_codex_prompt.sh](/Users/sunagawa/Project/hackathon-singulab/scripts/run_codex_prompt.sh:1) と設定ファイルも含めています。

- `config.codex.smoke.yaml`: 小さく安全に試すための設定
- `config.codex.yaml`: 通常サイズの設定

最初に一度だけログインしておけば、その後は設定ファイル経由でそのまま実行できます。

```bash
codex login
python main.py --config config.codex.smoke.yaml
```

通常実行:

```bash
python main.py --config config.codex.yaml
```

必要ならモデルだけ後から変えることもできます。

```bash
CODEX_MODEL=gpt-5.4 python main.py --config config.codex.smoke.yaml
```

Codex など別のCLIを使う場合も同じ仕組みで差し替えできます。ただし、CLIによっては人間向けの進捗表示やツール実行を含むことがあるため、**このシミュレーション向けには最終テキストだけを返す薄いラッパースクリプトを挟む構成**が安全です。

## 使用方法

**注意**: 
- 実行前に仮想環境を有効化してください
- `provider: ollama` の場合は Ollama サーバーが起動していることを確認してください（`ollama serve`を別のターミナルで実行）
- `provider: command` の場合は設定したCLIコマンドが `PATH` 上で実行できることを確認してください

### 基本的な実行

```bash
# 仮想環境を有効化（まだ有効化していない場合）
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate.bat  # Windows

# シミュレーションを実行
python main.py
```

### 可視化を有効にする

**注意**: WSL環境やGUIが利用できない環境では、`--visualize`オプションは動作しません。代わりに`--save-frames`を使用してください。

```bash
python main.py --visualize
```

### フレームを保存する

```bash
python main.py --save-frames
```

### カスタム設定ファイルを使用

```bash
python main.py --config custom_config.yaml
```

Claude Code CLI を使う例:

```bash
python main.py --config config.claude.smoke.yaml
python main.py --config config.claude.yaml
```

Codex CLI を使う例:

```bash
python main.py --config config.codex.smoke.yaml
python main.py --config config.codex.yaml
```

## 設定ファイル（config.yaml）

主要なパラメータ:

- **simulation**: シミュレーション設定
  - `duration`: シミュレーションステップ数
  - `half_space_size`: 空間の半分のサイズ（例: 25 → 座標範囲は -25 〜 +25）
  - `half_place_size`: 場所の半分のサイズ（各場所の`half_size`が優先されます）

- **agents**: エージェント設定
  - `num_agents`: エージェント数
  - `communication_radius`: 通信半径
  - `memory_limit`: 保存する最大メモリ数（デフォルト: 20）
  - `memory_size`: LLM推論に使用するメモリ数（デフォルト: 5）
  - `message_history_limit`: 保存する最大メッセージ数（デフォルト: 10）
  - `message_context_size`: LLM推論に使用するメッセージ数（デフォルト: 3）

- **economy**: 雇用喪失と構造持続通貨の設定（任意）
  - `enabled`: 経済レイヤーを有効化するか
  - `base_wage`: 雇用されているエージェントが各ステップで得る賃金
  - `living_cost`: 各ステップで支払う生活費
  - `initial_cash_balance`: 初期現金残高
  - `initial_structure_credits`: 初期の構造持続通貨残高
  - `message_reward`: 近隣へ有用なメッセージを送ったときの基礎報酬
  - `fire_coordination_reward`: 火災下での協調メッセージ報酬
  - `decongestion_reward`: 混雑緩和や過密場所からの離脱に対する報酬
  - `fire_escape_reward`: 火災半径から離脱したときの報酬
  - `crowding_threshold`: 「過密」とみなす占有率の閾値
  - `llm_automation.start_step`: LLM自動化による失職が始まるステップ
  - `llm_automation.interval`: 失職イベントの間隔
  - `llm_automation.job_losses_per_wave`: 1回の自動化波で失職する人数
  - `job_types`: 各職種の名前と `automation_risk`

- **places**: 場所設定（複数場所対応、将来的にカフェや図書館などにも拡張可能）
  - 場所のリスト。各場所は以下の設定を持ちます:
    - `name`: 場所名（必須、例: "left_bar", "right_bar", "cafe", "library"）
    - `type`: 場所の種類（必須、例: "bar", "cafe", "library"）
    - `center_x`: 場所の中心X座標（必須）
    - `center_y`: 場所の中心Y座標（必須）
    - `half_size`: 場所の半分のサイズ（必須、場所は中心から±half_sizeの範囲）
    - `capacity`: その場所の収容上限人数（必須、占有率の計算に使用）

  例（現在の設定）:
  ```yaml
  places:
    - name: "left_bar"
      type: "bar"  # 場所の種類: bar, cafe, library など
      center_x: -15
      center_y: 0
      half_size: 5
      capacity: 12
    - name: "right_bar"
      type: "bar"
      center_x: 15
      center_y: 0
      half_size: 5
      capacity: 10
  ```

  将来の拡張例（カフェや図書館など）:
  ```yaml
  places:
    - name: "cafe"
      type: "cafe"
      center_x: -15
      center_y: 0
      half_size: 5
      capacity: 12
    - name: "library"
      type: "library"
      center_x: 15
      center_y: 0
      half_size: 5
      capacity: 10
  ```

- **fires**: 火事イベント設定（複数火事対応）
  - 火事のリスト。各火事は以下の設定を持ちます:
    - `name`: 火事の名前（必須、例: "fire_1"）
    - `start_step`: 火事が発生するステップ（必須）
    - `intensity`: 火事の強度（0.0〜1.0、エージェントには定量値としてのみ伝達）
    - `radius`: 知覚半径（この距離内のエージェントのみ火事情報を直接受け取る）
    - `center_x`: 火事の中心X座標（省略時はランダム位置）
    - `center_y`: 火事の中心Y座標（省略時はランダム位置）

  ```yaml
  fires:
    - name: "fire_1"
      start_step: 15
      intensity: 0.8
      radius: 10
      center_x: 0         # 省略するとランダム位置
      center_y: 0
    - name: "fire_2"
      start_step: 30
      intensity: 0.5
      radius: 8
      center_x: -10
      center_y: 10
  ```

- **llm**: LLM設定（詳細は `config.yaml` を参照）
  - `provider`: `ollama` または `command`
  - `model`: モデル名。`ollama` では必須、`command` では任意の識別子
  - `base_url`: Ollama APIエンドポイント（`provider: ollama` のとき使用）
  - `command`: 実行するCLIコマンド。文字列または配列で指定可能（`provider: command` のとき使用）
  - `prompt_mode`: `auto` / `append_arg` / `stdin`。CLIへのプロンプト渡し方を制御
  - `response_format`: `text` または `json`
  - `response_json_field`: JSON出力から取り出すフィールド名（例: `result`）
  - `timeout_seconds`: CLI実行タイムアウト秒数
  - `env`: CLI実行時に追加する環境変数
  - `temperature`: サンプリング温度（低いほど一貫した行動、高いほど多様な行動）
  - `max_tokens`: 最大トークン数
  - `repeat_penalty`: 反復ペナルティ（同じトークンの繰り返しを抑制）
  - `repeat_last_n`: 反復チェック範囲（繰り返し検出の対象トークン数。`0`で無効、`-1`で`num_ctx`を使用）
  - `min_p`: Min-Pサンプリング（指定確率未満のトークンを除外）

### 座標系について

このシミュレーションは**原点中心の座標系**を使用します:

- **フィールド**: 原点 (0, 0) を中心に、`-half_space_size` 〜 `+half_space_size` の範囲
- **場所**: 各場所は独立した中心位置（`center_x`, `center_y`）を持ち、その中心から`±half_size`の範囲（両端を含む）

**エージェントの知識**:
- エージェントは**すべての場所の位置情報**を知っています（プロンプトに含まれます）
- ただし、場所の占有状況（エージェント数、収容上限、占有率）は、その場所内にいるエージェントのみが直接受け取ります

**モデルの選択について**:
- `provider: ollama` の場合は `config.yaml` の `llm.model` で使用するモデルを指定
- 利用可能な Ollama モデルを確認するには: `ollama list`
- Ollama モデルをダウンロードするには: `ollama pull <モデル名>`
- `provider: command` の場合は `llm.command` が実行可能かどうかが重要で、モデル一覧の確認はCLI側の仕様に依存します

## 出力

- `output/`: 可視化フレームと統計グラフが保存されます
  - 可視化では、エージェントの**性別を色**（男=青、女=赤）、**場所内/外をマーカー形状**（場所内=★、場所外=●）で表現
  - 火事発生後は各火事の**火事中心（赤三角）**と**知覚半径（破線円）**が描画される（複数火事対応）。火事の範囲はintensityに応じた**カラーマップ（YlOrRd）**で塗られ、右側に常時表示される**カラーバー（0.0〜1.0、"Intensity of Fire"）**で強度を確認できる
  - 統計グラフには「火事半径内エージェント数の時系列」サブプロットが追加され、各火事の発生ステップに垂直線が描画される
- `output/messages.jsonl`: エージェント間メッセージ履歴（火事情報の伝播パターンの分析に有用）
- `output/memory_reasoning.jsonl`: エージェントの記憶と推論ログ
- `output/economy_events.jsonl`: 失職イベントと構造持続通貨の発行ログ
- `simulation.log`: シミュレーションログ

## シミュレーション結果の可視化ツール

`visualization/` ディレクトリに、シミュレーション結果を閲覧・動画化するためのツールが含まれています。いずれも `output/` ディレクトリに保存されたフレーム画像（`frame_*.png`）とログファイル（`messages.jsonl`、`memory_reasoning.jsonl`）を読み込んで使用します。

### ブラウザビューア（viewer.html）

シミュレーション結果をブラウザ上でインタラクティブに再生・閲覧できるHTMLビューアです。左側にフレーム画像、右上にエージェント間メッセージ（会話内容+内省）、右下に各エージェントの行動理由と記憶が表示されます。

**使い方**:

1. `visualization/viewer.html` をブラウザで開く
2. シミュレーション結果が入ったディレクトリ（例: `output/`）を選択する
   - **Chrome / Edge（推奨）**: 「ディレクトリを選択」ボタンからフォルダごと選択
   - **Firefox / Safari**: 「ファイルを選択」ボタンから `messages.jsonl` を選択（ただしPNG画像が読み込めない場合があります）
3. ステップごとの画像・メッセージ・行動理由が統合表示される

**操作方法**:

| 操作 | 方法 |
|---|---|
| 再生 / 停止 | 「▶ 再生」ボタン または `Space` キー |
| 前のステップ | 「⏮ 前へ」ボタン または `←` キー |
| 次のステップ | 「⏭ 次へ」ボタン または `→` キー |
| ステップジャンプ | スライダーをドラッグ |
| 再生速度調整 | 速度スライダー（0.5x〜3.0x） |

### 動画生成（generate_video.py）

viewer.html と同様のレイアウト（左: フレーム画像、右上: メッセージ、右下: 思考）でMP4動画を生成するスクリプトです。

**前提条件**: FFmpeg および Pillow がインストールされている必要があります。Pillow は `requirements.txt` に含まれています。

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

**使い方**:

```bash
# 基本的な使い方（output/ ディレクトリから動画を生成）
python visualization/generate_video.py output/

# 出力ファイル名とフレームレートを指定
python visualization/generate_video.py output/ -o result.mp4 --fps 20

# DPIを指定（デフォルト: 150）
python visualization/generate_video.py output/ --dpi 200
```

**オプション**:

| オプション | デフォルト | 説明 |
|---|---|---|
| `data_dir`（必須） | — | シミュレーション結果のディレクトリパス |
| `-o`, `--output` | `simulation.mp4` | 出力MP4ファイル名 |
| `--fps` | `10` | フレームレート（1秒あたりのフレーム数） |
| `--dpi` | `150` | 画像解像度（DPI） |

## LLMエージェント設計

### 基本設計

- 各エージェントは毎ステップ、**Message / Memory / Action** をLLMから生成し、同期的に行動
- 同一のLLMエンジンを全エージェントで共有し、差分は各自のMemoryと相互作用履歴のみ（個性は履歴から創発）
- プロンプトは「最適化タスク」を明示せず、状況説明＋数値データ＋近傍メッセージ＋自己状態を与える構成

### ペルソナ（性別）

- 各エージェントには初期化時に **male** または **female** がランダム（1/2の確率）で割り当てられる
- LLMプロンプトの冒頭（`You are Agent N (male/female)`）および自己状態欄（`Gender:`）に性別が含まれる
- 近隣エージェント情報にも相手の性別が表示される（例: `Agent 3 (female) is outside the places`）
- エージェントは相手の性別を認識した上でメッセージ内容や行動を決定する

### Action（行動）

4方向の離散選択 + 滞在:
- `up`: Y+1（上方向）
- `down`: Y-1（下方向）
- `left`: X-1（左方向）
- `right`: X+1（右方向）
- `stay`: 現在位置に滞在

### Memory（記憶）

- LLMが出力した `memory` フィールドが次ステップの「Previous Memory」として自己フィードバック
- 内部状態が履歴依存で進化し、個性が創発する仕組み
- `memory_limit`: 保存する最大メモリ数（古いものから削除）
- `memory_size`: LLM推論時に参照する直近のメモリ数

### 場所内限定情報

**各場所内のエージェントのみ**が以下の数値データを直接受け取る:
- **現在のエージェント数**（Number of agents here）
- **収容上限**（Capacity）
- **占有率**（Occupancy rate = エージェント数 / 収容上限）

定性的な評価（快適/不快等）は一切含まれず、数値の解釈はエージェント自身に委ねられる。

**場所外のエージェント**はこれらの情報を受け取らない（会話や推論で間接的に学ぶ）

**注意**: エージェントはすべての場所の位置情報を知っていますが、各場所の占有状況はその場所内にいるエージェントのみが知ることができます。

### コミュニケーション

- 通信半径内（デフォルト: 5セル）のエージェント間でメッセージ交換が可能
- **同一領域条件**: 以下の条件を満たすエージェント間でのみ通信可能
  - **両方とも場所外**にいる、または
  - **両方とも同じ場所内**にいる
  
  **通信制限**:
  - ❌ 場所内のエージェント ↔ 場所外のエージェント: **通信不可**
  - ❌ 異なる場所内のエージェント同士: **通信不可**
  - ✅ 同じ場所内のエージェント同士: **通信可能**
  - ✅ 両方とも場所外のエージェント同士: **通信可能**

- `message_history_limit`: 保存する最大メッセージ数（古いものから削除）
- `message_context_size`: LLM推論時に参照する直近のメッセージ数

### シミュレーションステップの実行順序

各ステップは以下の順序で実行されます:

0. **火事活性化チェック** - 各火事について `step >= start_step` の場合、指定位置（またはランダム位置）に火事を発生（各火事1回のみ）
1. **Phase 1: メッセージ決定** - 全エージェントがLLMでメッセージを決定（いずれかの火事の知覚半径内のエージェントには該当する火事情報を含む）
2. **Phase 2: メッセージ送信** - 意思決定時点での近傍エージェントにメッセージを送信
3. **Phase 3: 行動決定** - 全エージェントがLLMで行動（move/stay）を決定（火事情報を含む）
4. **Phase 4: 移動実行** - エージェントが決定した方向に移動

この順序により、メッセージは移動前の位置関係に基づいて送信されます。

### LLM出力形式

**メッセージ決定（Phase 1）**:
```json
{
    "message": "近傍エージェントへのメッセージ（任意、最大200語）",
    "reasoning": "メッセージ送信の理由"
}
```

**行動決定（Phase 3）**:
```json
{
    "action": "move" or "stay",
    "direction": "up", "down", "left", or "right",
    "memory": "次ステップのために記憶したいこと",
    "reasoning": "決定理由"
}
```


## ライセンス

GNU General Public License v3.0

詳細は [LICENSE.txt](LICENSE.txt) を参照してください。
