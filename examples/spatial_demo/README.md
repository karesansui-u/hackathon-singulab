# 旧2D火災シミュレータ（ハッカソン配布のベース実装）

このディレクトリには、ハッカソン配布の2D火災シミュレータのコードと設定が入っています。
本線は [`domain_packs/agi_youth_japan/`](../../domain_packs/agi_youth_japan/) で、このディレクトリは**参考実装としての保管**が目的です。**メンテナンスは止めています**。

本線（制度反応波及シミュレーター）の使い方は [リポジトリルートの README](../../README.md) を参照してください。

## なぜ残っているか

ハッカソン発表では、配布された「2D空間・イベント・エージェント・会話」という骨格を、心理・制度空間の反応観測へ抽象化したことが評価ポイントになります（[ハッカソン発表シナリオ.md](../../docs/製品パッケージ/04_発表シナリオ/ハッカソン発表シナリオ.md) 参照）。そのため、出発点となった2D火災シミュレータのコードを `examples/` 下に保存しておきます。

## 構成

| ファイル | 役割 |
|---|---|
| `main.py` | シミュレーション実行器 |
| `simulation.py` / `agent.py` / `visualization.py` | コア実装 |
| `llm_backends.py` / `ollama_client.py` | LLMバックエンド（Ollama / Claude / Codex / Gemini） |
| `utils.py` | ユーティリティ |
| `setup_mac.sh` / `setup_win.bat` | venv セットアップ補助 |
| [`configs/`](configs/) | シナリオ YAML 一式（[configs/README.md](configs/README.md)） |

## 動かす場合の手順

import がカレントディレクトリ前提のため、このディレクトリに `cd` してから実行します。

```bash
cd examples/spatial_demo
python main.py --config configs/config.smoke.yaml
```

LLMバックエンドは `configs/config.*.smoke.yaml` で切り替えます。

| 設定 | バックエンド |
|---|---|
| `config.smoke.yaml` | Ollama |
| `config.claude.smoke.yaml` | Claude Code CLI |
| `config.codex.smoke.yaml` | Codex CLI |
| `config.gemini.smoke.yaml` | Gemini CLI |

出力は `outputs/spatial/`、ログは `logs/spatial/` に書かれます。
