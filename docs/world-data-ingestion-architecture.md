# 世界モデル向けデータ注入アーキテクチャ

この文書は、`hackathon-singulab` の世界モデルを「最新の現実データで較正しやすい形」にするための設計書である。
目的は、地政学、エネルギー、貿易、人口、労働、気候、紛争、制裁などのデータを、場当たり的に直接シミュレーションへ差し込むのではなく、再現可能なスナップショットと正規化レイヤを通して投入できるようにすること。

## 1. 基本方針

このシミュレーションでは、観測世界と仮説世界を分ける。

- `observed baseline`: 実データから作る初期世界
- `derived indicators`: `M`, `L`, `S`, `N`, `D`, `R` のような派生指標
- `scenario overlays`: AI進歩、戦争、制裁、政策変更などの仮説修正
- `simulation state`: 各ターンの内部状態

重要なのは、最新データをそのまま内部状態に直書きしないこと。
必ず、

1. raw snapshot
2. normalized table
3. derived feature
4. simulation input

の順に流す。

## 2. 先に決めるべき原則

- raw データは immutable に保存する
- 変換後データは raw から再計算可能にする
- 観測値とシナリオ改変値を混ぜない
- すべての数値に `source`, `dataset`, `snapshot_date`, `coverage_date`, `license`, `confidence` を紐づける
- `country`, `region`, `commodity`, `sector`, `event_type` の canonical ID を決めてから実装する
- 年次、月次、日次のデータを同じ粒度で無理に持たない

## 3. レイヤ構成

世界モデルは、最低でも次の 6 レイヤに分ける。

### 3.1 reference layer

ほぼ静的な参照情報。

- `country`
- `region`
- `border`
- `alliance`
- `commodity`
- `sector`
- `chokepoint`

### 3.2 structural baseline layer

比較的ゆっくり変わる年次・四半期データ。

- 人口
- 年齢構成
- GDP
- 財政余力
- 雇用構造
- エネルギーミックス
- 食料自給
- ガバナンス
- 物流性能

### 3.3 flow layer

国や地域の依存関係を表す流量データ。

- 貿易
- エネルギー輸出入
- 電力融通
- 食料輸送
- 資本移動
- 移民

### 3.4 event layer

比較的高頻度で変わるイベント。

- 紛争
- 制裁
- 災害
- 停電
- 港湾停止
- 価格ショック

### 3.5 environment layer

- 気温異常
- 降水異常
- 干ばつ
- 洪水
- 排出
- 再生可能資源の再生速度

### 3.6 scenario layer

観測データではなく、仮説として与える。

- `A_cog`
- `A_phy`
- `G_dist`
- 政策介入
- 戦争拡大仮説
- AI 失業速度

## 4. canonical schema

データを網羅的に突っ込めるようにするには、シミュレーション固有の変数より先に canonical schema を作る必要がある。

最低限ほしい主テーブルは次。

- `dim_country`
- `dim_region`
- `dim_commodity`
- `dim_sector`
- `dim_source`
- `dim_scenario`
- `fact_macro_indicator`
- `fact_trade_flow`
- `fact_energy_balance`
- `fact_labor_indicator`
- `fact_conflict_event`
- `fact_sanction_event`
- `fact_climate_indicator`
- `fact_policy_event`
- `fact_simulation_input_snapshot`

各 fact の共通カラムは次でよい。

| column | meaning |
| --- | --- |
| `entity_id` | 国、地域、組織などの対象 |
| `time_grain` | `annual`, `quarterly`, `monthly`, `daily`, `event` |
| `period_start` | 観測開始日 |
| `period_end` | 観測終了日 |
| `metric_code` | 指標名 |
| `value` | 数値 |
| `unit` | 単位 |
| `source_id` | 出典 |
| `dataset_code` | データセット識別子 |
| `snapshot_date` | 取得日 |
| `coverage_date` | データが表す対象期間 |
| `quality_flag` | 欠損補完、速報値、推計値など |
| `confidence_score` | 信頼度 |

## 5. 更新頻度で tier を分ける

実運用では、すべてを毎回更新しない。

### 5.1 cold tier

半年から年次更新。

- 人口
- ガバナンス
- 年次エネルギーバランス
- 食料生産
- 物流性能

### 5.2 warm tier

月次から四半期更新。

- 電力
- エネルギー価格
- 輸出入
- 労働市場
- 制裁リスト

### 5.3 hot tier

日次またはイベント駆動。

- 紛争イベント
- 気候異常
- 災害
- 突発政策

この tier 分離を入れると、世界モデルの初期化コストと更新コストを分けられる。

## 6. まず入れるべき一次ソース

以下は、2026-04-16 時点で「世界モデルの現実較正」に使いやすい一次ソースまたは準一次ソースである。
無料の公開APIと、ライセンス付きの拡張ソースを分けて考える。

### 6.1 公開ベースライン

| category | source | use | cadence | access |
| --- | --- | --- | --- | --- |
| マクロ全般 | World Bank Indicators API | GDP、貧困、エネルギー、保健、教育などの国別基礎指標 | 更新は指標ごと | 公開 API |
| ガバナンス | Worldwide Governance Indicators | 政治安定、政府有効性、法の支配など | 年次 | 公開 |
| 物流 | World Bank LPI | 物流性能、通関、輸送インフラ、追跡性 | 低頻度 | 公開 |
| マクロ・金融 | IMF Data API | 国際収支、財政、金融、外部部門など | データセットごと | 公開 API |
| 人口 | UN World Population Prospects 2024 | 人口、年齢構成、将来人口 | 年次更新の版管理 | 公開ダウンロード |
| 労働 | ILOSTAT SDMX API | 雇用、失業、労働参加率、賃金系指標 | 指標ごと | 公開 API |
| 農業・食料 | FAOSTAT API | 作物生産、土地利用、食料需給、価格 | データセットごと | 公開 API |
| 貿易 | UN Comtrade | 品目別輸出入、相手国依存、供給網 | 定期更新 | API キー |
| エネルギー | EIA Open Data API | 国際エネルギー、価格、供給、発電など | データセットごと | 公開 API |
| 再エネ | IRENA Data / IRENASTAT | 再エネ容量、発電、再エネバランス | 年次中心 | 公開 |
| 気候 | Copernicus Climate Data Store | 気温、降水、再解析、気候異常 | データセットごと | API |
| 制裁 | OFAC Sanctions List Service | 制裁対象、更新時点、対象種別 | 高頻度 | 公開ダウンロード |
| 紛争 | ACLED API | 紛争、暴動、暴力イベント、位置 | 高頻度 | アカウント/API |

### 6.2 有償または拡張ソース

| category | source | use | note |
| --- | --- | --- | --- |
| エネルギー総覧 | IEA World Energy Statistics | 国別エネルギーバランス、長期系列 | より包括的だがライセンス確認が必要 |
| 月次電力 | IEA Monthly Electricity Statistics | 国別電力生産と電力貿易 | 月次で現実較正しやすい |
| エネルギー速報 | IEA Global Energy Review Dataset | 世界・主要国の近年速報値 | 年次速報の補強に有効 |

ポイント:

- 公開ベースラインだけでも十分に強い世界モデルは作れる
- IEA は精度と整合性が高いが、配布条件を確認して premium augmentation として扱う
- AI やロボティクス進歩は一次ソースの定常データより、scenario layer で扱うほうが安定する

## 7. source registry の形

実装するときは、データソースをコードに埋め込まず registry 化する。

```yaml
sources:
  - source_id: world_bank_indicators
    category: macro
    url: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation
    entities: [country]
    cadence: mixed
    access: public_api
    metrics:
      - NY.GDP.MKTP.CD
      - SP.POP.TOTL
      - EG.USE.PCAP.KG.OE
  - source_id: un_comtrade
    category: trade
    url: https://comtradeplus.un.org/TradeFlow
    entities: [country, commodity]
    cadence: periodic
    access: api_key
```

この registry を持つと、後で別の LLM が見ても

- どのデータがどこから来るか
- 何をどの粒度で持つか
- どの認証が必要か

がすぐ分かる。

## 8. データの置き場所

最低限、保存先は次の 4 層に分ける。

```text
data/
  raw/
    {source_id}/{dataset_code}/{snapshot_date}/...
  staging/
    {source_id}/{dataset_code}/{snapshot_date}/...
  curated/
    macro/
    energy/
    trade/
    conflict/
    climate/
  simulation_inputs/
    baseline/{world_snapshot_id}/
    scenarios/{scenario_id}/
```

`raw` は取得そのまま。
`staging` は軽い整形。
`curated` は canonical schema に合わせた正規化済み。
`simulation_inputs` は実際にシミュレーションへ渡す素材。

## 9. ID の正規化

現実データを深く突っ込むと、ID の不一致が一番の事故源になる。
先に正規化ルールを固定する。

- 国は `ISO3`
- 地域は `world_region_id`
- 品目は `HS` または独自 `commodity_id`
- エネルギー品目は `energy_product_code`
- セクターは独自 `sector_code`
- イベントは `event_source_id + event_native_id`

特に重要なのは、`country` と `region` を混同しないこと。
国家、交易圏、電力圏、資源圏、気候圏は別の ID 空間で持つ。

## 10. 現実データから世界状態へ変換する

観測データはそのまま `M` や `L` ではない。
変換ルールを明示する必要がある。

例:

- `M_region`
  - 財政余力
  - エネルギー余剰
  - 食料備蓄
  - 物流性能
  - 制度能力
  - 教育水準

- `L_region`
  - 輸入依存集中
  - 制裁露出
  - 紛争頻度
  - 気候脆弱性
  - ガバナンス脆弱性
  - 不平等や必要充足不足

大事なのは、`feature engineering` を別レイヤにすること。
`raw -> normalized -> feature -> simulation` を崩さない。

## 11. 現実較正とシナリオ分岐を分ける

この世界モデルでは、現実較正と未来仮説を混ぜない。

- `baseline snapshot`
  現時点の世界
- `stress scenario`
  中東危機、制裁拡大、干ばつなど
- `AI scenario`
  `A_cog`, `A_phy`, `G_dist` の分岐
- `policy scenario`
  structure credits 導入、最低保障、共同基金、国際支援

こうしておくと、

- 現実世界にどれくらい近いか
- どの仮説でどう壊れるか
- どの政策でどれだけ持つか

を分離して比較できる。

## 12. ハッカソン向けの最小構成

最初から全世界フル取り込みにしない。
次の最小構成で十分強い。

- 国単位 30〜50 ノード
- `World Bank + IMF + UN WPP + ILOSTAT + FAOSTAT + UN Comtrade + EIA + ACLED + OFAC + Copernicus`
- 年次 baseline
- 月次の trade / energy / conflict 補正
- `A_cog / A_phy / G_dist` の scenario overlay

これだけでも、

- エネルギー依存
- 貿易依存
- 紛争波及
- 制裁リスク
- AI 失業の制度吸収力

までかなりリアルに出せる。

## 13. 実装順

実装は次の順がよい。

1. canonical ID と source registry を作る
2. `raw` と `curated` の保存規約を作る
3. World Bank / IMF / UN WPP / UN Comtrade / EIA を先に入れる
4. ACLED / OFAC / Copernicus を event layer として足す
5. `M`, `L`, `S`, `H_x`, `I*_x(H)` の feature 変換を作る
6. baseline snapshot から simulation input を吐く
7. scenario layer を上から被せる

## 14. この文書の位置づけ

この文書は、「どんなデータを、どんな構造で、どんな更新運用で入れるか」のための設計書である。
理論そのものは [ポスト資本主義ではなく「持続主義で資本主義を補完する」シミュレーション設計メモ](/Users/sunagawa/Project/hackathon-singulab/docs/post-capitalist-structure-sustain-simulation-design.md) を参照する。

この文書で固定したいのは次。

- 最新データは snapshot と provenance つきで入れる
- 観測世界とシナリオ世界を混ぜない
- 地政学・エネルギー・紛争・制裁は event layer と flow layer で扱う
- AI 進歩は baseline データではなく scenario overlay で扱う
- `raw -> normalized -> feature -> simulation` の変換を崩さない

## 15. 公式データ入口

以下は、2026-04-16 時点で確認した公式または公式配布元の入口 URL。
実装時はこの一覧を source registry の初期値に使う。

| source | url | note |
| --- | --- | --- |
| World Bank Indicators API | https://datahelpdesk.worldbank.org/knowledgebase/articles/889392-about-the-indicators-api-documentation | 指標 API の公式説明 |
| Worldwide Governance Indicators | https://www.worldbank.org/en/publication/worldwide-governance-indicators | ガバナンス指標の公式入口 |
| IMF Data API | https://data.imf.org/en/Resource-Pages/IMF-API | IMF の SDMX 2.1 / 3.0 API |
| UN World Population Prospects 2024 | https://population.un.org/wpp/ | 人口ベースライン |
| ILOSTAT SDMX tools | https://ilostat.ilo.org/resources/sdmx-tools/ | 労働データ API/ツール入口 |
| FAOSTAT | https://www.fao.org/faostat/ | 農業・食料データ入口 |
| UN Comtrade | https://comtradeplus.un.org/TradeFlow | 貿易データ入口 |
| EIA Open Data API | https://www.eia.gov/opendata/ | エネルギー公開 API |
| IRENA Data | https://www.irena.org/Data | 再エネ統計入口 |
| Copernicus Climate Data Store API | https://cds.climate.copernicus.eu/how-to-api | 気候 API 入口 |
| OFAC Sanctions List Service | https://ofac.treasury.gov/sanctions-list-service | 制裁リスト配布元 |
| ACLED API | https://acleddata.com/acled-api-documentation | 紛争イベント API |
| IEA Monthly Electricity Statistics | https://www.iea.org/data-and-statistics/data-product/monthly-electricity-statistics | 2026-04-16 時点で月次更新の電力データ製品 |
| IEA World Energy Statistics | https://www.iea.org/data-and-statistics/data-product/world-energy-statistics | 2026-04-16 時点で 2023 年までの本系列と一部 2024 速報値を案内 |
| IEA Global Energy Review 2025 | https://www.iea.org/reports/global-energy-review-2025 | 2024 年の速報的な世界エネルギー動向 |
