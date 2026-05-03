# AGI若者日本ドメインパック移行前素材

このディレクトリは、AGI時代の若者・現役世代・国家モデルに関する、ドメインパック化前の素材置き場。

現在ここに残っているもの:

- 若者/現役世代エージェント候補
- イベント定義候補
- 更新係数候補
- 認知層・過去経験・結婚出産関連のTSV
- 国家モデル関連のTSV/設計メモ
- 出典や設計根拠の対応表

今後の方針:

- 製品仕様の正本は `docs/製品パッケージ/` に置く
- 実行入力の正本は `domain_packs/agi_youth_japan/` に移す
- ここは移行前の素材置き場として扱う
- 生成済みrowデータはここに置かず、`outputs/runs/` に置く

判断:

| 種類 | 移行先 |
|---|---|
| 実行入力として使うTSV | `domain_packs/agi_youth_japan/data/` |
| プロンプトテンプレート | `domain_packs/agi_youth_japan/prompts/` |
| 比較シナリオ | `domain_packs/agi_youth_japan/scenarios/` |
| 製品仕様 | `docs/製品パッケージ/` |
| 旧メモ | `docs/アーカイブ/` |
