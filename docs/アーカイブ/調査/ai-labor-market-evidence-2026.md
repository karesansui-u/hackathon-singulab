# AI雇用影響の最新研究メモ 2026

## 目的

このメモは、`world demo` と今後の世界シミュレーションにおいて、

- AI による雇用代替
- AI による補完・生産性上昇
- 国・所得階層ごとの普及差
- 国内不安定化と再分配需要

を、できるだけ最新の一次ソースに基づいてパラメータ化するための基礎資料である。

ここで重視するのは「AI が仕事をなくすかどうか」という二択ではなく、

- `どの仕事がどの程度 exposed か`
- `実際にどの程度 adoption が進んでいるか`
- `置換より augmentation が多いのか`
- `国ごとに何が bottleneck になるか`
- `どの程度の政策反応が必要か`

を切り分けて、シミュレーションの各変数に落とすことである。

## 先に結論

2026年4月時点で、一次ソースを横断して見ると、次の絵がかなり一貫している。

1. `仕事の消滅リスク` はゼロではないが、現時点の実証では「即時の大規模雇用崩壊」が確定したとは言えない。
2. ただし `認知労働の高露出職` はかなり明確で、特に clerical、digitized professional、software/analysis 系が強く影響を受ける。
3. 影響は `世界一様` ではなく、高所得国ほど exposure は高い。一方で低所得国は AI の便益も disruption も、インフラ不足で抑えられる。
4. 短期の実データでは adoption はまだ限定的だが、利用は急速に伸びている。
5. 企業・研究の実証では、現段階の GenAI は `augmentation` が `automation` よりやや優勢。
6. ただし medium-skill の再配分圧力、初期キャリア層の不利、地域間・所得階層間格差の拡大は十分あり得る。
7. 日本は labor shortage が深刻だが、AI だけで穴埋めできるわけではなく、労働移動と制度対応が重要。

## 一次ソースから拾うべき事実

### 1. ILO 2025: グローバルな occupational exposure

ILO の 2025 年更新では、

- `世界の労働者の4人に1人` が何らかの GenAI exposure のある職にいる
- `世界雇用の3.3%` が highest exposure category
- 高所得国では highest exposure category がより大きく、`高所得国全体では 34% が何らかの exposure`
- 低所得国では `11%`
- 最高露出カテゴリでは女性の比率が高く、`HIC では女性 9.6%、男性 3.5%`

という差が出ている。

また、2025 update では、

- clerical occupations が依然として最も高露出
- 一方で 2023 年より professional / technical 側の露出も上がっている

という方向が示されている。

シミュレーションへの含意:

- `automation_exposure` は国一律ではなく、職種構成の white-collar 比率で変える
- `gendered exposure` を入れるなら clerical / administrative / digitized service を厚く見る
- `low-income countries are safer` ではなく、`exposure も便益も低い` とみなす

### 2. IMF 2024-2026: 世界全体の job exposure と新スキル需要

IMF は 2024 年以降、かなり一貫して

- `世界全体で約40%の jobs が AI の影響を受ける`
- `advanced economies では約60%`
- `emerging markets では約40%`
- `low-income countries では約26%`

と整理している。

2026年1月時点の IMF blog では、オンライン求人データから

- `advanced economies では 10件に1件`
- `emerging markets では 20件に1件`

の求人が、すでに `少なくとも1つの新しい skill` を要求しているとしている。

シミュレーションへの含意:

- `AI exposure` と `skill churn` は別変数にする
- `automation_velocity` が同じでも、`reskilling pressure` は advanced / emerging で分ける
- 中期シナリオでは `jobs disappear` だけでなく `required skill set changes` を強く入れる

### 3. World Bank 2025: 低・中所得国では exposure より infra が効く

World Bank の 2025 working paper では、

- worker-level の AI exposure は `high income 62`, `upper-middle 49`, `lower-middle 44`, `low income 37`
- 低所得国では電力・インターネット不足が AI exposure の実効化をさらに制約
- `low-income countries の約42%の occupations` は、露出があっても電力アクセスがない
- `low-income rural` では、露出があっても `51%` が電力アクセスなし

としている。

シミュレーションへの含意:

- `compute_access` だけでは足りず、`electricity reliability` を別に持つべき
- `AI が遅れる国` は disruption も productivity uplift も遅れる
- 低所得国の delayed exposure は、単なる安全ではなく `後追いショック` の可能性でもある

### 4. Anthropic Economic Index 2025: 実際の use は augmentation 優位

Anthropic の 2025 年の初回 Economic Index は、

- Claude の匿名化利用データ約100万会話を O*NET task に対応
- `36%` の occupations で、関連 task の少なくとも `25%` に AI use
- ただし `75%` 以上の tasks で使われている occupations は `約4%`
- overall では `augmentation 57%`, `automation 43%`

としている。

また use は、

- software development
- technical writing
- arts / media / editing
- office / administrative

に濃く、physical labor 系はかなり薄い。

シミュレーションへの含意:

- 2026 時点の baseline は `full replacement` ではなく `task-level partial adoption`
- `automation_exposure` と `actual substitution` の間にギャップを置く
- `physical_automation_velocity` は `cognitive automation_velocity` よりかなり遅く置くのが自然

### 5. U.S. Census BTOS 2023-2025: firm-level adoption はまだ低いが伸びは速い

U.S. Census の BTOS 系列では、

- 2023年10-11月時点で `3.9%` の businesses が AI を goods/services production に使用
- 2024年2月には `5.4%`
- 2025年5月には `約10%`

まで上昇している。

これは「AI がすでに全産業で常態化している」というより、

- `adoption is still early`
- ただし `diffusion is fast`

という読みが自然である。

シミュレーションへの含意:

- `adoption curve` は logistic っぽく置く
- 2026 時点の初期値は `高露出でも利用率はまだ限定的`
- ただし `後半5年で急伸` するシナリオは十分あり得る

### 6. WEF 2025: 雇用は純減ではなく、大規模な入替として出る

WEF の `Future of Jobs Report 2025` は、雇用への影響をかなり大きく見積もっているが、
その絵は `一方向の消滅` ではなく `大規模 churn` である。

2030年までに、

- `170 million` jobs created
- `92 million` jobs displaced
- net `+78 million`
- ただし total disruption は `22% of today’s formal jobs`

としている。

また、

- `86%` の employers が AI / information processing technologies が business を変えると回答
- `39%` の core skills が 2030 までに変化

とされる。

シミュレーションへの含意:

- `employment destruction` と `job creation` を別に持つ
- `skill churn` をかなり強く置く
- disruption は net employment だけでは読めず、`transition pain` を別に持つ必要がある

### 7. NBER 実証・理論: 短期は productivity/augmentation、長期は unemployment risk の分岐

重要なのは、NBER 系の結果が一方向ではないこと。

#### Brynjolfsson, Li, Raymond

`Generative AI at Work` では customer support agents に対して

- average productivity `+14%`
- novice / low-skill workers は `+34%`
- retention や learning も改善

が出ている。

これは `augmentation` 側の強い実証。

#### Baslandze et al. 2026

2026年3月の NBER working paper では、

- nearly 750 executives の調査で `more than half` がすでに AI 投資
- near-term aggregate employment declines の evidence は小さい
- ただし larger firms は workforce reduction を見込む傾向

とされる。

#### Wang & Wong 2025

理論モデルでは、ある均衡では

- productivity が大きく上がる一方で
- `long-run employment loss 23%`
- その `half` が最初の `5年間` に起こる

という stress path も示される。

シミュレーションへの含意:

- `base case` と `stress case` を分ける
- baseline は augmentation 優位
- long-run stress では medium-skill erosion と transition unemployment を大きく取る
- `firm size / sector concentration` が高い国ほど severe path を引きやすくする

### 8. Japan-specific: IMF 2025

IMF の 2025 年 Japan paper はかなり重要で、

- 日本の aging は labor shortage を悪化させる
- AI は一部で助けるが、`日本の workers は他の advanced economies より AI exposure が低い`
- そのため `AI だけで labor shortage を埋めるのは難しい`
- displaced occupations から in-demand occupations への `labor mobility` が重要

と整理している。

シミュレーションへの含意:

- 日本は `automation exposure 高め` というより、`高齢化による shortage と limited substitution` の混合ケースとして扱う
- `JPN` の `adaptation` は、単なる AI 導入率ではなく `mobility / retraining / participation` に依存させる

## シミュレーションにどう落とすか

## 1. 変数を3層に分ける

### A. Exposure

AI に理論上どれだけ触れるか。

- `automation_exposure`
- `physical_exposure`
- `clerical_share`
- `digitized_professional_share`
- `manual_share`

### B. Effective adoption

実際に導入・運用できるか。

- `compute_access`
- `electricity_reliability`
- `internet_access`
- `managerial_capability`
- `institutional_capacity`
- `ai_capital_availability`

### C. Buffer / transition

失職圧力を吸収できるか。

- `adaptation_velocity`
- `distribution_capacity`
- `structure_credit_intensity`
- `winner_reinvestment`
- `labor_mobility`
- `reskilling_capacity`

この3層を分けると、

- `exposure は高いが adoption は遅い国`
- `adoption は速いが buffer が弱い国`
- `exposure も adoption も高いが augmentation に振れる国`

を分けられる。

## 2. 現在の主要パラメータへの対応

今の `run_world_demo.py` にそのまま対応させると、概ねこう読むとよい。

- `automation_velocity`
  認知労働の置換スピード。ILO/IMF/Anthropic から見て、まずここが主戦場。

- `physical_automation_velocity`
  物流・倉庫・製造・配送・ケア補助などへの浸透速度。Cognitive より遅く置くのが自然。

- `adaptation_velocity`
  再訓練、職種転換、制度更新、企業内の job redesign がどれくらい間に合うか。

- `structure_credit_intensity`
  市場で過小評価される安定化行動にどれだけ報酬を与えるか。

- `winner_reinvestment`
  資本・高収益企業がどれだけ分配、冗長性、ケア、インフラに利益を戻すか。

- `domestic_trigger_bonus`
  生活費高騰、住宅、債務、失業、政治ショックなどが protest を押し上げる exogenous shock。

## 3. 2026時点のおすすめ初期レンジ

これは `真値` ではなく、最新研究に整合的な simulation prior。

### 認知AI

- conservative: `0.012 - 0.018`
- base: `0.020 - 0.032`
- fast: `0.035 - 0.055`

### フィジカルAI

- conservative: `0.004 - 0.008`
- base: `0.008 - 0.018`
- fast: `0.020 - 0.035`

### 適応速度

- weak: `0.008 - 0.015`
- medium: `0.018 - 0.028`
- strong: `0.030 - 0.050`

### 構造クレジット強度

- weak: `0.005 - 0.012`
- medium: `0.015 - 0.025`
- strong: `0.028 - 0.045`

### 勝者再投資

- extractive: `0.005 - 0.015`
- mixed: `0.015 - 0.030`
- regenerative: `0.030 - 0.060`

## 4. 20年シミュレーションの解釈

20年を回すときは、1本の deterministic future ではなく、少なくとも次の4系統に分けたほうが良い。

### 1. Augmentation-led transition

- 認知AIは速い
- フィジカルAIは中速
- 適応が十分
- 失職より task redesign が多い

### 2. Polarization path

- 認知AIは速い
- medium-skill white-collar が圧迫される
- low/high に分極
- protest は増えるが state collapse までは行かない

### 3. Fragile displacement path

- 導入は速い
- 再分配と labor mobility が遅い
- `cash_stability` と `social_cohesion` が落ちる
- protest -> riot -> insurgency の確率が上がる

### 4. Uneven world path

- advanced economies は高 exposure / 高 adoption
- low-income countries は exposure 低め / infra bottleneck
- ただし資本・エネルギー・食料の価格変動で間接ショックを受ける

### 補足 1. 単発の「シンギュラリティ」より、速度差による長い再編として見る

このテーマを考えるとき、`ある日を境に人間の仕事が一気に消える` という単発イベントを想像しがちである。
ただし、2026年4月時点の一次ソースと実務観測を合わせると、実際に起きやすいのはもっと遅く、 uneven な変化である。

より自然な見方は次。

- `A_cog`: 認知労働の自動化が先に進む
- `A_phy`: 身体労働の自動化は別速度で追いかける
- `G_dist`: 分配・再訓練・制度更新がその間に合うかどうかで社会の壊れ方が変わる

つまり「AI が世界を一気に変える」より、
「認知系から順に sector を縦断し、社会の吸収力との差で崩れ方が決まる」
と見るほうが、今の研究とも実感とも整合的である。

### 補足 2. なぜ 20 年スパンが現実的に見えるのか

短い議論では、

- `AI がすべての仕事を奪う`
- `AI はただの道具にすぎない`

の両極端に振れやすい。

しかし research と経済史の中間にあるのは、
`雇用の大半は20年かけて再編される`
という見方である。

ここで大事なのは、LLM が未来を当てているというより、
LLM が訓練データの中にある労働経済学・技術史・制度変化の平均像をかなり素直に返している、という点である。

したがって、20年という時間感覚は楽観ではなく、

- 技術の能力上昇
- 組織導入の遅さ
- 規制・責任・インフラ制約
- 雇用制度の粘性

を全部入れたときの、かなり現実的なレンジと考えたほうがよい。

### 補足 3. 米国と日本は「どちらがマシか」ではなく、壊れ方が違う

ユーザの観察どおり、米国は解雇がしやすいので、`A_cog` のショックを比較的早く雇用に反映しやすい。
そのため、

- レイオフ
- 採用停止
- no backfill
- 再就職か離脱かの早い選別

が見えやすい。

日本は逆に、

- 終身雇用
- 解雇しにくさ
- 新卒一括採用
- 社内配置転換

がショックを表面上は吸収する。

ただし、これは無傷という意味ではない。
日本ではむしろ、

- 新規雇用の縮小
- 若年層の選択肢の減少
- 非正規化
- 賃金抑制
- 中小企業の静かな疲弊

として出やすい。

構造持続の言葉で言うと、

- 米国は `L` を早く計上して、短期の痛みで再編する型
- 日本は `L` を雇用統計にすぐは出さず、`N` と将来世代の選択肢が静かに縮む型

であり、崩壊の出方が違うだけで、どちらも放置すると `e^{-L}` 側が下がっていく。

### 補足 4. 「人間が鈍感」ではなく、生活が前提のアップデートを縛っている

ここはかなり重要で、人間が鈍いというより、
生活と制度が前提のアップデートを遅らせている、と表現したほうが正確である。

人間は、

- `自分の仕事はまだ残るかもしれない`
- `認知労働の大半は置き換わるかもしれない`

という二つの信念を同時に持っていても、
片方を完全には採用できないことが多い。

理由は単純で、前提のアップデートコストが生活に直結するからである。

- 住宅ローン
- 家族扶養
- 組織評価
- 転職コスト
- 再訓練コスト

があるため、正しいかもしれない新しい見方が、すぐ行動に変わらない。

ここで言うコストは、
`前提のアップデートコスト`
と呼ぶほうが分かりやすい。

この意味で、LLM が鋭く見えるのは、予測能力そのものより、
`生活Sに縛られずに信念空間を動かせる`
からである。

### 補足 5. シミュレーションで本当に比べたいもの

したがって、このプロジェクトが比較したいのは、
単純に `AI が強いか弱いか` ではない。

本質は、

- `A_cog` が先に進む世界で
- `A_phy` があとから追いつくとき
- `G_dist` と `生活Sの切り離し` が間に合うか

である。

より平易に言うと、

- AI が仕事を奪うか

ではなく、

- 社会がその速度に合わせて、生活と前提アップデートの土台を作れるか

を見たい。

この意味で `structure credits` は単なる再分配ではない。
それは、
`市場賃金から切り離された最低限の生活S`
をつくり、人間が現状維持バイアスだけで動かなくて済む外部代謝として読むのが自然である。

## 5. 今の world demo に足したい変数

次の段階では、少なくとも以下を追加すると research にかなり近づく。

- `electricity_reliability`
- `internet_access`
- `labor_mobility`
- `reskilling_capacity`
- `clerical_share`
- `digitized_professional_share`
- `manual_share`
- `firm_concentration`
- `youth_entry_penalty`
- `ai_skill_demand_gap`

特に重要なのは、

- `labor_displacement` だけではなく
- `skill mismatch`
- `mobility failure`
- `delayed adoption because of infra`

を別に持つこと。

## 6. すぐ使える実装方針

### 方針A: 既存モデルを最小拡張

今の `run_world_demo.py` をなるべく壊さずに、

- `electricity_reliability`
- `labor_mobility`
- `reskilling_capacity`
- `ai_skill_demand_gap`

だけ足す。

この場合、

- `labor_displacement` は AI shock
- `ai_skill_demand_gap` は求人側のスキル再編
- `labor_mobility` / `reskilling_capacity` は吸収力

と読める。

### 方針B: occupations を中間層に入れる

各国の中に、

- clerical
- professional
- technical
- frontline service
- industrial / logistics
- care

の occupation bucket を持ち、bucket ごとに exposure を変える。

こちらのほうが research には近い。

## Source Links

- ILO 2025 refined index:
  https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure
- ILO 2025 update brief:
  https://www.ilo.org/publications/generative-ai-and-jobs-2025-update
- ILO article on Europe and beyond:
  https://www.ilo.org/resource/article/generative-ai-work-what-it-means-jobs-europe-and-beyond
- IMF 2024 Gen-AI and future of work:
  https://www.imf.org/en/publications/staff-discussion-notes/issues/2024/01/14/gen-ai-artificial-intelligence-and-the-future-of-work-542379
- IMF 2026 skills and vacancies blog:
  https://www.imf.org/en/blogs/articles/2026/01/14/new-skills-and-ai-are-reshaping-the-future-of-work
- IMF 2025 Japan labor market paper:
  https://www.imf.org/en/Publications/WP/Issues/2025/09/19/The-Impact-of-Aging-and-AI-on-Japan-s-Labor-Market-Challenges-and-Opportunities-570528
- World Bank 2025 low/middle income exposure paper:
  https://documents1.worldbank.org/curated/en/099629202052521198/pdf/IDU-37d75e66-4ee0-45c9-9c7f-dc4831e7fa02.pdf
- Anthropic Economic Index:
  https://www.anthropic.com/news/the-anthropic-economic-index
- U.S. Census BTOS AI snapshot:
  https://www.census.gov/library/working-papers/2024/adrm/CES-WP-24-16.html
- U.S. Census AI adoption story:
  https://www.census.gov/about/history/stories/monthly/2025/july-2025.html
- WEF Future of Jobs 2025 jobs outlook:
  https://www.weforum.org/publications/the-future-of-jobs-report-2025/in-full/2-jobs-outlook/
- WEF report digest:
  https://www.weforum.org/publications/the-future-of-jobs-report-2025/digest/
- NBER Generative AI at Work:
  https://www.nber.org/papers/w31161
- NBER Artificial Intelligence and Technological Unemployment:
  https://www.nber.org/papers/w33867
- NBER AI, Productivity, and the Workforce: Evidence from Corporate Executives:
  https://www.nber.org/papers/w34984

## 次にやるとよいこと

1. `major_powers_20year_outlook.yaml` に research-based パラメータコメントを足す
2. `labor_mobility` と `reskilling_capacity` を state に追加する
3. `occupation buckets` を国別 state の中間層として入れる
4. `Japan / US / EU / India / Brazil` の比較シナリオを、研究知見ベースで再調整する
