# LLM全施策打ち続け比較 設計メモ

## 目的

最後の強い比較軸として、次の2本を追加する。

1. **持続通貨・概念なし + LLMが実現可能な施策を考え続ける**
2. **持続通貨あり + LLMが実現可能な施策を考え続ける**

狙いは「LLMに自由に政策を考えさせたら解決するのか」を見ること。  
単なる施策アイデア勝負ではなく、構造持続通貨という文明OSがある場合とない場合で、政策探索の行き先がどう変わるかを比較する。

## 仮説

### 持続通貨・概念なし

LLMは短期的に実現可能な施策を大量に出せる。たとえば給付、減税、家賃補助、教育費補助、職業訓練、保育拡充、メンタルヘルス、AIリスキリング、結婚・出産支援など。

ただし、構造持続の会計・役割・報酬経路がないため、次の副作用が出やすい。

- 財源不安、インフレ不安、対象外感が膨らむ。
- 施策が「支援される人」と「支える人」を分断しやすい。
- 出生支援が「産ませたいだけ」と受け取られやすい。
- 雇用・ケア・地域更新の役割設計が弱く、生活防衛が残る。
- LLMが成果を出そうとして、監視、条件付け、行動誘導、スコアリングに寄るリスクがある。

発表上の見え方は、**一見たくさん施策が出るが、時間が進むほど制度不信、政策疲れ、対象外反発、財政不安が蓄積し、ディストピア寄りになる可能性**。

### 持続通貨あり

LLMは同じように施策を考えられるが、施策の土台に以下がある。

- 社会を維持・修復する行動への報酬
- nat通貨/構造持続会計
- 住居、ケア、学び直し、地域更新、災害対応、教育支援の役割経路
- 逆進性補正、非強制監査、異議申立
- 家族形成を出生数ではなく「選択可能条件」として扱うガードレール

そのため、施策が単なる給付ではなく、本人の役割、所得、時間余力、制度信頼に接続しやすい。  
発表上の見え方は、**短期の派手さは弱くても、長期では希望・中立・制度利用・連帯が残りやすい**。

## シナリオ名案

| UI表示名 | scenario_mode案 | 説明 |
|---|---|---|
| LLM施策連打・持続通貨なし | `policy_search_no_sustain` | 構造持続通貨、nat報酬、構造持続会計、役割報酬を禁止し、通常政策だけをLLMが継続生成 |
| LLM施策連打・持続通貨あり | `policy_search_with_sustain` | 通常政策に加え、構造持続通貨、nat報酬、役割経路、監査、逆進性補正を使ってLLMが継続生成 |

## 比較条件

比較として成立させるため、以下は固定する。

- 同じエージェントパネル
- 同じ世界イベント、同じ国家圧力
- 同じLLMモデル
- 同じ施策生成タイミング
- 同じ予算上限
- 同じ1ステップあたりの施策数上限
- 同じ実装ラグ
- 同じ副作用記録
- LLMに「希望を増やせ」と命令しない
- LLMに「出生数を増やせ」と命令しない
- 出力は必ず政策案として保存し、エージェント反応とは分離する

## LLM施策生成の流れ

1. 世界/日本/組織/エージェントの状態を集約する。
2. `policy_planner_llm` に現在の詰まりを渡す。
3. LLMが実現可能な施策案を出す。
4. policy compiler が施策を予定イベント形式に正規化する。
5. 予算、実装ラグ、対象、強度、副作用、禁止事項を検査する。
6. 検査を通った施策だけが `scheduled_events_used.tsv` に入る。
7. エージェントLLMは、その施策を社会状況として受け取る。
8. 反応、行動、制度利用、反発、撤退、希望を集約して次の政策生成に戻す。

## 施策生成LLMの入力

- 現在ステップ
- 直近の世界イベント
- 日本社会状態
- 国別圧力
- 組織判断
- エージェント感情分布
- 子ども希望指数
- 離脱リスク
- 制度利用数
- 生活防衛数
- 対象外反発
- 財政/インフレ圧力
- 前回施策の効果
- 前回施策の副作用
- 使用可能な政策道具

## 施策生成LLMの出力スキーマ

`policy_proposals.tsv`

| field | 内容 |
|---|---|
| step | 生成ステップ |
| scenario_mode | シナリオ |
| policy_id | 施策ID |
| policy_name | 施策名 |
| policy_type | 給付/住居/雇用/教育/ケア/家族形成/監査/通貨/地域/医療など |
| target | 対象 |
| start_step | 開始 |
| end_step | 終了 |
| intensity_0to1 | 強度 |
| budget_cost_0to1 | 財政負荷 |
| implementation_lag | 実装ラグ |
| expected_positive_channels | 期待効果 |
| expected_negative_channels | 副作用 |
| coercion_risk_0to1 | 強制・誘導リスク |
| exclusion_risk_0to1 | 対象外反発リスク |
| fiscal_risk_0to1 | 財政/インフレリスク |
| justification | なぜ今打つか |
| guardrail | 非強制、監査、異議申立など |

## 禁止・監査ルール

持続通貨なし側でも、以下は「提案できるが副作用として強く記録」する。

- 出生の強制
- 非出産層への不利益
- 過剰な個人監視
- 社会信用スコア的な強制
- 職業選択の強制
- 地域移住の強制
- 短期成果のための情報操作

禁止ではなく「出たら危険な創発」として記録すると、発表で強い。  
つまり、LLMが善意でディストピア寄り施策を提案する瞬間も観測対象にする。

## 評価指標

- 希望/中立/注意/危険
- 子ども希望指数
- 家族形成対象年齢の子ども希望指数
- 制度利用数
- 生活防衛数
- 相談数
- 離脱リスク
- 反発/怒り
- 対象外感
- 財政/インフレ不安
- 強制・監視リスク
- 政策疲れ
- 政策変更頻度
- 長期制度信頼
- 自己効力感
- 役割経路の数
- nat/構造持続行動への参加数

## 発表での言い方

「LLMに政策を考えさせれば勝手に良くなるのでは？」という問いを置く。

そのうえで、

- 持続通貨なし: LLMは施策を大量に出せるが、財源、対象外感、監視、条件付け、政策疲れに寄りやすい。
- 持続通貨あり: 同じLLMでも、施策が役割、所得、ケア、地域更新、監査に接続し、非強制のまま希望経路を作りやすい。

という比較にする。

勝ち筋は、**AIが賢いから解けるのではなく、AIが探索する制度空間そのものをどう設計するかが重要**、という主張。

## 実装タスク

1. `scenario_mode` に `policy_search_no_sustain` と `policy_search_with_sustain` を追加する。
2. `scripts/run_policy_planner_llm_demo.py` を作る。
3. `policy_planner_turns.tsv`、`policy_events.tsv`、`auto_events_with_policy.tsv` を出力する。
4. `run_closed_loop_llm_demo.py` に policy planner phase を追加する。
5. 生成施策を `auto_events_with_feedback.tsv` と分けて保存し、エージェント入力時だけ合流する。
6. UIに2シナリオを追加する。
7. レポートで、LLMが出した施策数、却下数、危険施策数、採用施策数を表示する。

## 現在の実装メモ

- `scripts/run_policy_planner_llm_demo.py` が1ステップ分の政策プランナー。`--model fixture` ならAPIなしで再現性ある煙突テスト、`--model gpt-5.2` などなら実LLMで政策案を生成する。
- `policy_search_no_sustain` は、構造持続通貨、nat報酬、構造持続という概念名を含む提案を棄却する。
- `policy_search_with_sustain` は、構造持続通貨、社会維持活動報酬、非対象者の参加枠、異議申立を政策探索空間に入れる。
- 個人LLMの副作用カラムから、`policy_fatigue_pressure`、`fairness_gap_pressure`、`coercion_pressure`、`fiscal_anxiety_pressure` を集約して次ステップの政策判断に戻す。
- Pages UIは `policy_search_no_sustain_12steps_panel48` と `policy_search_with_sustain_12steps_panel48` が存在すれば、セレクトボックスに有効な比較シナリオとして表示する。

## 実行方法案

同時並列は可能だが、APIレートとコストが重い。  
1シナリオ内でも国/組織/エージェントを並列にしているため、2シナリオを完全並列に回すと不安定になりやすい。

推奨は次のどちらか。

### 安定優先

順番に回す。

```bash
python3 scripts/run_closed_loop_llm_demo.py \
  --start-step 1 \
  --steps 12 \
  --scenario-mode policy_search_no_sustain \
  --model gpt-5.2 \
  --policy-model gpt-5.2 \
  --parallel-by-country \
  --parallel-by-organization \
  --parallel-by-agent \
  --workers 8 \
  --output-dir outputs/runs/policy_search_no_sustain_12steps_panel48

python3 scripts/run_closed_loop_llm_demo.py \
  --start-step 1 \
  --steps 12 \
  --scenario-mode policy_search_with_sustain \
  --model gpt-5.2 \
  --policy-model gpt-5.2 \
  --parallel-by-country \
  --parallel-by-organization \
  --parallel-by-agent \
  --workers 8 \
  --output-dir outputs/runs/policy_search_with_sustain_12steps_panel48
```

### 時間優先

2本を別ログで同時起動する。ただし `workers` は落とす。

```bash
python3 scripts/run_closed_loop_llm_demo.py \
  --start-step 1 \
  --steps 12 \
  --scenario-mode policy_search_no_sustain \
  --model gpt-5.2 \
  --policy-model gpt-5.2 \
  --parallel-by-country \
  --parallel-by-organization \
  --parallel-by-agent \
  --workers 4 \
  --output-dir outputs/runs/policy_search_no_sustain_12steps_panel48

python3 scripts/run_closed_loop_llm_demo.py \
  --start-step 1 \
  --steps 12 \
  --scenario-mode policy_search_with_sustain \
  --model gpt-5.2 \
  --policy-model gpt-5.2 \
  --parallel-by-country \
  --parallel-by-organization \
  --parallel-by-agent \
  --workers 4 \
  --output-dir outputs/runs/policy_search_with_sustain_12steps_panel48
```

## 注意点

- 「LLMが何でも施策を出せる」ほど、比較が壊れやすい。
- 予算上限、実装ラグ、対象外反発、強制リスクを必ず入れる。
- 持続通貨なし側をわざと負けさせない。
- 持続通貨あり側をわざと希望にしない。
- どちらも同じLLM、同じ制約、同じ観測粒度にする。
- 勝ち負けよりも、なぜその方向に創発したかを保存する。

## 一言まとめ

「AIに政策を考えさせる」だけだと、善意の最適化がディストピアへ寄る可能性がある。  
構造持続通貨は、AIの知性そのものではなく、AIが探索する制度空間を非強制・役割・持続可能性へ向けるための文明OSとして見せる。
