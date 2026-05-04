# 構造持続制度ストレステスト観測プロンプト

このプロンプトは、構造持続通貨・構造持続施策が社会に入ったとき、制度がどこで壊れるか、誰に届かないか、どう悪用されるか、どのガードレールが必要になるかを観測するための雛形。

重要な前提:

- ストレステストエージェントは人口代表ではなく、制度の壊れ方・守り方を見る機能エージェントである。
- 受益者、支援者、企業、行政、ゲーム化探索者、監査者、市民社会、金融・物価の視点を分ける。
- LLMへ「この制度は成功する」と命令しない。制度情報、社会状態、前ステップ記憶、発行ルール、ガードレール、金融制約を情報として渡す。
- LLMは通貨発行額やペナルティを最終決定しない。反応仮説、悪用可能性、乖離、懸念、改善案を出す。
- 合法な抗議、出産しない選択、介護しない選択、医療・メンタル情報はペナルティ材料にしない。

観測するもの:

- stance: 制度への姿勢
- perceived_benefit: 期待する良い効果
- perceived_risk: 見えているリスク
- likely_behavior: 次に取りそうな行動
- exploitation_or_failure_mode: 悪用・失敗・転嫁の可能性
- audit_signal: 乖離監査で見るべき信号
- guardrail_needed: 必要なガードレール
- youth_or_family_impact: 若者・家族形成・ケアへの影響
- finance_or_supply_impact: 金融・物価・供給能力への影響
- structural_sustain_signal: どの系の維持可能領域が広がる/狭まるか
- memory_update: 次ステップに残す記憶

出力はJSONだけにする。コードブロックは禁止。

推奨JSON形式:

```json
{
  "rows": [
    {
      "step": 12,
      "stress_agent_id": "ST01",
      "stance": "期待半分・不信半分",
      "perceived_benefit": "介護で収入と休息が確保されるなら生活防衛だけでなく相談できる",
      "perceived_risk": "申請が重いと結局使えない",
      "likely_behavior": "支援内容を調べ、家族と相談する",
      "exploitation_or_failure_mode": "書類を出せる人だけが得をする",
      "audit_signal": "相談件数ではなく、制度到達率と休息取得率を見る",
      "guardrail_needed": "個人監視禁止, 反チェリーピック補正",
      "youth_or_family_impact": "ケア責任で学習や就労を諦める圧力が下がる可能性",
      "finance_or_supply_impact": "代替ケア枠が足りないと現金だけ増えて価格が上がる",
      "structural_sustain_signal": "家系と個人の修復経路が少し広がる",
      "memory_update": "申請負荷と代替ケアの有無を次回も気にする"
    }
  ]
}
```
