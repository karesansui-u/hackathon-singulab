# 構造持続理論ベースの文明OSシミュレーション

制度や施策を実行する前に、人々がどう感じ、どう動き、その反応が社会全体へどう跳ね返るかをLLMエージェントで事前検証する**創発反応の観測装置**です。

```text
施策・世界イベント・社会状態を入力する
  -> 属性を持つ人間/国家/組織エージェントが反応する
  -> 感情と行動が row データとして出る
  -> 集団反応へ集約される
  -> 次の社会状態へ戻る
```

https://github.com/user-attachments/assets/e405f2c3-9518-489d-87c3-c155d7fca38b

このリポジトリはハッカソン配布の2D火災シミュレータをベースに、**物理空間の避難**ではなく **心理・制度空間の反応観測** へ骨格を抽象化したものです。

## ドキュメントの入口

| 種別 | パス |
|---|---|
| 製品パッケージ（正本） | [docs/製品パッケージ/README.md](docs/製品パッケージ/README.md) |
| プロダクト実装アーキテクチャ | [docs/製品パッケージ/02_実装仕様/プロダクト実装アーキテクチャ.md](docs/製品パッケージ/02_実装仕様/プロダクト実装アーキテクチャ.md) |
| LLM観測仕様 | [docs/製品パッケージ/03_LLM観測仕様/](docs/製品パッケージ/03_LLM観測仕様/) |
| ハッカソン発表シナリオ | [docs/製品パッケージ/04_発表シナリオ/ハッカソン発表シナリオ.md](docs/製品パッケージ/04_発表シナリオ/ハッカソン発表シナリオ.md) |
| 初期ドメインパック | [domain_packs/agi_youth_japan/README.md](domain_packs/agi_youth_japan/README.md) |
| 旧設計メモ・調査 | [docs/アーカイブ/](docs/アーカイブ/) |

## ドメインパック構成

シミュレーションの入力・観測対象は **ドメインパック単位** で差し替えます。本線パックは [domain_packs/agi_youth_japan](domain_packs/agi_youth_japan) で、AGI/シンギュラリティ時代の日本の若者・現役世代の未来感情を観測対象とします。

| 内容 | パス |
|---|---|
| ドメイン定義 | `domain_packs/agi_youth_japan/domain.yaml` |
| エージェント | `data/youth_agents.tsv`, `working_agents.tsv`, `country_agents.tsv`, `organization_agents.tsv` |
| 本番デモ用パネル（48枠） | `data/demo_panel_48.tsv`（国家12・0〜14歳コホート8・15〜22歳12・23〜40歳8・組織8） |
| 時間設計（71ステップ） | `data/time_schedule.tsv` |
| 世界イベント | `data/world_events.tsv` |
| 国家→日本の波及経路 | `data/country_to_japan_channels.tsv` |
| シナリオ | `scenarios/baseline.yaml`, `scenarios/stress.yaml` |
| プロンプト雛形 | `prompts/` |
| ビューア設定 | `viewer/viewer_config.yaml` |

時間軸は次の3レンジで構成します。

- ステップ 1-60: 直近5年を月次
- ステップ 61-65: 次の5年を年次
- ステップ 66-71: 15年目から40年目までを5年単位

## 必要な環境

- Python 3.8+
- [Claude Code CLI](https://docs.claude.com/claude-code) （`claude`）
- `requirements.txt` のPythonパッケージ
- FFmpeg（動画生成を行う場合のみ）

LLMバックエンドは Claude Code CLI に固定しています。`scripts/run_country_llm_demo.py` などが内部で `claude --model <model>` を subprocess 呼び出しします。サブスクリプト料金内で動くため、APIキー課金は不要です。

## セットアップ

```bash
# 1. 仮想環境
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 2. Claude Code CLI 認証（初回のみ）
claude login
```

## 実行

本線の閉ループrow生成は [scripts/run_closed_loop_llm_demo.py](scripts/run_closed_loop_llm_demo.py) です。国家LLM → 世界から日本社会状態への変換 → 組織LLM → 若者/現役世代LLM → 社会フィードバック、を1ステップずつ繰り返します。

```bash
python3 scripts/run_closed_loop_llm_demo.py \
  --steps 71 \
  --output-dir outputs/runs/closed_loop_llm_71steps_40years
```

同じ `--output-dir` で再実行すると、完了済みの国家step/組織step/エージェントstepはスキップして途中から再開します。

### 介入なし／介入あり比較run

```bash
python3 scripts/run_closed_loop_llm_demo.py \
  --steps 71 \
  --scenario-mode no_intervention \
  --output-dir outputs/runs/no_intervention_71steps_40years

python3 scripts/run_closed_loop_llm_demo.py \
  --steps 71 \
  --scenario-mode structure_intervention \
  --output-dir outputs/runs/structure_intervention_71steps_40years
```

| `--scenario-mode` | 内容 |
|---|---|
| `no_intervention` | `events.tsv` の政策イベント（P系）を除外し、ショックと世界圧力のみを与える |
| `structure_intervention` | 政策イベント（P系）も含む、構造持続論ベースの介入あり |
| `all` | 上記両方を順に実行 |

### 主なオプション

| オプション | デフォルト | 説明 |
|---|---|---|
| `--steps` | `71` | 実行ステップ数 |
| `--start-step` | `1` | 開始ステップ |
| `--model` | `sonnet` | `claude --model` に渡す値 |
| `--country-codes` | `USA,CHN,JPN,...` | 国家エージェントの絞り込み |
| `--agent-ids` | `A01,A02,...,W22` | 15〜22歳・23〜40歳エージェントの絞り込み |
| `--organization-ids` | `O02,...,O15` | 組織エージェントの絞り込み |
| `--agent-panel-tsv` | `demo_panel_48.tsv` | 代表重みパネル |
| `--country-budget` / `--organization-budget` / `--agent-budget` | — | 各層のLLM時間予算（秒） |
| `--timeout` | `420` | LLM 1呼び出しのタイムアウト |
| `--parallel-by-country` / `--parallel-by-organization` / `--parallel-by-agent` | off | 各層を並列実行 |
| `--workers` | `5` | 並列ワーカ数 |
| `--dry-run` | off | 実行コマンドの表示のみ |

## 出力

`outputs/runs/{run_id}/` 配下に以下が生成されます。

| ファイル | 内容 |
|---|---|
| `country_turns.tsv` / `country_turns.jsonl` | 国家LLMの行動・状態 |
| `organization_turns.tsv` | 組織LLMの意思決定 |
| `agent_turns.tsv` | 若者・現役世代の感情・内心・会話・SNS・行動 |
| `agent_feedback.tsv` | 集団反応として集約した社会フィードバック |
| `japan_state.tsv` | 国家出力から変換した日本社会状態 |
| `manifest.json` | run メタデータ |
| `run_log.tsv` | 各 phase のコマンド・所要秒・status |
| `raw/` | 各 step の生レスポンス（監査用） |

LLMには定性評価や指示は与えず、属性・状態・イベントの数値とテキスト記述のみを渡します。出力は固定スキーマの row として保存され、発表時はこの row を再生する設計です。

## 可視化

| ツール | 用途 |
|---|---|
| [visualization/future_emotion_map.html](visualization/future_emotion_map.html) | 4部屋（良好・中立・注意・危険）マップで row データを再生する本番ビューア |
| [visualization/country_llm_demo.html](visualization/country_llm_demo.html) | 国家エージェント単体の閲覧 |
| [visualization/generate_video.py](visualization/generate_video.py) | フレーム画像から MP4 を生成（FFmpeg + Pillow 必要） |

ブラウザビューアは `outputs/runs/{run_id}/` を選択して読み込みます。Chrome / Edge ではディレクトリごと選択できます。

## ドメインパックを差し替える

別ドメインへ転用するときは、`domain_packs/{your_domain}/` を新設し、

- `domain.yaml`（ドメイン定義）
- `data/` 配下のエージェント・イベント・係数 TSV
- `prompts/` の観測プロンプト
- `scenarios/*.yaml` のシナリオ強度
- `viewer/viewer_config.yaml` のUI設定

を上書きします。共通辞書・標準row仕様は `sim_core/defaults/default_v1.yaml` から継承するので、ドメインパック側では差分のみ書きます。詳しくは [高品質なドメインパックの作り方.md](docs/製品パッケージ/02_実装仕様/高品質なドメインパックの作り方.md) を参照してください。

## ライセンス

GNU General Public License v3.0

詳細は [LICENSE.txt](LICENSE.txt) を参照してください。
