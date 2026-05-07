# 制度設計シミュレーション デモ

GitHub Pages公開用の静的サイトです。

- Demo URL: `https://karesansui-u.github.io/hackathon-singulab/visualization/future_emotion_map.html`
- Main UI: `visualization/future_emotion_map.html`
- Studio mock: `visualization/simulation_studio_mock.html`
- Presentation: `presentation/`
- 実行結果データ: `data/runs/no_intervention_71steps_panel48/`, `data/runs/structure_intervention_100years_panel48_midprompt/`, `data/runs/policy_search_no_sustain_71steps_panel48/`, `data/runs/policy_search_with_sustain_71steps_panel48/`, `data/runs/policy_search_with_sustain_hope_family_71steps_panel48/`, `data/runs/birth_grant_only_83steps_panel48/`, `data/runs/structure_birth_grant_package_83steps_panel48/`, `data/runs/structure_hope_family_package_83steps_panel48/`
- Domain data: `domain_packs/agi_youth_japan/data/`

Source files live outside this directory. Rebuild this folder with:

```bash
python3 scripts/build_pages_site.py
```
