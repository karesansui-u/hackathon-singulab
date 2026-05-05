# UI生成/API連携シミュレーション作成設計

## 目的

ユーザーがブラウザUIから施策案や検証したい問いを入力し、バックエンドAPI経由でシミュレーション設定を作成し、LLM観測runを生成して、既存ビューアで比較再生できるようにする。

現段階では実装しない。
この文書では「この設計で進めれば実装可能」という境界、API、データ保存、最小実装順序を固定する。

## 結論

実装は可能。

ただし、ブラウザだけで完結させない。
LLM実行、ファイル生成、ジョブ管理、APIキー管理はバックエンド側に置く。

```text
Browser UI
  -> Product API
  -> Draft/Scenario Builder
  -> Domain Pack Validator
  -> Run Job Queue
  -> Simulation Runner
  -> outputs/runs/{run_id}
  -> Viewer Manifest
  -> Browser Viewer
```

GitHub Pagesの静的ビューアは再生専用として残す。
UIから新規生成する場合は、ローカルまたはクラウドのAPIサーバーを立てる。

## 最初のMVP

最初から「任意ドメインを丸ごと作るUI」は作らない。

MVPは、既存の `agi_youth_japan` ドメインパックに対して、ユーザーが新しい施策パッケージ/比較シナリオを作る機能に絞る。

できること:

- ユーザーが施策名、対象、開始step、終了step、強度、副作用、説明文を入力する
- APIが `draft.json` と `scenario.yaml` 相当の構造へ変換する
- 検証に通ればrunジョブを開始する
- 生成後、既存ビューアが新しい比較runとして読み込む

まだやらないこと:

- 完全なドメインパック自動生成
- 複数ユーザー同時編集
- DB前提の重い管理画面
- 本番課金/認証/権限の作り込み
- ブラウザからLLM APIを直接呼ぶ実装

## 役割分離

| 層 | 役割 |
|---|---|
| Browser UI | 入力、確認、進捗表示、再生 |
| Product API | 入力受付、検証、ジョブ作成、run一覧提供 |
| Draft Builder | 自然文やフォーム入力を構造化draftへ変換 |
| Domain Pack Validator | 既存 `sim_core/domain_pack.py` を使って入力を検証 |
| Simulation Runner | 既存 `scripts/run_closed_loop_llm_demo.py` 系を呼び出す |
| Model Adapter | OpenAI/Anthropic/Gemini/CLI/Rule-based を差し替える |
| Storage | draft、入力スナップショット、run出力、viewer manifestを保存 |
| Viewer | `agent_turns.tsv` などのrowデータを読み込んで再生 |

重要なのは、設計補助LLMとシミュレーション観測LLMを分けること。

| LLM | 役割 |
|---|---|
| 設計補助LLM | ユーザー入力から施策案、イベント、仮定、対象を整理する |
| 観測LLM | エージェント、組織、国家の反応rowを生成する |

設計補助LLMは便利な入力補助であり、シミュレーション結果を直接決めない。

## APIキーと.env

APIキーやモデル設定はブラウザに置かない。
ローカルまたはクラウドのバックエンドが `.env` から読む。

例:

```env
SIM_MODEL_BACKEND=openai_api
SIM_DESIGN_MODEL=gpt-5.2
SIM_OBSERVATION_MODEL=gpt-5.2
OPENAI_API_KEY=sk-...

# 別プロバイダへ差し替える場合
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

UIはAPIキーを知らない。
UIは `POST /api/simulation-drafts` へユーザー入力を渡すだけにする。

```text
Browser UI
  -> Product API
      -> .env から model/backend/API key を読む
      -> Draft Builder LLM を呼ぶ
      -> draft.json / scenario.yaml / run_request.json を作る
```

## 設計補助プロンプト

ユーザーの自由入力をそのままrunnerへ渡さない。
まず汎用の設計補助プロンプトで、ドメインパックの設計形式へ変換する。

入力:

- ユーザーの自然文
- 選択中の `domain_pack_id`
- 既存の感情辞書、行動辞書、状態変数、イベント列
- UIフォームの値

出力:

- `draft.json`
- `scenario.yaml` 相当の差分
- `events_override.tsv` 相当のイベント候補
- 検証警告

設計補助プロンプトの役割は、次のJSONを返すこと。

```json
{
  "question": "何を検証するか",
  "target_segments": ["対象集団"],
  "interventions": [
    {
      "name": "施策名",
      "target": "対象",
      "start_step": 1,
      "end_step": 12,
      "intensity_0to1": 0.5,
      "expected_channels": ["影響する状態変数"],
      "possible_side_effects": ["副作用"]
    }
  ],
  "assumptions": [
    {
      "text": "仮定",
      "confidence": "low|medium|high"
    }
  ],
  "validation_notes": ["ユーザー確認が必要な点"]
}
```

その後、通常のPrompt Builderが観測LLM用のプロンプトを作る。

```text
ユーザー入力
  -> 設計補助プロンプト
  -> draft.json
  -> scenario/events/interventions差分
  -> validate
  -> run_request.json
  -> 観測LLMプロンプト
  -> row生成
```

## API設計

### 1. Draft作成

```http
POST /api/simulation-drafts
```

入力:

```json
{
  "domain_pack_id": "agi_youth_japan",
  "title": "若者希望+出産支援パッケージ",
  "user_prompt": "若者が将来に希望を持ち、子どもを持つ選択肢を失わない政策を試したい",
  "mode": "scenario_extension"
}
```

出力:

```json
{
  "draft_id": "draft_20260505_001",
  "status": "draft",
  "next_action": "edit_or_validate"
}
```

### 2. Draft取得

```http
GET /api/simulation-drafts/{draft_id}
```

出力:

```json
{
  "draft_id": "draft_20260505_001",
  "domain_pack_id": "agi_youth_japan",
  "title": "若者希望+出産支援パッケージ",
  "question": "施策導入時に希望、制度信頼、子ども意向、撤退圧がどう変わるか",
  "steps": 83,
  "target_segments": ["15-22", "23-40", "child_cohort"],
  "interventions": [
    {
      "id": "custom_policy_001",
      "name": "住居・休息・代替ケア支援",
      "start_step": 61,
      "end_step": 83,
      "intensity_0to1": 0.72,
      "target": "若者・家族形成世代",
      "expected_channels": ["制度信頼", "生活コスト圧", "修復経路密度"],
      "possible_side_effects": ["非対象者の不公平感", "申請負荷への反発"]
    }
  ],
  "assumptions": [
    {
      "text": "周知は中程度、申請負荷は改善されるがゼロではない",
      "confidence": "medium"
    }
  ]
}
```

### 3. Draft更新

```http
PATCH /api/simulation-drafts/{draft_id}
```

UIのフォーム編集内容を保存する。
この時点ではrunを開始しない。

### 4. Draft検証

```http
POST /api/simulation-drafts/{draft_id}/validate
```

処理:

- draftをscenario/events/interventions相当の内部形式へ変換する
- `domain_packs/{pack_id}/domain.yaml` と結合する
- 必須ファイル、必須列、step範囲、ID参照、値域を検証する

出力:

```json
{
  "ok": true,
  "errors": [],
  "warnings": [
    "possible_side_effects は入力されていますが、定量係数は未指定です"
  ],
  "generated_files": {
    "draft": "outputs/api_drafts/draft_20260505_001/draft.json",
    "scenario": "outputs/api_drafts/draft_20260505_001/scenario.yaml",
    "events": "outputs/api_drafts/draft_20260505_001/events_override.tsv"
  }
}
```

### 5. Run作成

```http
POST /api/simulation-runs
```

入力:

```json
{
  "draft_id": "draft_20260505_001",
  "run_id": "custom_hope_family_20260505_001",
  "model_backend": "openai_api",
  "model_name": "gpt-5.2",
  "steps": 12,
  "dry_run": false
}
```

出力:

```json
{
  "run_id": "custom_hope_family_20260505_001",
  "job_id": "job_20260505_001",
  "status": "queued"
}
```

### 6. Run状態取得

```http
GET /api/simulation-runs/{run_id}
```

出力:

```json
{
  "run_id": "custom_hope_family_20260505_001",
  "status": "running",
  "current_step": 4,
  "total_steps": 12,
  "phase": "agent_llm",
  "started_at": "2026-05-05T12:00:00+09:00",
  "outputs_ready": false
}
```

### 7. Run一覧

```http
GET /api/simulation-runs
```

ビューアが比較候補を表示するために使う。

出力:

```json
{
  "runs": [
    {
      "run_id": "no_intervention_71steps_panel48",
      "label": "介入なし",
      "status": "completed",
      "viewer_manifest": "/api/simulation-runs/no_intervention_71steps_panel48/viewer-manifest"
    },
    {
      "run_id": "custom_hope_family_20260505_001",
      "label": "若者希望+出産支援パッケージ",
      "status": "completed",
      "viewer_manifest": "/api/simulation-runs/custom_hope_family_20260505_001/viewer-manifest"
    }
  ]
}
```

### 8. Viewer Manifest

```http
GET /api/simulation-runs/{run_id}/viewer-manifest
```

出力:

```json
{
  "run_id": "custom_hope_family_20260505_001",
  "label": "若者希望+出産支援パッケージ",
  "files": {
    "agent_turns": "/api/simulation-runs/custom_hope_family_20260505_001/files/agent_turns.tsv",
    "country_turns": "/api/simulation-runs/custom_hope_family_20260505_001/files/country_turns.tsv",
    "auto_events": "/api/simulation-runs/custom_hope_family_20260505_001/files/auto_events_with_feedback.tsv",
    "scheduled_events": "/api/simulation-runs/custom_hope_family_20260505_001/files/scheduled_events_used.tsv"
  }
}
```

既存ビューアの固定 `runConfigs` は、将来的にこのmanifest読み込みへ置き換える。

## 保存レイアウト

最初はDBを使わず、ファイル保存でよい。

```text
outputs/
  api_drafts/
    draft_20260505_001/
      draft.json
      scenario.yaml
      events_override.tsv
      validation_report.json
      generated_at.txt

  jobs/
    job_20260505_001/
      job.json
      status.json
      log.tsv

  runs/
    custom_hope_family_20260505_001/
      manifest.json
      input_snapshot/
      run_request.json
      resolved_config.json
      validation_report.json
      country_turns.tsv
      organization_turns.tsv
      agent_turns.tsv
      agent_feedback.tsv
      japan_state.tsv
      auto_events_with_feedback.tsv
      scheduled_events_used.tsv
      raw/
```

プロダクト化する段階で、draft/job/run metadataだけDBへ移す。
rowデータとraw responseはファイルまたはオブジェクトストレージに残す。

## Run Request

APIからrunnerへ渡す正規化済み入力は `run_request.json` に保存する。

```json
{
  "schema_version": "simulation_run_request_v1",
  "run_id": "custom_hope_family_20260505_001",
  "domain_pack_id": "agi_youth_japan",
  "domain_pack_dir": "domain_packs/agi_youth_japan",
  "draft_id": "draft_20260505_001",
  "scenario_file": "outputs/api_drafts/draft_20260505_001/scenario.yaml",
  "events_override_tsv": "outputs/api_drafts/draft_20260505_001/events_override.tsv",
  "steps": 12,
  "model": {
    "backend": "openai_api",
    "name": "gpt-5.2"
  },
  "output_dir": "outputs/runs/custom_hope_family_20260505_001"
}
```

これを置くことで、API、CLI、手動実行の境界が揃う。

## 既存コードへの最小変更点

### Runner

現在の `scripts/run_closed_loop_llm_demo.py` は `--scenario-mode` が固定選択式。
UI生成シナリオを扱うには、次のどちらかを追加する。

推奨:

```bash
python3 scripts/run_closed_loop_llm_demo.py \
  --run-request outputs/runs/custom_hope_family_20260505_001/run_request.json
```

暫定:

```bash
python3 scripts/run_closed_loop_llm_demo.py \
  --scenario-file outputs/api_drafts/draft_20260505_001/scenario.yaml \
  --events-override-tsv outputs/api_drafts/draft_20260505_001/events_override.tsv
```

### Viewer

現在の `visualization/future_emotion_map.html` は `runConfigs` に固定runを書いている。
API連携時は次へ置き換える。

```text
GET /api/simulation-runs
  -> run一覧

GET /api/simulation-runs/{run_id}/viewer-manifest
  -> TSVパス
```

静的公開では `public/data/run_index.json` を生成すれば同じUIで読める。

### Domain Pack

既存の `sim_core/domain_pack.py` は、`domain.yaml + scenario.yaml + CLI overrides` を解決できる。
UI生成draftも最終的にはscenario相当へ変換し、この解決順序に乗せる。

```text
default_v1.yaml
  + domain.yaml
  + generated scenario.yaml
  + run_request overrides
  = resolved_config.json
```

## Model API方針

ブラウザからOpenAI/Anthropic/Gemini等のAPIを直接呼ばない。

理由:

- APIキーをブラウザに置けない
- raw responseや監査ログを保存できない
- 再実行条件を固定しにくい
- 長時間ジョブをブラウザ接続に依存させると不安定

モデル呼び出しは必ずバックエンドの `Model Adapter` 経由にする。

```text
Product API
  -> Model Adapter
      -> openai_api
      -> anthropic_api
      -> gemini_api
      -> claude_cli
      -> rule_based
```

ハッカソン/ローカルでは `claude_cli` や `rule_based`。
本番では `openai_api` などに差し替える。

## ジョブ実行

最小構成では、APIサーバーがsubprocessでrunnerを起動する。

```text
POST /api/simulation-runs
  -> job.json作成
  -> status.json = queued
  -> subprocess起動
  -> status.jsonを更新
  -> outputs/runs/{run_id}へ保存
```

プロダクト化したら、キューへ分離する。

| 段階 | 実装 |
|---|---|
| Local MVP | FastAPI + subprocess + file status |
| Prototype | FastAPI + SQLite + background task |
| Product | API + worker + Redis/SQS/PubSub + object storage |

## UIフロー

```text
1. ユーザーが「試したい施策」を入力
2. UIがDraft作成APIを呼ぶ
3. 設計補助LLMが施策・対象・副作用・仮定を構造化
4. UIでユーザーが確認・編集
5. Draft検証APIを呼ぶ
6. 問題なければRun作成APIを呼ぶ
7. UIがRun状態をpolling
8. 完了したらViewer Manifestを読み込む
9. 既存runと比較再生する
```

## 失敗時の扱い

| 失敗 | UI表示 | 保存 |
|---|---|---|
| Draft変換失敗 | 入力不足や矛盾をフォームで表示 | `draft_error.json` |
| Validation error | 必須項目、範囲外、ID不一致を表示 | `validation_report.json` |
| LLM timeout | 該当step/phaseを表示し再開ボタンを出す | `run_log.tsv` |
| row parse error | raw responseを保持し修復候補を出す | `raw/`, `audit_report.md` |
| Viewer file missing | run未完了として表示 | `manifest.json` |

途中再開は既存runnerの「完了済みstepはスキップ」の性質を使う。

## セキュリティ/運用

ローカルMVPでは認証なしでもよい。
クラウド公開時は必須。

最低限必要な制約:

- APIキーはサーバー環境変数に置く
- ユーザー入力から任意コマンドを組み立てない
- `run_id` と `draft_id` は安全な文字種へ正規化する
- 保存先は `outputs/` 配下に制限する
- TSV/JSON/YAMLのサイズ上限を設ける
- raw responseを公開ビューアへそのまま出さない
- 本番ではユーザー/組織ごとにrun閲覧権限を分ける

## 実装順序

1. この設計を正本にする
2. `run_request.json` のスキーマを決める
3. `outputs/api_drafts/` のdraft保存を作る
4. Draft検証APIだけ作る
5. `--run-request` をrunnerに追加する
6. Local FastAPIでrunジョブ起動を作る
7. `GET /api/simulation-runs` とviewer manifestを作る
8. ビューアの固定 `runConfigs` をrun一覧読み込みへ置き換える
9. UIに施策作成フォームを追加する
10. 必要になったらDB/キュー/認証を入れる

## 判断

この設計なら、今のコード資産を壊さずに進められる。

最初の焦点は「ユーザーがUIから新しい施策比較runを追加する」こと。
ドメインパック自体の完全自動作成は、その後でよい。
