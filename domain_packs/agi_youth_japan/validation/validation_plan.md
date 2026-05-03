# validation plan

最初の検証項目:

- `domain.yaml` が default を継承して解決できる
- 必須ファイルが存在する
- 若者/現役世代エージェントに `エージェントID` と `人口重み_パーセント` がある
- イベント定義に `イベントID` と `開始ステップ` がある
- viewer config が default から上書きされる
- hooks は宣言されるが、未実装のものは `enabled: false` で暴走しない
