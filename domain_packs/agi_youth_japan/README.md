# AGI時代の日本の若者・現役世代

このドメインパックは、AGI/シンギュラリティ時代に、日本の若者・現役世代がどのように未来を知覚し、感情と行動を変化させるかを観測するための最初のパック。

基本構造:

- 共通辞書・標準row仕様は `sim_core/defaults/default_v1.yaml` から継承する
- AGI若者固有の若者30体・現役30体・国家30体・組織15体、イベント、認知層、国家イベントをこのパックで上書きする
- 本番デモは `data/demo_panel_48.tsv` で国家12体・0-14歳コホート8枠・15-22歳12体・23-40歳8体・組織8体へ絞り、代表重みを再配分する
- シナリオごとの強度や差し替えは `scenarios/*.yaml` に置く
- UI設定は `viewer/viewer_config.yaml` で上書きできる
- 拡張処理は `hooks` で宣言する

主要データ:

- `data/youth_agents.tsv`: 日本の若者30エージェント
- `data/working_agents.tsv`: 日本の現役世代30エージェント
- `data/country_agents.tsv`: 世界国家30エージェント
- `data/organization_agents.tsv`: 企業・自治体・教育機関などの組織15エージェント
- `data/demo_panel_48.tsv`: 本番デモ用48枠パネルと層内代表重み
- `data/time_schedule.tsv`: 本番デモ用71ステップの時間設計
- `data/age_observation_policy.tsv`: 年齢帯ごとの個人LLM/コホート観測/非表示の運用方針
- `data/child_cohorts.tsv`: 0-14歳を名前付き個人ではなく次世代コホートとして扱う定義
- `data/family_formation_cohort_definitions.tsv`: 今の家族形成世代、今の若者、今の子どもを10年/20年単位で見るためのコホート定義
- `data/family_formation_states.tsv`: 現在の現役世代W01-W30の結婚・出産状態と年次遷移確率
- `data/lifecycle_transition_rules.tsv`: 年齢帯ごとの若者/家族形成/子育て後半/現役外への遷移ルール
- `data/family_formation_metrics.tsv`: 結婚意向、子ども意向、子育て実行可能性、次世代信頼などの観測指標
- `data/generation_flow_rules.tsv`: 新世代流入、代表重み更新、前世代記憶継承のルール
- `data/generation_inflow_templates.tsv`: 今の子ども世代を15歳到達タイミングで若者/家族形成層へ流入させるテンプレート
- `data/country_objective_weights.tsv`: 国家ごとの目的関数重み
- `data/country_to_japan_channels.tsv`: 国家出力から日本社会状態への波及チャンネル
- `data/world_events.tsv`: 71ステップ分の世界イベント入力

年齢・世代の扱い:

- 0-14歳: 名前付き個人LLMではなく、`child_cohorts.tsv` の8次世代コホートとして扱う
- 15-22歳: 若者の進路・初職・未来経路を12体の個人/代表エージェントで厚く見る
- 23-40歳: 家族形成・子育ての中心観測層を8体で見る
- 41-64歳: 子育て後半・介護・次世代支援の補助観測に回す
- 65歳以上: 死亡ではなく、現役/家族形成マップの直接観測対象外にする

本番デモの時間軸:

- ステップ1-60: 直近5年を月次で観測
- ステップ61-65: 次の5年を年次で観測
- ステップ66-71: 15年目から40年目までを5年単位で観測

比較run:

- `--scenario-mode no_intervention`: `events.tsv` の政策イベント(P系)を除外し、ショックと世界圧力だけを見る
- `--scenario-mode structure_intervention`: 政策イベント(P系)も含め、構造持続論ベースの介入ありとして見る

自動化イベントは分離している:

- `E01`: 生成AI・認知労働自動化急加速
- `E09`: 汎用ロボティクス普及による身体労働再編
- `P11`: 介護ロボット・在宅支援普及
