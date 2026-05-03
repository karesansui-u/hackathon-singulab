# 旧2D空間実験用configs

このディレクトリは、`main.py` で動かす旧2D空間シミュレーション用の設定ファイル置き場。

若者・現役世代の未来感情シミュレーションはここではなく、`domain_packs/agi_youth_japan/domain.yaml` と `domain_packs/agi_youth_japan/scenarios/` で管理する。

ルール:

- ルート直下に `config*.yaml` を増やさない
- 実行時は `examples/spatial_demo/` に `cd` してから `python main.py --config configs/config.xxx.yaml` のように指定する
- 旧2D実験の出力先は `outputs/spatial/`
- 旧2D実験のログは `logs/spatial/`

残す設定:

| ファイル | 用途 |
|---|---|
| `config.yaml` | 旧2D空間実験の標準設定 |
| `config.smoke.yaml` | Ollamaの小規模確認 |
| `config.claude.smoke.yaml` | Claude CLIの小規模確認 |
| `config.codex.smoke.yaml` | Codex CLIの小規模確認 |
| `config.gemini.smoke.yaml` | Gemini CLIの小規模確認 |
