        function renderOverlay() {
            if (!state.turns.length) {
                overlay.innerHTML = "";
                return;
            }

            const turn = state.turns[state.turnIndex];
            const rows = visibleRowsForTurn(turn);
            const activeKinds = buildTurnActiveCountryKinds(turn);

            let nodes = "";
            for (const row of rows) {
                const code = row.code;
                const pos = project(code, row);
                const radius = instabilityRadius(row);
                const modeColor = MODE_COLORS[row.likely_mode] || MODE_COLORS.none;
                const ringWidth = 3 + Number(row.war_pressure) * 18;
                const auraWidth = 8 + Number(row.war_pressure) * 42;
                const selected = state.selectedCountry === code ? "selected" : "";
                const activeKind = activeKinds.get(code);
                const activeClass = activeKind ? `event-active event-${activeKind}` : "";
                const warLabel = warBadgeLabel(row);
                const domesticLabel = domesticBadgeLabel(row);
                const instabilityFill = instabilityColor(row);
                const warMarker = renderStatusMarker({
                    label: warLabel,
                    shortLabel: "戦",
                    x: radius + 12,
                    y: -radius + 2,
                    kind: "war",
                    fill: modeColor,
                });
                const domesticMarker = renderStatusMarker({
                    label: domesticLabel,
                    shortLabel: "内",
                    x: radius + 12,
                    y: radius - 2,
                    kind: "domestic",
                    fill: "#ffbe55",
                });

                nodes += `
                    <g class="node-group ${selected} ${activeClass}" data-code="${code}" transform="translate(${pos.x.toFixed(1)} ${pos.y.toFixed(1)})">
                        <circle class="node-aura" r="${(radius + 18).toFixed(1)}" stroke="${modeColor}" stroke-width="${auraWidth.toFixed(1)}"></circle>
                        <circle class="node-ring" r="${(radius + 10).toFixed(1)}" stroke="${modeColor}" stroke-width="${ringWidth.toFixed(1)}"></circle>
                        <circle class="node-hit" r="${(radius + 18).toFixed(1)}"></circle>
                        <circle class="node-core" r="${radius.toFixed(1)}" fill="${instabilityFill}"></circle>
                        <text class="node-label" text-anchor="middle" y="${(-radius - 18).toFixed(1)}">${code}</text>
                        ${warMarker}
                        ${domesticMarker}
                    </g>
                `;
            }

            overlay.innerHTML = nodes;
        }

        function renderSelectedCountry() {
            const codeEl = document.getElementById("countryCode");
            const modeEl = document.getElementById("countryMode");
            const nameEl = document.getElementById("countryName");
            const barsEl = document.getElementById("countryBars");

            if (!state.turns.length) {
                codeEl.textContent = "-";
                modeEl.textContent = "待機";
                nameEl.textContent = "シナリオを読み込むと、国をクリックして詳細を見られます。";
                barsEl.innerHTML = "";
                return;
            }

            const row = ensureSelectedCountryVisible();
            if (!row || !isCountryVisible(row.code, row)) {
                codeEl.textContent = "-";
                modeEl.textContent = "非表示中";
                modeEl.style.color = "#cfd8dc";
                nameEl.textContent = "いまはすべての国が非表示です。表示フィルタから地域か国をオンに戻してください。";
                barsEl.innerHTML = "";
                return;
            }
            state.selectedCountry = row.code;
            codeEl.textContent = row.code;
            modeEl.textContent = `${modeLabel(row.likely_mode)} / ${stageLabel(row.domestic_stage || "stable")}`;
            modeEl.style.color = MODE_COLORS[row.likely_mode] || "#cfd8dc";
            nameEl.textContent = `${countryLabel(row.code, row.name)}。経済安定度 ${format(row.cash_stability)}、外部支援必要度 ${format(row.support_needed)}、戦争圧力 ${format(row.war_pressure)}、国内不安定度 ${format(row.domestic_burden || 0)}。`;

            const barSpec = [
                ["構造持続指数", Number(row.S), BAR_COLORS.S, "その国や地域がどれだけ壊れにくく、持ちこたえやすいかの総合指数です。"],
                ["経済安定度", Number(row.cash_stability), BAR_COLORS.cash, "家計・雇用・企業・政府の支払い余力がどれだけ保たれているかの目安です。"],
                ["外部支援必要度", Number(row.support_needed), BAR_COLORS.support, "外からの食料・エネルギー・資金・外交支援がどれだけ必要かを示します。"],
                ["国内不安定度", Number(row.domestic_burden || 0), "#8e24aa", "内政の揺らぎや統治の傷みがどれだけ積み上がっているかを示します。"],
                ["デモ圧力", Number(row.protest_pressure || 0), "#ffb300", "不満や抗議行動が広がる強さの目安です。"],
                ["対外衝突圧力", Number(row.war_pressure), BAR_COLORS.war, "他国との威圧・衝突・軍事エスカレーションが起きやすい強さを示します。"],
                ["持続見込み", clamp(Number(row.horizon_turns) / 10, 0, 1), BAR_COLORS.horizon, "今の状態のままで、どれくらい持ちこたえられそうかの粗い見通しです。"],
            ];
            barsEl.innerHTML = barSpec.map(([label, value, color, help]) => `
                <div class="bar-row" title="${help || ''}">
                    <span>${label}</span>
                    <div class="bar-track"><div class="bar-fill" style="width:${(value * 100).toFixed(1)}%; background:${color};"></div></div>
                    <strong>${format(value)}</strong>
                </div>
            `).join("");
        }

        function renderCountryList() {
            const listEl = document.getElementById("countryList");
            if (!state.turns.length) {
                listEl.innerHTML = "";
                return;
            }

            const turn = state.turns[state.turnIndex];
            const rows = visibleRowsForTurn(turn)
                .sort((a, b) => Number(b.S) - Number(a.S));

            if (!rows.length) {
                listEl.innerHTML = `<div class="filter-empty">表示対象の国がありません。表示フィルタで地域か国をオンに戻してください。</div>`;
                return;
            }

            listEl.innerHTML = rows.map(row => `
                <div class="list-item ${state.selectedCountry === row.code ? "active" : ""}" data-code="${row.code}">
                    <strong>
                        <span>${row.code}</span>
                        <span>構造持続指数 ${format(row.S)}</span>
                    </strong>
                    <small>持続見込み ${format(row.horizon_turns, 1)} | 経済安定度 ${format(row.cash_stability)} | 国内段階 ${stageLabel(row.domestic_stage || "stable")} | 戦争圧力 ${format(row.war_pressure)} | ${modeLabel(row.likely_mode)}</small>
                </div>
            `).join("");

            listEl.querySelectorAll(".list-item").forEach(item => {
                item.addEventListener("click", () => {
                    state.selectedCountry = item.dataset.code;
                    render();
                });
            });
        }

        function renderChatFeed() {
            const chatEl = document.getElementById("chatFeed");
            if (!state.turns.length) {
                chatEl.innerHTML = "";
                return;
            }

            const startIndex = Math.max(0, state.turnIndex - 2);
            const recentTurns = state.turns.slice(startIndex, state.turnIndex + 1).reverse();
            const messages = [];
            for (const turn of recentTurns) {
                messages.push(...buildTurnMessages(turn));
            }

            if (!messages.length) {
                chatEl.innerHTML = `
                    <article class="feed-item latest">
                        <div class="feed-meta">
                            <span>世界 → 全体</span>
                            <span>${formatElapsed(state.turns[state.turnIndex])}</span>
                        </div>
                        <div class="feed-body">このターンは大きな交渉イベントが少なく、世界チャットは静かです。</div>
                        <div class="feed-note">シナリオデータは読めています。以後のターンで支援・圧力・国内イベントがここに流れます。</div>
                    </article>
                `;
                return;
            }

            chatEl.innerHTML = messages.map((item, index) => `
                <article class="feed-item ${index < 3 ? "latest" : ""}">
                    <div class="feed-meta">
                        <span>${item.from} → ${item.to}</span>
                        <span>${item.time}</span>
                    </div>
                    <div class="feed-body">${item.body}</div>
                    <div class="feed-note">${item.note}</div>
                </article>
            `).join("");
        }

        function renderThoughtFeed() {
            const thoughtEl = document.getElementById("thoughtFeed");
            const summaryEl = document.getElementById("reasoningSummary");
            if (!state.turns.length) {
                summaryEl.innerHTML = `
                    <div class="country-note-head">再生が始まると、この国の推論サマリーがここに出ます。</div>
                    <div class="country-note-meta">
                        <span class="country-note-pill">モード 待機</span>
                        <span class="country-note-pill">国内 安定</span>
                    </div>
                `;
                thoughtEl.innerHTML = "";
                return;
            }

            const turn = state.turns[state.turnIndex];
            const prevTurn = previousTurnValue(turn);
            const row = ensureSelectedCountryVisible();
            if (!row || !isCountryVisible(row.code, row)) {
                summaryEl.innerHTML = `
                    <div class="country-note-head">表示対象の国がありません。</div>
                    <div class="country-note-meta">
                        <span class="country-note-pill">フィルタ確認</span>
                    </div>
                `;
                thoughtEl.innerHTML = "";
                return;
            }
            const prevRow = prevTurn != null ? state.rowsByTurn.get(prevTurn).get(row.code) : null;
            const event = state.eventsByTurn.get(turn) || { conflict_events: [], cooperation_transfers: [], domestic_events: [] };
            const thought = buildCountryThought(row, prevRow, event);
            const narrative = buildCountryNarrative(row);

            summaryEl.innerHTML = `
                <div class="country-note-head">${row.code}: ${narrative.headline}</div>
                <div class="country-note-meta">
                    ${narrative.pills.map(item => `<span class="country-note-pill">${item}</span>`).join("")}
                </div>
            `;

            thoughtEl.innerHTML = `
                <article class="feed-item">
                    <div class="feed-meta">
                        <span>${row.code} 状態メモ</span>
                        <span>${formatElapsed(turn)}</span>
                    </div>
                    <div class="feed-body">${thought.snapshot}</div>
                    <div class="feed-note">${thought.reasoning}</div>
                    <div class="subhead">考慮事項</div>
                    <ul class="thought-list">
                        ${thought.considerations.map(item => `<li>${item}</li>`).join("")}
                    </ul>
                </article>
            `;
        }

        function renderSidebarTabs() {
            const activeTab = ["chat", "ranking", "glossary", "legend"].includes(state.sidebarTab)
                ? state.sidebarTab
                : "chat";
            state.sidebarTab = activeTab;

            const panelMap = {
                chat: document.getElementById("tabPanelChat"),
                ranking: document.getElementById("tabPanelRanking"),
                glossary: document.getElementById("tabPanelGlossary"),
                legend: document.getElementById("tabPanelLegend"),
            };

            tabButtons.forEach(button => {
                const isActive = button.dataset.tab === activeTab;
                button.classList.toggle("active", isActive);
                button.setAttribute("aria-selected", isActive ? "true" : "false");
            });

            Object.entries(panelMap).forEach(([key, panel]) => {
                if (!panel) {
                    return;
                }
                panel.hidden = key !== activeTab;
            });

            localStorage.setItem(SIDEBAR_TAB_PREF_KEY, activeTab);
        }

        function renderHeader() {
            const header = document.getElementById("eventSummary");
            if (!state.turns.length) {
                return;
            }

            const turn = state.turns[state.turnIndex];
            const event = state.eventsByTurn.get(turn);
            const aggregate = state.aggregateByTurn.get(turn);
            const timeLabel = formatElapsed(turn);

            header.innerHTML = `
                <h1 style="font-size: 16px;">${scenarioLabel(state.scenarioName)}</h1>
                <p>${eventNameLabel(event.name)}</p>
            `;

            document.getElementById("turnValue").textContent = `${turn}/${state.turns.length}`;
            document.getElementById("avgSValue").textContent = format(aggregate.avg_S);
            document.getElementById("avgCashValue").textContent = format(aggregate.avg_cash_stability);
            document.getElementById("warBurdenValue").textContent = format(aggregate.avg_war_burden);
            document.getElementById("eventCountValue").textContent = `戦${aggregate.war_events_count} / 内${aggregate.domestic_events_count || 0}`;
        }

        function render() {
            renderOverlay();
            renderMapEventPopups();
            renderMapFocusCard();
            renderHeader();
            renderSelectedCountry();
            renderChatFeed();
            renderThoughtFeed();
            renderCountryList();
            renderSidebarTabs();
            renderFilterPanel();
            emptyState.style.display = state.turns.length ? "none" : "grid";
            turnSlider.value = state.turns.length ? String(state.turns[state.turnIndex]) : "1";
        }
