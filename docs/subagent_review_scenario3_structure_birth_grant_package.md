# 第3シナリオ（構造持続介入 + 出産一時金/家族形成パッケージ）追加レビュー（サブエージェント）

対象レポ: `/Users/sunagawa/Project/hackathon-singulab`

このメモは「第3シナリオ」を **実装・実行・UI反映** する際に親エージェントが踏みやすい地雷と、変更が必要な箇所を短時間で把握するためのチェックリストです。

## 1) 第3シナリオ追加に必要なファイル/設定/スクリプト

### 既に入っているもの（確認済み）

1. `domain_packs/agi_youth_japan/data/events.tsv`
  - `BP01`〜`BP07` の政策イベントが定義済み（「構造持続型出産一時金の上乗せ」「産後休息・代替ケア保障」「希望経路の可視化と達成共有」等）。
  - 追加の勝ち筋として `HP01`〜`HP07` も定義済み（若者希望経路、初職リカバリー、地域持分、子育て共同体、異議申立、希望3体以上観測ゲート）。
2. `scripts/run_civilization_os_llm_demo.py`
   - `scenario_mode` に `structure_birth_grant_package` が存在。
   - イベントフィルタ仕様:
     - `no_intervention`: `区分=政策` と `イベントID` が `P*` と `BP*` を除外
     - `structure_intervention`: `BP*` のみ除外（`P*` は含める）
     - `structure_birth_grant_package`: 全イベント（`P*` + `BP*`）を含める
3. `scripts/run_closed_loop_llm_demo.py`
   - `--scenario-mode` の choices に `structure_birth_grant_package` が入っている。

### 追加が必要になりがちなもの（未反映の可能性が高い）

1. ビューア（ローカル）: `visualization/future_emotion_map.html`
   - `runConfigs` に第3シナリオの run_id と各 TSV パスを追加
   - `#scenarioTabs` のボタン（2つ固定）を 3つ目に増やす
2. GitHub Pages 用 public 生成: `scripts/build_pages_site.py`
   - `RUN_IDS` に第3シナリオ run_id を追加（`public/data/runs/{run_id}` にコピーされるため）
3. public 側ビューア: `public/visualization/future_emotion_map.html`
   - `scripts/build_pages_site.py` は `visualization/future_emotion_map.html` をコピーしてパス書換するだけなので、
     基本は source 側（`visualization/...`）を直すのが筋。

## 2) 推論を途中再開できるか / run_id の切り方

### 再開可否

`scripts/run_closed_loop_llm_demo.py` は **途中再開可能**。

- `outputs/runs/{run_id}/country_turns.tsv` 等の既存 TSV を見て `step_complete()` で完了ステップを判定し、既に完了しているステップは skip する。
- 再開する場合は **同じ `--output-dir`（= run_id フォルダ）** を指定して `--start-step` を進めて実行する。

### run_id の切り方（重要）

`scenario_mode` を変えるなら **必ず run_id（出力ディレクトリ）を分ける**。

理由:
- 同じ run_id に `structure_intervention` の途中結果があり、後から `structure_birth_grant_package` を混ぜると、
  `agent_turns.tsv` / `scheduled_events_used.tsv` が「途中から別フィルタ」に変わり、比較不能になる。

おすすめ命名例:
- `structure_birth_grant_package_100years_panel48_midprompt` のように、
  `scenario_mode` + `年数/steps` + `panel` + `prompt差分` を含める。

注意（現状仕様）:
- `manifest.json` は **実行のたびに上書き**され、`start_step/steps` は「最後に実行した分」になる。
  - 例: `outputs/runs/no_intervention_71steps_panel48/manifest.json` は `start_step=67, steps=5` だが、
    `agent_turns.tsv` 自体は `step=1..71` を含む。
  - 追跡は `run_log.tsv` と TSV の実データ側で見る前提が安全。

## 3) 既存 UI に第3シナリオタブを増やす際の注意点

`visualization/future_emotion_map.html` は **2シナリオ前提の分岐が複数箇所**ある。
単純に `runConfigs` とボタンを増やすだけだと、表示が壊れる/意図と違う可能性が高い。

要注意箇所（代表例）:
- 「政策イベントの表示/非表示」が `state.scenario === "sustain"` で固定判定
  - 第3シナリオでも政策イベントを見せたいなら、
    `sustain` と同様に扱う条件へ拡張が必要。
- アクションラベルや補正ロジックが `scenario === "sustain"` 前提で分岐
  - 第3シナリオを `sustain` 系として扱うなら、`scenario` が `sustain` または `birth` のような判定にするか、
    `isInterventionScenario(scenario)` 的に整理する必要がある。

実装の作法（衝突回避）:
- ハードコード分岐が多いので、親が編集するときは「第3キー追加」だけでなく
  `baseline/sustain` の二択をやめる箇所が残っていないか `rg '\"sustain\"' visualization/future_emotion_map.html` で点検するのが早い。

## 4) 「出産一時金」単体でなく「構造持続介入 + 一時金パッケージ」に見せるイベント設計の妥当性

現状のイベント設計は「パッケージ」として概ね筋が良い（実装もそれに沿っている）。

- `P*` が構造持続介入のベース（住居、学び直し、ケア、nat報酬など）
- `BP*` が家族形成パッケージの追加要素（出産一時金上乗せ、産後ケア、企業負担補正、住居・教育費緩衝、非強制ガードレール、財政監査、希望経路可視化）
- `structure_intervention` は `BP*` を除外して「構造持続のみ」を表現
- `structure_birth_grant_package` は `P* + BP*` で「構造持続 + 家族形成パッケージ」を表現
- `structure_hope_family_package` は `P* + BP* + HP*` で「希望を持つ若者と子どもを迎えられる人を増やす追加設計」を表現

確認観点:
- `BP05`（非強制・監査ガードレール）と `BP06`（財政・インフレ持続性監査）が入っているため、
  「産ませたいだけ」反発や持続性懸念に対してイベント設計で先回りできている。

## 5) 親が見落としそうなバグ/整合性リスク

1. ビューアが2シナリオ前提
   - `state.scenario === "sustain"` 前提の表示/ロジックが残ると、第3シナリオで政策イベントが隠れる等の誤表示が出る。
2. `manifest.json` の上書き
   - 途中再開や追実行で、manifest が「最後の実行条件」になってしまう（履歴としては不正確）。
3. `build_pages_site.py` の `RUN_IDS` ハードコード
   - 第3 run_id を追加し忘れると、GitHub Pages 側にはデータが出ず UI がロードできない。
4. run_id と実データの steps がズレる
   - フォルダ名が `71steps` でも、実際に揃っているかは TSV を見ないと分からない（UI は maxStep を TSV から計算）。
