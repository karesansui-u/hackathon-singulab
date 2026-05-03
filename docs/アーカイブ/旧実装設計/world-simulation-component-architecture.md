# World Simulation Component Architecture

## Goal

`world_demo` はすでに動いているが、現在は以下の問題を抱えている。

- viewer の状態管理、データ読込、地図描画、右カラム描画、インタラクションが 1 ファイルに集中している
- simulation の選定、状態更新、戦争、国内不安定化、集計、出力生成が 1 スクリプトに集中している
- モデルの意味づけと viewer 上の見せ方が密結合している

この文書の目的は、今後の改修で壊れにくく、役割が見通しやすい構成を定義すること。

## Design Principles

1. `observed baseline` と `scenario overlay` を分ける
2. `simulation engine` と `reporting / export` を分ける
3. `viewer state` と `rendering` と `interaction` を分ける
4. 表示用の narrative はなるべく pure function に寄せる
5. 既存出力フォーマット `turns.csv / aggregate.csv / events.jsonl / manifest.json` は当面維持する

## Target Structure

### Viewer

```text
visualization/
  world_demo_viewer.html
  world_demo/
    app.js
    state.js
    constants.js
    data-loader.js
    selectors.js
    render/
      header.js
      map.js
      sidebar.js
      filters.js
    interactions/
      playback.js
      map.js
      filters.js
```

#### Responsibility Split

- `constants.js`
  - ラベル辞書
  - 色定義
  - 既定 root
- `state.js`
  - 共有 state
  - state mutation helper
- `data-loader.js`
  - manifest / csv / jsonl 読込
  - file system access と bundled URL access
- `selectors.js`
  - `visibleRowsForTurn`
  - `ensureSelectedCountryVisible`
  - `buildTurnActiveCountryKinds`
  - 表示用に必要な derived data
- `render/header.js`
  - ヘッダー、メトリクスチップ
- `render/map.js`
  - ノード、地図下部イベント帯、地図詳細カード
- `render/sidebar.js`
  - 選択国、チャット、ランキング、推論
- `render/filters.js`
  - 表示フィルタパネル
- `interactions/playback.js`
  - 再生、ターン移動、キーボード
- `interactions/map.js`
  - クリック、ズーム、パン、地図詳細カードドラッグ
- `interactions/filters.js`
  - 地域・国フィルタのイベントハンドラ
- `app.js`
  - 初期化
  - render orchestration
  - root connect 流れ

### Simulation

```text
world_demo_sim/
  __init__.py
  types.py
  selection.py
  engine.py
  domestic.py
  conflict.py
  reporting.py
  io_helpers.py
```

#### Responsibility Split

- `types.py`
  - `CountryState`
  - `TurnMetrics`
  - `ConflictEvent`
  - `DomesticEvent`
  - `ScenarioResult`
- `selection.py`
  - `resolve_country_selection`
  - country library 読込
  - preset 展開
- `engine.py`
  - `build_initial_states`
  - `metric_snapshot`
  - `self_update`
  - `apply_cooperation`
  - `run_scenario`
- `domestic.py`
  - `compute_domestic_signals`
  - `apply_domestic_instability`
- `conflict.py`
  - `compute_survival_pressure`
  - `conflict_probabilities`
  - `compute_conflict_candidate`
  - `apply_conflict_event`
  - `apply_conflict_escalation`
- `reporting.py`
  - aggregate row 作成
  - summary row 作成
  - markdown summary
  - comparison report
  - plot helpers
- `io_helpers.py`
  - yaml 読込
  - csv/json/jsonl 書込
  - merge helper

## Data Contract

当面の viewer 入力は次を維持する。

- `manifest.json`
- `turns.csv`
- `aggregate.csv`
- `events.jsonl`

ただし内部的には、`reporting.py` 側で次の 2 層へ整理する。

1. `simulation state rows`
2. `viewer-facing derived rows`

将来的には narrative を `events.jsonl` に直接含める余地を残す。

## Immediate Refactor Scope

今回は次だけを行う。

1. viewer JS を外部ファイルへ分割する
2. simulation script の pure logic を `world_demo_sim` package に移す受け皿を作る
3. `scripts/run_world_demo.py` は薄い entrypoint へ寄せる

今回は次はやらない。

- 出力スキーマの大幅変更
- baseline 較正ロジックの実装
- UI の全面 redesign

## Migration Rule

分割時は「挙動を変えない」を優先する。

- まずコードを移す
- 次に import / wiring を入れる
- 最後に dead code を落とす

## Follow-up

この分割後にやると効果が高いもの。

1. `observed baseline` の実データ較正
2. viewer narrative の backend 側生成
3. tests for `domestic` / `conflict` thresholds
4. alternate views
   - region summary
   - bloc summary
   - timeline compare
