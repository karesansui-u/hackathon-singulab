# ポスト資本主義ではなく「持続主義で資本主義を補完する」シミュレーション設計メモ

この文書は、`hackathon-singulab` を次の段階へ拡張するための設計メモである。
目的は、別の LLM や別の開発者がこの構想を一読で把握できるように、前提、目的、状態変数、報酬、Goodhart 対策、実装段階をまとめておくことにある。

## 1. 一言でいうと何を作るのか

市場経済は残す。
そのうえで、市場が十分に報酬化できないが、社会・組織・家族・環境の長期維持には本質的な活動に対して、別の報酬系を与える。

その別の報酬系は、各スケールの構造持続ポテンシャル

`S = M e^{-L}`

の改善に基づく。

ただし、`S` そのものを通貨化するのではなく、介入によって生じた `信用できる ΔS` を通貨化する。

## 2. 世界観

このシミュレーションは「反資本主義」ではない。
目指すのは、資本主義の欠点を持続主義で補完した複合秩序である。

基本発想:

- `cash`: 通常の市場経済による収入
- `structure credits`: 構造持続への寄与に対する収入

この世界では、次のような活動でも生活できる。

- 対立調停
- 家族・地域・組織の関係修復
- 選択肢の増加
- 冗長性の確保
- 矛盾の整理
- ケア、介護、孤立防止
- 教育、技能継承
- 環境修復
- サプライチェーンや制度の脆弱性低減

要するに、
「市場価格では十分に支払われないが、文明の持続に必要な仕事」
が `structure credits` によって報酬化される世界を試す。

## 3. 理論との接続

この設計は、構造持続理論の最小形式とその写像手順に依拠する。

- `M`: 修復・再編・判断・行動・適応に使える余力
- `L`: 累積構造損失。矛盾、分断、依存集中、脆弱性、環境劣化など
- `S = M e^{-L}`: そのスケールの構造持続ポテンシャル

このシミュレーションでは、`L` は単なる損害の総量ではない。
「維持可能な選択肢や整合的経路をどれだけ削っているか」を表す。

## 4. スケール

最初から単一の社会全体指標に潰さない。
少なくとも次のスケールを別々に持つ。

1. 個人
2. 家系
3. 組織
4. 地域
5. 国家
6. 世界
7. 環境

これらは独立ではなく依存グラフでつながる。

例:

- 個人の失業は家系の `S` を削る
- 家系の崩壊は地域の `L` を増やす
- 組織の短期利潤追求は国家や環境の `L` を増やす
- 環境悪化は全スケールの `M` を削る

## 5. 各スケールの状態変数

各スケール `x` に対して、少なくとも以下を持つ。

- `S_x`: 構造持続ポテンシャル
- `M_x`: 修復余力、冗長性、資源、信頼、制度余力
- `L_x`: 累積構造損失
- `N_x`: 有効選択肢多様性
- `U_x`: 未整理矛盾・未解決対立・更新失敗
- `D_x`: 依存集中度
- `B_x`: 基本的必要充足
- `R_x`: 回復時間または回復困難性
- `I_x`: 測定の信頼性

直感:

- `N_x` は「別ルートがあるか」
- `U_x` は「見えないまま積み残しているズレ」
- `D_x` は「一箇所が壊れると全体が壊れるか」
- `B_x` は「最低限、生きていけるか」
- `R_x` は「壊れた後に戻れるか」

## 6. あるべき状態

この設計では、理想の一点を置かない。
代わりに「生存可能域」と「期待される挙動帯」を置く。

各スケールごとに以下を持つ。

- `S_min`
- `B_min`
- `N_min`
- `U_max`
- `D_max`
- `R_max`

つまり「よい状態」は、

- 壊れていない
- 必要充足を下回っていない
- 選択肢が消えていない
- 矛盾が積み上がりすぎていない
- 依存が集中しすぎていない
- 回復不能域に入っていない

という帯域で定義する。

## 7. 最重要設計原則: raw S ではなく credited ΔS

`S` をそのまま通貨化すると失敗する。

理由:

- もともと強い主体が有利すぎる
- 既に安定な系ほど報酬を取りやすい
- 改善ではなく保有が通貨化される
- Goodhart 化しやすい

したがって通貨化するのは `raw ΔS` ではなく、次の性質を満たす `credited ΔS` である。

- 本当に改善した
- その行動が原因といえる
- 短期の見せかけではない
- 他スケールに損失を押しつけていない
- 選択肢を増やすか、少なくとも減らしていない
- 矛盾を隠しただけではない

## 8. credited ΔS の骨格

行動 `a` に対する報酬の骨格は次のように置く。

```text
credited_ΔS(a) =
  persistence(a)
  × causal_attribution(a)
  × alignment(a)
  × positive_multiscale_gain(a)
  - externality_penalty(a)
  - option_loss_penalty(a)
  - manipulation_penalty(a)
  - uncertainty_penalty(a)
```

意味:

- `persistence`: 改善が数ターン維持されたか
- `causal_attribution`: 本当にその介入が原因か
- `alignment`: 期待される改善方向と一致しているか
- `positive_multiscale_gain`: 複数スケールで見て正の改善か
- `externality_penalty`: 他スケールへ損失移転していないか
- `option_loss_penalty`: 選択肢を無意味に減らしていないか
- `manipulation_penalty`: 指標ハックしていないか
- `uncertainty_penalty`: 測定が不確かなのに確定報酬化していないか

## 9. 乖離の可視化

この設計で重要なのは、「明らかにおかしい・無意味・結局 S の最大化になっていないもの」が乖離として浮き出ること。

乖離は最低でも4種類に分ける。

### 9.1 state divergence

現在状態が生存可能域からどれだけ外れているか。

```text
d_x(t) =
  a1 [S_min - S_x]_+
+ a2 [B_min - B_x]_+
+ a3 [N_min - N_x]_+
+ a4 [U_x - U_max]_+
+ a5 [D_x - D_max]_+
+ a6 [R_x - R_max]_+
```

### 9.2 trajectory divergence

期待される改善方向に進んでいるか。

例:

- 調停なら `U↓`, `信頼↑`, `将来のL↓`
- 教育なら `M↑`, `N↑`
- 冗長化なら `D↓`, `R↓`

### 9.3 cross-scale divergence

あるスケールの改善が、別スケールの悪化で帳尻合わせされていないか。

例:

- 組織 `S` は上がったが環境 `S` が大きく落ちた
- 国家 `S` は上がったが個人の `B` と `N` が崩壊した

### 9.4 semantic divergence

名目上の行動目的と実際の結果がズレていないか。

例:

- 「効率化」と言いながら実際は `N` を削って脆弱化
- 「安定化」と言いながら強制で `U` を隠蔽

## 10. Goodhart 対策のための赤旗コード

乖離は、数値だけでなく理由コードで出す。

例:

- `TRANSFER`: 他スケールへ損失移転
- `FRAGILE_GAIN`: 短期改善だが回復力を削った
- `OPTION_COLLAPSE`: 選択肢を減らして改善を演出
- `METRIC_HACK`: 測定値だけ改善
- `DEFERRED_DAMAGE`: 損失を評価窓の外へ先送り
- `CONTRADICTION_HIDE`: 矛盾を解消せず隠した
- `POWER_CONCENTRATION`: 権力集中で局所 `S` を上げた
- `COERCIVE_STABILITY`: 強制による安定化で自律性を毀損

この赤旗コードは、報酬判定だけでなく、分析 UI や LLM への説明にも使う。

## 11. 報酬の基本式

行動 `a` の価値は、概念上は次でよい。

```text
value(a) =
  Σ_x w_x · ΔS_x^+
+ λ Σ_x reduction(d_x)
- ρ Σ_x ΔS_x^-
- ξ risk_transfer(a)
- ζ gaming(a)
```

重要なのは、`ΔS_x^+` だけでなく `reduction(d_x)` を入れること。
これにより、

- 単に強い系をさらに強くする

よりも、

- 壊れかけた系を生存可能域へ戻す

行動が評価される。

## 12. hard constraint

報酬計算だけに任せず、次は hard constraint とする。

- 下位スケールの壊滅で上位スケールの改善を買ってはいけない
- 環境スケールには代替不能な下限を置く
- `N_x` の急減は原則ペナルティ
- `U_x` の増加を伴う改善は仮払い扱い
- 数ターン維持されるまで full reward を出さない

要するに、目的は「総 `S` 最大化」ではなく、
「多層制約つきの構造持続改善」である。

## 13. agent の収入構造

各 agent は少なくとも二種類の収入を持つ。

- `cash_income`
- `structure_credit_income`

`cash` は通常の市場活動で得る。
`structure credits` は `credited_ΔS` に応じて得る。

これにより agent は、

- 短期利益だけを追う
- 長期的な構造維持を支える
- その折衷を狙う

の戦略を選べる。

## 14. どんな活動が報酬化されるべきか

以下は `structure credits` の候補。

- ケア
- 孤立防止
- 調停
- 教育
- スキル継承
- 誤情報の訂正
- 依存構造の可視化
- 冗長化投資
- 地域ネットワーク形成
- 防災
- 環境修復
- 制度改善
- 物流や福祉のボトルネック解消

## 15. LLM にやらせる仕事

この世界は大規模なので、全 agent を毎ターン LLM にかけない。

LLM は主に次を担当する。

- 注目 agent の意思決定
- 乖離理由の解釈
- どの介入が `credited_ΔS` を生みそうかの提案
- 赤旗コードの自然言語説明
- スケール間対立の要約

大半の agent 更新はルールベースまたは軽量更新でよい。

## 16. 地域・国家の持続可能期間

各地域・国家について、「今どれだけ持続できるか」を現在値だけでなく期間で持つ。

- `H_x`: 無介入で生存可能域に留まれる見込み期間
- `I*_x(H)`: `H` ターン持続させるための最小介入量
- `T*_x(B)`: 介入予算 `B` で維持できる期間
- `P_survive(x, H | policy)`: 特定政策下で `H` ターン後も生存可能域にいる確率

ここでいう介入は、現金注入だけではない。

- 食料・水・エネルギー供給
- インフラ修復
- 技術移転
- 教育・医療支援
- 債務再編
- 制度設計支援
- 安全保障
- 情報透明化

重要なのは、「今の `S_x` が高いか」だけでなく、
「何ターン持つか」
「どれだけ支援すれば自走可能な構造に入るか」
を問えるようにすること。

## 17. 国際協力は共同レジリエンス投資として扱う

国家間協力は善意だけでなく、自国の `L` を下げる合理的投資として表現する。

国 A が国 B を支援したとき、B の `S` だけでなく、A や世界全体にも次の効果が返る。

- 物流断絶リスクの低下
- 紛争や難民流出の波及低下
- 資源価格乱高下の抑制
- 共有 chokepoint の安定化
- 同盟ネットワークの信頼増加

したがって、国際協力の評価は一国の改善ではなく、`cross-border credited_ΔS` として計上する。

```text
cooperation_value(A -> B) =
  direct_gain(B)
+ indirect_gain(A)
+ network_stability_gain(world)
- burden_cost(A)
- dependency_lock_in_penalty
```

これにより、援助を「持続を支える共有インフラ投資」として扱える。

### 17.1 戦争と強制的外部化

地域・国家スケールでは、自国の持続可能性が崩れそうなとき、協力だけでなく強制的外部化が起きうる。
これは歴史的にも現代的にも、

- 国内の生存圧力や体制維持圧力
- 資源・物流・制裁の締め付け
- 領土や海域の争点
- 同盟と核抑止による直接戦争の抑制

の組み合わせで現れる。

したがって世界モデルでは、戦争を単純なランダムイベントにしない。
少なくとも次の順でエスカレーションするほうが現実に近い。

1. `gray-zone coercion`
2. `proxy war / coercive campaign`
3. `limited war`

重要なのは、特に核抑止や同盟抑止が強い組み合わせでは、
全面戦争よりも灰色地帯の圧力、海上・経済・技術・情報領域での coercion が先に立ちやすいこと。

このモデルでは、戦争を「自国の `S` を守るための危険な外部化戦略」として扱う。
短期的な rally 効果や攪乱効果はあっても、長期的には `war_burden` として自国の `M` を削り、`L` を増やす。

### 17.2 戦争は確定攻撃ではなく確率的エスカレーションとして扱う

より現実に近づけるなら、戦争は `attack = true / false` の単純行動ではなく、
`hazard` と `escalation probability` の組み合わせで扱うほうがよい。

つまり各国家ペア `(A, B)` に対して、各 turn で

- `p_gray_zone(A -> B, t)`
- `p_proxy(A -> B, t)`
- `p_limited_war(A -> B, t)`

を計算し、その turn に実際の event が発火するかを確率的に決める。

この確率は少なくとも次の変数に依存する。

- `survival_pressure(A)`: 自国存続圧力
- `domestic_diversion_incentive(A)`: 国内不満を外部化したい誘因
- `target_fragility(B)`: 相手が崩れやすいか
- `territorial_salience(A, B)`: 領土・海域・物流争点の強さ
- `resource_gain(A, B)`: 資源・chokepoint・制裁回避の利得
- `alliance_gap(A, B)`: 同盟支援の不確実性
- `deterrence(A, B)`: 核抑止・軍事抑止・経済抑止
- `war_fatigue(A)`: 既存の戦争負担

イメージとしては次の形になる。

```text
p_mode(A -> B, t) =
  sigmoid(
    α * survival_pressure(A)
  + β * domestic_diversion_incentive(A)
  + γ * target_fragility(B)
  + δ * territorial_salience(A, B)
  + ε * resource_gain(A, B)
  - ζ * deterrence(A, B)
  - η * war_fatigue(A)
  )
```

重要なのは、戦争を「起こす/起こさない」の意思決定だけでなく、
「起こりやすさがどこまで高まっているか」を state として持つこと。

ハッカソン実装では次の 2 モードを用意するとよい。

1. `stochastic mode`
   確率から event をサンプルする。毎回少し違う歴史になる。
2. `deterministic replay mode`
   乱数 seed を固定するか、期待値上位だけを発火させる。デモ再現性が高い。

これにより、

- 平時は線が出ない
- 緊張が高まると `war_pressure` が上がる
- しきい値を超えると一定確率で `gray-zone` が出る
- さらに条件が重なると `proxy` や `limited war` が出る

という自然な見え方になる。

### 17.3 国内崩壊も段階付きの確率過程として扱う

国内内部の崩壊も、`riot = true` のような単発イベントではなく、
不満の蓄積とエスカレーション段階で扱うほうが精度が出る。

各国家に対して次の潜在変数を持つ。

- `economic_stress`
- `legitimacy_stress`
- `mobilization_capacity`
- `coercion_capacity`
- `elite_fragmentation`
- `communal_polarization`
- `trigger_shock`

ここで重要なのは、重課税そのものではなく
`生活維持不能感` と `制度への不信`
が protest や暴動の核になること。

したがって、税制は直接変数というより、

- 可処分所得悪化
- 若年失業
- 住宅負担
- 食料・エネルギー負担
- 債務負担
- AI 失職圧力

を通じて `economic_stress` を上げるものとして入れる。

国内状態は少なくとも次の段階を持てる。

1. `stable`
2. `grievance`
3. `protest`
4. `mass_protest`
5. `riot`
6. `insurgency`
7. `civil_conflict`

各 turn で段階遷移確率を計算する。

```text
p(protest | state) =
  sigmoid(
    a * economic_stress
  + b * legitimacy_stress
  + c * mobilization_capacity
  + d * trigger_shock
  - e * coercion_capacity
  - f * relief_support
  )
```

```text
p(riot | protest_state) =
  sigmoid(
    g * repression_mismatch
  + h * elite_fragmentation
  + i * communal_polarization
  + j * unemployment_shock
  - k * trusted_mediation
  )
```

```text
p(civil_conflict | riot_state) =
  sigmoid(
    l * armed_capacity
  + m * elite_fragmentation
  + n * territorial_fragmentation
  + o * external_sponsorship
  - p * regime_cohesion
  )
```

これにより、

- 重課税や就職難がただちに内乱を生むわけではない
- しかし生活苦と制度不信が続くと protest 確率が上がる
- protest が長引き、弾圧や分断が重なると riot へ進みやすい
- さらに武装化能力や外部支援があると civil conflict に近づく

という、より現実に近い挙動を表現できる。

### 17.4 戦争と国内崩壊は相互作用させる

国内崩壊と対外戦争は別系統ではなく、相互に影響する。

- 国内不満が高いと `domestic_diversion_incentive` が上がり、対外 coercion の確率が上がる
- 対外戦争が長引くと `war_burden` が増え、国内の `economic_stress` と `legitimacy_stress` が悪化する
- 支援や `structure credits` がうまく機能すると protest と war の両方を下げうる

したがって、国家スケールの主要変数としては最低でも次を持つ。

- `war_pressure`
- `protest_pressure`
- `riot_pressure`
- `elite_fragmentation`
- `domestic_diversion_incentive`
- `war_fatigue`

そして viewer 上では、

- 平時は線を出さない
- 支援や交渉が走ったときだけ青線
- coercion や war event が発火したときだけ赤/紫/黒の矢印
- 国内不安は地図上のノードの halo や pulse で見せる

とすると、情報量と直感のバランスがよい。

### 17.5 国家を 1 人格として扱わない

国家を 1 つの agent として扱うと、挙動が不自然になりやすい。
現実の国家は、少なくとも次の論理の衝突として動く。

- 行政府トップ
- 財務・経済
- 安全保障
- 社会・雇用
- 与党内調整や世論対応

したがって、国家ノードは `1 人格` ではなく、
`制度データで制約された奇数メンバーの政治ユニット`
として扱うのが自然である。

最小構成は `3 人`、標準は `5 人` とする。

- 3 人構成: `executive`, `economy`, `security`
- 5 人構成: `executive`, `economy`, `security`, `social`, `political`

奇数にする理由は、各 turn で決定を止めずに合意を収束させるためである。

### 17.6 先に入れるべきなのは「国民性」ではなく制度プロファイル

国の振る舞いを `慎重`, `攻撃的`, `協調的` のような性格だけで表すと、
かなり雑なモデルになる。

先に必要なのは、国家の `political_profile` である。

最低限ほしい変数は次。

- `state_capacity`
- `fiscal_slack`
- `bureaucratic_capacity`
- `coalition_fragility`
- `elite_fragmentation`
- `military_autonomy`
- `public_trust`
- `protest_sensitivity`
- `media_plurality`
- `corruption_patronage`
- `judicial_constraint`
- `centralization`
- `external_dependency`
- `update_cost`

ここで `update_cost` は、
国家が前提を変え、政策を組み替え、役割を再配分する際の
`前提のアップデートコスト`
を表す。

このデータがあると、同じ shock を受けても

- すぐレイオフや政策転換に向かう国家
- 表面上は維持するが若年層の選択肢が静かに縮む国家
- 抑圧でしばらく耐える国家

を分けられる。

### 17.7 政治メンバーは「性格」ではなく弱い政策気質を持つ

制度データの上に、各メンバーごとの弱い政策気質を重ねる。
これは国民性ではなく、役職や派閥の傾向として読む。

例:

- `hawkishness`
- `redistribution_preference`
- `technocracy_bias`
- `protest_tolerance`
- `update_resistance`
- `risk_aversion`

重要なのは、これらを主因にしないこと。
主因はあくまで `political_profile` と当該 turn の state であり、
気質は tie-break や優先順位の違いを作る程度に留める。

### 17.8 各メンバーが何を見るか

各メンバーは同じ国家状態を読むが、重視する変数が違う。

- `executive`
  - `S_state`
  - `legitimacy_stress`
  - `coalition_fragility`
  - `war_fatigue`
- `economy`
  - `cash_stability`
  - `fiscal_slack`
  - `support_needed`
  - `labor_displacement`
- `security`
  - `war_pressure`
  - `deterrence`
  - `military_autonomy`
  - `domestic_diversion_incentive`
- `social`
  - `B_state`
  - `protest_pressure`
  - `riot_pressure`
  - `youth_entry_pressure`
- `political`
  - `public_trust`
  - `media_plurality`
  - `elite_fragmentation`
  - `update_cost`

これにより、同じ turn でも
「財政上は無理」「安全保障上は妥協できない」「社会的にはもう持たない」
といった対立が自然に出る。

### 17.9 委員会の意思決定フロー

各 turn の国家意思決定は、次の 5 段階で行う。

1. `state ingestion`
   国家状態、外部イベント、国際圧力、国内不安、資源制約を読む
2. `member evaluation`
   各メンバーが自分の目的関数で政策候補を採点する
3. `intra-state bargaining`
   互いの譲歩条件を評価し、短い交渉を行う
4. `decision aggregation`
   多数決、重み付き投票、または拒否権付き多数決で確定する
5. `post-decision update`
   採られた決定に応じて `public_trust`, `elite_fragmentation`, `update_cost` などを更新する

このとき政策候補は、まずは離散集合でよい。

- `maintain_status_quo`
- `tighten_security`
- `increase_support_request`
- `launch_structure_credit_program`
- `cut_spending`
- `subsidize_households`
- `seek_mediation`
- `externalize_pressure`

### 17.10 合意ロジック

最初の実装では、次の 3 パターンを用意すれば十分である。

1. `simple majority`
   最多得票案を採用
2. `weighted majority`
   `executive` や `economy` に少し重みを乗せる
3. `veto-aware majority`
   `security` または `executive` が特定条件下で veto を持つ

この切り替え自体が国家の制度差になる。

例:

- 大統領制で安全保障が強い国: `veto-aware majority`
- 連立政権で財政制約が強い国: `weighted majority`
- 調整国家: `simple majority`

### 17.11 何をデータで入れ、何を LLM に任せるか

この設計では、
`性格データ` を先に置くのではなく、
`制度データ + 役割エージェント + 弱い気質`
の順で積む。

- データで入れる:
  - `political_profile`
  - 制度の veto 構造
  - 国家能力
  - 財政余地
  - 抗議耐性
  - 軍・官僚の自律性
- LLM に任せる:
  - 状態解釈
  - 部局間の優先順位対立
  - 短い交渉
  - その turn の説明可能な決定理由

### 17.12 実装の現実解

全国家で毎 turn 5 人の LLM を回すと重い。
したがって、現実的には次の hybrid がよい。

- 全国家:
  `political_profile` を持つルールベース国家
- 注目国家だけ:
  `3〜5 人の政治委員会` を有効化
- 大きな shock が起きた turn だけ:
  委員会を起動して、その国家の決定を LLM で上書きする

この形なら、30〜50 国家でも回しやすく、
しかも国家ごとの「リアルな立ち振る舞い」をかなり出せる。

## 18. AI 進歩シナリオの基本軸

AI による雇用代替を入れるときは、まず 2 軸で見る。

1. `automation_velocity`
2. `adaptation_velocity`

意味:

- `automation_velocity`: LLM・ソフトウェア・フィジカルAI が仕事を代替する速さ
- `adaptation_velocity`: 分配、制度、教育、所有、持続報酬系が追いつく速さ

この 2 軸だけで、次の世界が分かれる。

- `高自動化 × 低適応`: 雇用喪失が先行し `cash` が崩れる
- `高自動化 × 高適応`: 雇用は減るが `structure credits` と分配で社会が持つ
- `低自動化 × 低適応`: 長期停滞と格差固定
- `低自動化 × 高適応`: 置換は遅いが制度を先回りで整備できる

## 19. 実装では 3 軸で持つ

シミュレーション変数としては、次の 3 軸がよい。

- `A_cog`: 認知労働の自動化速度
- `A_phy`: 身体労働の自動化速度
- `G_dist`: 分配・所有・制度適応の質

`G_dist` には次を含める。

- `structure credits` の設計品質
- 最低保障
- 税と再分配
- 共同所有や配当権
- 再教育・移行支援
- 企業・国家・共同体の協調能力

これにより、次の違いを比較できる。

- LLM は急速に進歩するがロボティクスは遅い世界
- 認知と身体の両方が 5 年で急進展する世界
- 技術は進むが制度が壊れる世界
- 技術進歩が `M` を増やす形で社会へ再注入される世界

## 20. 地域ごとの AI 普及制約

同じ AI 技術でも、各国・各地域で普及速度は違う。
その差は地政学・資源・制度で表現する。

最低限ほしい係数は次。

- `compute_access`
- `energy_cost`
- `robotics_supply_access`
- `rare_mineral_dependency`
- `export_control_risk`
- `sanction_risk`
- `alliance_support`
- `social_acceptance`
- `regulatory_friction`
- `knowledge_capacity`

これにより、例えば同じ `A_cog` でも、

- 電力が高く計算資源にアクセスできない国
- 制裁で半導体やロボット部材が止まる国
- 技術はあるが社会受容が低い国

では、雇用代替速度と社会影響が変わる。

## 21. AI 失業下の二重経済

AI が多くの仕事を代替すると、`cash` だけを所得源にする社会は不安定になりやすい。

そのため各 agent の収入構造は、AI 時代ほど次の形を重視する。

- `cash_income`: 市場売上、雇用、投資、配当
- `structure_credit_income`: 構造持続への寄与報酬
- `capital_share_income`: AI・ロボット・計算資源・共同基金への持分収入

ここで重要なのは、失業者救済だけではなく、
「市場価格では捉えきれないが、社会の `M` を増やし `L` を下げる活動」
を主たる所得源にできること。

例:

- ケア
- 調停
- 地域再編
- 誤情報訂正
- 教育と技能移行
- 環境修復
- 災害予防
- 依存構造の冗長化

### なぜ「一気に崩壊」ではなく、20年かけた再編として考えるのか

この設計では、AIの未来を単発のシンギュラリティとしては扱わない。
より自然なのは、

- `A_cog` が先に進む
- `A_phy` が少し遅れて進む
- `G_dist` がその間に合うかどうかで社会の壊れ方が分かれる

という見方である。

つまり、起きるのは
「ある日突然すべての雇用が消えること」
よりも、
「まず入口の雇用と中間職が痩せ、あとから物理世界の仕事が再編されること」
である。

この見方にすると、20年スパンは長すぎる仮定ではなく、
技術・制度・雇用慣行・インフラがずれる速度としてかなり自然になる。

### 米国型と日本型は、崩壊の出方が違う

同じ AI ショックでも、社会の見え方は国によって大きく違う。

- 米国型: 解雇と採用停止で `L` を早く顕在化させる。短期の痛みは大きいが再編も速い。
- 日本型: 終身雇用や配置転換で表面の雇用を維持しやすいが、若年層の `N` と将来の選択肢が静かに縮む。

したがって、このシミュレーションでは
「どちらがマシか」
ではなく、
「どのスケールで、どの損失が先に見えるか」
を比較する必要がある。

### なぜ structure credits が効くのか

人間が AI の変化に鈍いのではなく、
生活がかかった状態では前提のアップデートコストが高すぎる、
と考えたほうがよい。

人は、

- 今の仕事にしがみつくべきか
- もう別の技能や役割へ移るべきか

を頭では理解していても、

- 住宅
- 扶養
- 組織評価
- 学び直しの時間と費用

があるため、すぐには動けない。

この意味で `structure credits` は、単なる再分配ではない。
それは、
`生活Sを市場賃金から少し切り離し、前提のアップデートと役割移行を可能にする外部代謝`
として読むことができる。

## 22. マネーゲーム勝者と持続投資

この世界では、マネーゲームの勝者が構造持続に寄与すると、継続的に自分も得をする設計にする。

単なる慈善ではなく、将来損失を減らす合理的ヘッジとして扱う。

勝者が `structure credits` や共同基金を通じて投資すると、次の便益を得る。

- サプライチェーン安定による将来収益改善
- 政治不安・暴動・紛争波及の低下
- 保有資産の毀損確率低下
- 協調ネットワーク上の信用増加
- 制度優遇や保険料低下

概念上は次のように置ける。

```text
resilience_return(i) =
  avoided_loss(i)
+ supply_chain_stability_gain(i)
+ cooperation_reputation_gain(i)
+ policy_preference_gain(i)
- upfront_contribution_cost(i)
```

これにより、
「短期 cash で勝った主体が、長期 S の維持に投資するほど自分の将来利得も守られる」
構造を作る。

## 23. 実装方針

段階的に作る。

### Phase 1: ハッカソン最小構成

- `cash` と `structure credits` の二重報酬
- スケールは `個人 / 組織 / 地域 / 環境` の4つでもよい
- `credited_ΔS` は簡略版
- 赤旗コードは数個から開始
- 50〜100 agent 規模
- AI シナリオ軸は `A_cog` と `G_dist` の簡略版から始める

### Phase 2: 理論寄り拡張

- 家系、国家、世界を追加
- `N`, `U`, `D`, `R` を明示変数化
- cross-scale divergence を厳格化
- `H_x`, `I*_x(H)`, `P_survive` を導入
- 国家間協力と chokepoint を追加

### Phase 3: 長期実験

- 200 agent 以上
- 100 turn 前後
- ルールベース更新 + 注目 agent LLM の hybrid 運用
- `A_cog / A_phy / G_dist` の複数シナリオを並列比較

## 24. 成功条件

このシミュレーションが面白くなる条件は次。

- `cash` 最大化だけでは全体が壊れやすい
- `structure credits` があると、持続に必要だが市場で過小評価される行動が増える
- AI の自動化が速くても、制度適応が高ければ社会が持つ
- 国家間協力が善意ではなく相互利得として機能する
- マネーゲーム勝者の持続投資が、全体の崩壊率を下げつつ自分の損失も減らす
- ただし設計が甘いと Goodhart 化する
- 赤旗コードと乖離計測で「見せかけの改善」が浮かぶ
- 市場と持続主義の補完関係が観測できる

## 25. この文書の位置づけ

これは理論の完全な定式化ではなく、実装指向の設計メモである。
ただし、以下の方針は固定とする。

- raw `S` は通貨化しない
- `credited_ΔS` を通貨化する
- 多層整合と Goodhart 対策を最初から入れる
- 乖離は数値と理由コードの両方で可視化する
- 地域・国家ごとに持続可能期間と必要介入量を問えるようにする
- AI 進歩は `A_cog / A_phy / G_dist` の軸で世界分岐として扱う
- 資本主義を残しつつ、持続主義の報酬系で補完する

これがこのシミュレーションの中核コンセプトである。
