# スライド編集ディレクトリ

発表用と課題提出用のHTMLスライドを、編集しやすいセクション単位に分割して管理する。

## ファイル構成

```text
スライド/
  build_slides.py
  発表用/
    template_before.html
    01_導入.html
    02_設計.html
    03_結果とデモ.html
    04_転用と締め.html
    template_after.html
  課題提出用/
    template_before.html
    01_問いと背景.html
    02_設計とLLMエージェント.html
    03_UI結果と考察.html
    04_転用限界評価.html
    template_after.html
```

## 編集方法

本文を直すときは、`発表用/` または `課題提出用/` の `01_...html` から `04_...html` を編集する。

CSS、共通JS、印刷設定を直すときは、それぞれの `template_before.html` / `template_after.html` を編集する。

## 統合方法

このディレクトリで次を実行する。

```bash
python3 build_slides.py
```

生成先:

```text
../発表用スライド_軽め.html
../課題提出用スライド_詳細版.html
```

片方だけ生成する場合:

```bash
python3 build_slides.py --deck 発表用
python3 build_slides.py --deck 課題提出用
```

## PDF化

生成されたHTMLをブラウザで開いて、`Cmd + P` からPDF保存する。

- レイアウト: 横
- 余白: なし
- 背景グラフィック: ON
