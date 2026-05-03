# 世界シミュレーション対象国の選定

この文書は、`hackathon-singulab` の世界モデル（`S = M·e^(-L)` に基づく構造持続シミュレーション）に組み込む対象国を決めるためのメモである。
理論と設計は [post-capitalist-structure-sustain-simulation-design.md](./post-capitalist-structure-sustain-simulation-design.md) を、データ注入方針は [world-data-ingestion-architecture.md](./world-data-ingestion-architecture.md) を参照する。

## 1. 目的

世界中に約 200 の国家があるが、全てを対象にするとノイズが増え、ハッカソン規模の実装では `S` の合算が鈍る。
そこで、次の4軸で「世界 S に非自明な影響を持つ国」を絞り込む。

- **戦争・軍事・同盟**: 核保有、進行中の武力紛争、flashpoint、抑止ネットワーク
- **資源・サプライチェーン**: エネルギー、重要鉱物、食料、肥料、半導体、海運 chokepoint
- **規制・金融・基軸通貨**: ルール形成、制裁執行、AI/データ規制、基軸通貨決済
- **仲介・中立・ソフトパワー**: 外交仲介の実績、人口規模で world S に効く国

最終的に **Tier 1 = 30ヶ国**（第一段階シミュレーション対象）、**Tier 2 = +20ヶ国（強推奨拡張）**、**Tier 3 = +10ヶ国（機能別補完）** の3階層で定義する。

## 2. 選定手順

3つのサブエージェントに異なる観点で独立に抽出させ、その合意度を軸に統合した。

- Agent A: 地政学・安全保障（核、同盟、chokepoint、flashpoint）
- Agent B: 資源・サプライチェーン（精錬独占、エネルギー、半導体、食料）
- Agent C: 規制・金融・仲介（ルール形成、制裁執行、仲介伝統、人口）

合意度の定義:

- **3 エージェント合意**: Tier 1（必須）
- **2 エージェント合意**: Tier 2（強推奨）
- **1 エージェント推奨 + 統合判断で機能的に不可欠**: Tier 3（補完）

### 2.1 実装用 companion の前提

この文書は人間向けの意思決定記録であり、そのままコードの入力にはしない。
実装では、[data/world_country_sets.yaml](../data/world_country_sets.yaml) を機械可読 companion として source of truth に置く。

companion に最低限必要な項目:

- `code`, `name`, `name_ja`
- `tier`
- `consensus_level`
- `agent_votes`
- `primary_axes`, `secondary_axes`
- `role_tags`
- `region_id`
- `phase1_priority`
- `lon`, `lat`
- `entity_type`
- `reason_short`

これにより、Tier の説明責任を残しつつ、シミュレーション側では

- 30ヶ国コア
- 50ヶ国拡張
- 将来の 60ヶ国拡張

を設定だけで切り替えられるようにする。

### 2.2 実装時の preset

初期実装では次の preset を持つ。

- `core_30`: Tier 1 のみ
- `current_realism_32`: `core_30` に `UKR` と `ITA` を追加した 2026 現実寄り baseline
- `europe_frontline_30`: 30ヶ国を維持しつつ `OMN`, `MAR` を外して `UKR`, `ITA` を入れた欧州戦線寄り variant
- `extended_50`: Tier 1 + Tier 2
- `full_60`: Tier 1 + Tier 2 + Tier 3

現在の推奨 baseline は `current_realism_32` である。理由は、

- `UKR` は 2026 時点でも欧州戦争・黒海穀物・支援依存の結節点であり、Tier 2 のまま既定から外すと現実感が落ちる
- `ITA` は G7 の南欧代表であり、地中海移民・債務・EU 内調整の観点で、独仏英だけでは拾い切れない

ためである。

一方、ノード数を 30 に抑えたい実験では `core_30` か `europe_frontline_30` を使い、挙動が安定した後に `extended_50` を常用対象へ広げる。

## 3. Tier 1: 30ヶ国コア構成（第一段階シミュレーション対象）

第一段階ではこの 30ヶ国で動かす。3エージェント合意のため、外すとどこかの軸が欠落する。

### 3.1 リスト（ISO3 順）

| ISO3 | 国 | 主機能軸 | 一行理由 |
|------|----|---------|---------|
| ARE | アラブ首長国連邦 | 資源・仲介 | ホルムズ隣接、ドバイ金融・物流ハブ、COP28 気候外交 |
| AUS | オーストラリア | 規制・資源 | AUKUS、Five Eyes、鉄鉱石・リチウム・石炭・LNG |
| BRA | ブラジル | 仲介・資源 | BRICS、アマゾン、ニオブほぼ独占、G20 |
| CAN | カナダ | 規制・資源 | G7、ウラン・カリ、AI 規制（AIDA）、制裁協調 |
| CHE | スイス | 仲介・規制 | 最強中立仲介、BIS、ジュネーブ、米イラン代理外交 |
| CHN | 中国 | 全軸 | 人口 14 億、レアアース精錬 90%、基軸通貨対抗 |
| DEU | ドイツ | 規制・資源 | EU 最大経済、GDPR/AI Act 執行中核 |
| EGY | エジプト | 戦争・chokepoint | スエズ運河、ガザ仲介、アラブ連盟本部 |
| FRA | フランス | 戦争・規制 | P5 核、OECD/UNESCO、アフリカ仲介 |
| GBR | イギリス | 戦争・規制 | P5 核、ロンドン金融、AI Safety Institute、OFSI |
| IDN | インドネシア | 資源・仲介 | ニッケル精錬 1 位、マラッカ、ASEAN 盟主、人口 2.8 億 |
| IND | インド | 全軸 | 核保有、人口 14 億超、グローバルサウス筆頭 |
| IRN | イラン | 戦争・資源 | ホルムズ封鎖オプション、代理網中核、制裁下 |
| ISR | イスラエル | 戦争・規制 | 曖昧核、ガザ戦争、半導体設計、サイバー |
| JPN | 日本 | 全軸 | G7、半導体素材・装置、広島 AI プロセス、ODA |
| KOR | 韓国 | 規制・資源 | DRAM/NAND 6 割超、対北最前線、AI 規制極 |
| MAR | モロッコ | 資源・仲介 | リン鉱石埋蔵 7 割超、欧州-アフリカ橋渡し |
| MEX | メキシコ | 仲介・規制 | 対米送金ハブ、G20、麻薬/移民ガバナンス |
| NGA | ナイジェリア | 仲介・戦争 | アフリカ最大経済、人口 2.2 億、ECOWAS 盟主 |
| NLD | オランダ | 資源・規制 | ASML（EUV 100%）、ロッテルダム港、ハーグ司法 |
| NOR | ノルウェー | 資源・仲介 | 欧州最大ガス、SWF 世界最大、オスロプロセス |
| OMN | オマーン | 仲介・資源 | 米イラン秘密交渉の老舗、ホルムズ南岸 |
| PAK | パキスタン | 戦争・仲介 | 核保有、人口 2.4 億、対印・アフガン接面 |
| QAT | カタール | 資源・仲介 | LNG 2 位、ハマス/タリバン仲介、Al Jazeera |
| RUS | ロシア | 全軸 | P5 核、石油・ガス・小麦・肥料・ウラン濃縮 |
| SAU | サウジアラビア | 資源・仲介 | 原油スペアキャパ、OPEC+ 盟主、G20 |
| TUR | トルコ | 戦争・仲介 | NATO、ボスポラス、黒海穀物合意仲介、人口 8500 万 |
| TWN | 台湾 | 資源・戦争 | 先端半導体 9 割超、台湾海峡 flashpoint |
| USA | アメリカ | 全軸 | 基軸通貨、LNG 最大輸出、AI 規制、軍事ネットワーク |
| ZAF | 南アフリカ | 資源・仲介 | PGM 1 位、BRICS、ICJ 提訴、アフリカ仲介 |

### 3.2 機能カバレッジの検証

この 30ヶ国で、各機能が最低何ヶ国でカバーされているかを確認する。

| 機能 | カバー国数 | 代表国 |
|------|----------|-------|
| 核保有 | 9 | USA, CHN, RUS, GBR, FRA, IND, PAK, ISR（曖昧）, TWN は非核 |
| G7 | 6 | USA, GBR, FRA, DEU, JPN, CAN（ITA は Tier 2） |
| BRICS | 5 | BRA, RUS, IND, CHN, ZAF（+ ARE, EGY, IRN は拡大 BRICS） |
| 海運 chokepoint | 5 | EGY(スエズ), IRN/OMN/ARE(ホルムズ), TUR(ボスポラス), IDN(マラッカ) |
| 先端半導体 | 5 | TWN, KOR, JPN, NLD, USA |
| 主要産油・ガス | 7 | SAU, RUS, USA, IRN, ARE, QAT, NOR |
| 重要鉱物精錬 | 3 | CHN, IDN, ZAF（COD は Tier 3） |
| 食料・肥料 | 6 | USA, RUS, CAN, BRA, IND, MAR（UKR/FRA は Tier 2） |
| 仲介伝統国 | 6 | CHE, NOR, OMN, QAT, TUR, ZAF |
| 人口 1 億超 | 10 | CHN, IND, USA, IDN, PAK, BRA, NGA, RUS, JPN, MEX |

### 3.3 地域バランス

- 北米: 3（USA, CAN, MEX）
- 欧州: 6（GBR, FRA, DEU, NLD, CHE, NOR）
- 東アジア: 5（CHN, JPN, KOR, TWN, RUS）
- 東南アジア: 1（IDN）
- 南アジア: 2（IND, PAK）
- 中東: 7（SAU, UAE, QAT, OMN, IRN, ISR, TUR, EGY）
- アフリカ: 3（NGA, ZAF, MAR）
- ラテンアメリカ: 2（BRA, MEX は北米カウント重複）
- オセアニア: 1（AUS）

東南アジアとラテンアメリカが薄い。Tier 2 拡張時に VNM, PHL, SGP, ARG, CHL, COL で補完する。

## 4. Tier 2: +20ヶ国（強推奨拡張・計 50ヶ国）

2 エージェント合意。Tier 1 の地域バランス不足と、進行中紛争の当事国を補う。

| ISO3 | 国 | 補完する機能 |
|------|----|------------|
| PRK | 北朝鮮 | 核・制裁極端値、対南直接脅威 |
| UKR | ウクライナ | 戦争当事国、黒海穀倉 |
| ITA | イタリア | G7、地中海移民ガバナンス、FAO 本部 |
| POL | ポーランド | NATO 東翼、ウクライナ支援物流 |
| VNM | ベトナム | 人口 1 億、半導体代替地、南シナ海 |
| PHL | フィリピン | 南シナ海当事国、送金経済、台風脆弱 |
| SGP | シンガポール | アジア金融・仲裁ハブ、マラッカ |
| AUT | オーストリア | IAEA/OPEC/OSCE ホスト |
| IRL | アイルランド | GDPR 執行主管、EU 内中立 |
| SYR | シリア | アサド後の地政学再編 |
| YEM | イエメン | バブ・エル・マンデブ、フーシ攻撃元 |
| LBN | レバノン | ヒズボラ、対イスラエル戦線 |
| PSE | パレスチナ | ガザ戦争、国家承認進行中 |
| IRQ | イラク | OPEC 2 位、シーア民兵、米軍残留 |
| AZE | アゼルバイジャン | ナゴルノ、BTC パイプライン |
| KAZ | カザフスタン | ウラン 1 位、中露緩衝、CSTO |
| BGD | バングラデシュ | 人口 1.7 億、気候脆弱国代表 |
| ETH | エチオピア | 人口 1.2 億、AU 本部、紅海出口問題 |
| COD | コンゴ民主 | コバルト 70%、人口 1 億、熱帯林 |
| BLR | ベラルーシ | 対露従属、戦術核配備、カリ |

## 5. Tier 3: +10ヶ国（機能別補完・計 60ヶ国）

1 エージェント推奨だが、統合判断で特定機能に不可欠と判断したもの。および 3 エージェントが軽視したが構造持続の観点で重要な追加。

| ISO3 | 国 | 追加理由 |
|------|----|---------|
| CHL | チリ | リチウム 2 位、銅 1 位、OECD ラテン優等生 |
| PER | ペルー | 銅 2 位、銀 |
| MMR | ミャンマー | 重レアアース主要産、内戦、制裁下 |
| GIN | ギニア | ボーキサイト 1 位、シマンドゥ鉄鉱石 |
| PAN | パナマ | パナマ運河（気候起因の通航制限事例） |
| DJI | ジブチ | 紅海出口、米中軍事基地併存 |
| LUX | ルクセンブルク | 欧州投資銀行、ファンド大国 |
| VAT | バチカン | 宗教仲介、米キューバ解凍仲介実績 |
| AFG | アフガニスタン | 失敗国家典型、低 S エンドポイント |
| HTI | ハイチ | 失敗国家典型、PKO 対象 |

AFG と HTI は 3 エージェントとも未選定だったが、`H_x`（持続可能期間）や `I*_x(H)`（最小介入量）のモデル挙動を検証する低 S 側の典型として、シミュ設計の観点からは不可欠と判断した。

## 6. 設計上の注意

### 6.1 TWN / HKG の ISO3 扱い

- **TWN（台湾）**: 国連非加盟だが、先端半導体で world S への寄与が巨大。独立ノードとして持つ。ただし CHN との関係は `alliance_gap` と `territorial_salience` で明示的に強く紐付ける。
- **HKG（香港）**: 中国特別行政区だが、金融ハブとしての `L` / `M` は中国本土と別トラックで計算したい。Tier 2/3 拡張時に独立ノード化するか CHN に吸収するかは設計判断。現段階では CHN に吸収。

### 6.2 小島嶼国（AOSIS）の扱い

気候脆弱小島嶼国を個別追加するとノイズが増える。代わりに、

- 気候脆弱性の代表として BGD, PHL, MOZ（Tier 拡張時）, HTI を含める
- AOSIS 全体を 1 ノード「世界スケール気候脆弱集団」として環境レイヤに集約する

### 6.3 サヘル軍政連合

マリ・ブルキナファソ・ニジェールは ECOWAS 脱退と露接近で注目されるが、3 カ国を個別に持つと冗長。Tier 3 で NER（ニジェール、ウラン）を代表ノードとし、他は NGA（ECOWAS）経由で波及させる。

### 6.4 region の別持ち

[world-data-ingestion-architecture.md](./world-data-ingestion-architecture.md) §9 で述べた通り、国家・交易圏・電力圏・資源圏・気候圏は別 ID 空間で持つ。本リストは `dim_country` の初期集合であり、`dim_region` は別途定義する。

## 7. 第一段階（30ヶ国）実装の進め方

[post-capitalist-structure-sustain-simulation-design.md](./post-capitalist-structure-sustain-simulation-design.md) §23 Phase 1 の拡張として:

1. 30ヶ国 × `国家ノード + 3人政治委員会` で開始
   - `executive`
   - `economy`
   - `security`
   必要に応じて `social`, `political` を足して 5 人構成に拡張する
2. `S`, `M`, `L`, `N`, `U`, `D` を国家スケールで持つ
3. 国家間依存グラフは、本リストの「主機能軸」から最初の近似を引く
   - 半導体: TWN ↔ USA, CHN, KOR, JPN, NLD
   - エネルギー: SAU/RUS ↔ CHN, IND, JPN, DEU, KOR
   - chokepoint: EGY, TUR, IRN, IDN が通航国への `L` 伝播ノード
   - 仲介: CHE, NOR, OMN, QAT, TUR が「紛争ペアに対する `reduction(d_x)` 提供者」
4. 戦争 event は §17.2 の hazard 式で、IRN-ISR, CHN-TWN, RUS-UKR, PRK-KOR, IND-PAK のペアを優先実装
5. スーパーノード（1 国停止で世界が確実に痛むノード）として CHN, TWN, USA, SAU, RUS, KOR, NLD, QAT, IDN の 9 国に L 伝播係数を重み付け

### 7.1 各国家に最低限持たせたい政治プロファイル

国家ごとのリアルな立ち振る舞いを出すには、
`性格` よりも次の制度変数を優先する。

- `state_capacity`
- `fiscal_slack`
- `bureaucratic_capacity`
- `coalition_fragility`
- `elite_fragmentation`
- `military_autonomy`
- `public_trust`
- `protest_sensitivity`
- `centralization`
- `external_dependency`
- `update_cost`

これがあると、同じ AI shock を受けても

- 米国型: 早く痛みを顕在化させる
- 日本型: 若年層の選択肢を縮めつつ表面を保つ
- 軍の強い国家: 抑圧で先送りする

といった違いを出しやすい。

## 8. 拡張パスのプリセット

- **32 → 50**: `current_realism_32` から Tier 2 を全て追加。PRK や POL を先に入れて戦争相互作用を完成させる
- **30 → 50**: `core_30` や `europe_frontline_30` から Tier 2 を追加
- **50 → 60**: Tier 3 を全て追加。AFG / HTI で低 S 典型、PAN で気候運河事例、CHL/PER で鉱物ラテン軸
- **60 → 80〜100**: LKA（債務再編）, ARG, FIN, SWE, DNK, BEL, KEN, COL, THA, MYS, ESP, ROU, JOR, ARM, SDN, TKM, ZWE, MOZ, MDG, KWT, DZA, AGO, HKG, NZL, NER

80 超えはシミュ精度よりノイズが増えるリスクがある。`S` 合算が特定国の微動で揺れるようなら 50〜60 に戻す。

## 9. この文書の位置づけ

これは国選定の**意思決定記録**であり、将来の国追加/削除はこの Tier 構造の上に履歴として積む。
特に次の判断は事後検証可能にする。

- どの国を外したときに world S の挙動がどう変わるか
- Tier 2/3 追加が Tier 1 だけの結果を覆すか
- サブエージェントの選定合意度と、シミュ挙動への寄与に相関があるか

選定の根拠となった 3 サブエージェントの詳細回答は本文書の執筆時点の会話ログに残る。必要なら別ファイルへの抜粋保存も可能。

## 10. 関連文書

- 理論: [post-capitalist-structure-sustain-simulation-design.md](./post-capitalist-structure-sustain-simulation-design.md)
- データ注入: [world-data-ingestion-architecture.md](./world-data-ingestion-architecture.md)
- プレゼン: [presentation-framing-world-realism.md](./presentation-framing-world-realism.md)
- ビューア: `../visualization/world_demo_viewer.html`
