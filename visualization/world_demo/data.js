        function modeLabel(mode) {
            return MODE_LABELS_JA[mode] || mode;
        }

        function stageLabel(stage) {
            return STAGE_LABELS_JA[stage] || stage;
        }

        function scenarioLabel(name) {
            return SCENARIO_NAME_JA[name] || name;
        }

        function eventNameLabel(name) {
            return EVENT_NAME_JA[name] || name;
        }

        function eventDescriptionLabel(text) {
            return EVENT_DESC_JA[text] || text;
        }

        function domainLabel(domain) {
            return DOMAIN_LABELS_JA[domain] || domain;
        }

        function format(value, digits = 2) {
            return Number(value).toFixed(digits);
        }

        function formatElapsed(turn) {
            const months = Number(turn) * Number(state.viewerMeta.turn_duration_months || 1);
            if (!Number.isFinite(months) || months <= 0) {
                return "現時点";
            }
            if (months < 12) {
                return `${months}か月後`;
            }
            const years = Math.floor(months / 12);
            const remMonths = months % 12;
            if (remMonths === 0) {
                return `${years}年後`;
            }
            return `${years}年${remMonths}か月後`;
        }

        function previousTurnValue(turn) {
            const index = state.turns.indexOf(turn);
            if (index <= 0) {
                return null;
            }
            return state.turns[index - 1];
        }

        function topChangesForTurn(turn) {
            const prevTurn = previousTurnValue(turn);
            if (prevTurn == null) {
                return { rising: [], falling: [] };
            }
            const currentRows = Array.from(state.rowsByTurn.get(turn).values());
            const previousRows = state.rowsByTurn.get(prevTurn);
            const deltas = [];
            for (const row of currentRows) {
                const prev = previousRows.get(row.code);
                if (!prev) {
                    continue;
                }
                deltas.push({
                    code: row.code,
                    delta: Number(row.S) - Number(prev.S),
                });
            }
            deltas.sort((a, b) => b.delta - a.delta);
            return {
                rising: deltas.slice(0, 3),
                falling: deltas.slice(-3),
            };
        }

        function modeReasoning(row) {
            if (row.likely_mode === "gray_zone") {
                return "生存圧力と対立関係が境界的圧力の閾値を超え、直接戦争未満の威圧行動が立ち上がっています。";
            }
            if (row.likely_mode === "proxy") {
                return "抑止は効いているものの、第三者や周辺経由で圧力をかける誘因がかなり強い状態です。";
            }
            if (row.likely_mode === "limited_war") {
                return "抑止を織り込んでも限定戦争リスクがかなり高く、構造持続を直接削る局面です。";
            }
            if (row.likely_mode === "pressure_only") {
                return "圧力は高まっていますが、このターンではイベント発火までは届いていません。";
            }
            return "このターンでは強い強制イベントはなく、内部状態の調整が中心です。";
        }

        function warBadgeLabel(row) {
            const mode = row.likely_mode || "none";
            if (mode === "limited_war") {
                return "限定戦争";
            }
            if (mode === "proxy") {
                return "間接衝突";
            }
            if (mode === "gray_zone") {
                return "境界的圧力";
            }
            return "";
        }

        function domesticBadgeLabel(row) {
            const stage = row.domestic_stage || "stable";
            if (stage === "civil_conflict") {
                return "内乱";
            }
            if (stage === "insurgency") {
                return "武装化";
            }
            if (stage === "riot") {
                return "暴動";
            }
            return "";
        }

        function renderStatusMarker({ label, shortLabel, x, y, kind, fill }) {
            if (!label) {
                return "";
            }
            return `
                <g class="status-marker ${kind}" transform="translate(${x.toFixed(1)} ${y.toFixed(1)})">
                    <title>${label}</title>
                    <circle cx="0" cy="0" r="12" fill="${fill}"></circle>
                    <text x="0" y="4" text-anchor="middle">${shortLabel}</text>
                </g>
            `;
        }

        function eventKindPriority(kind) {
            return {
                conflict: 3,
                domestic: 2,
                cooperation: 1,
            }[kind] || 0;
        }

        function registerActiveCountry(activeKinds, code, kind) {
            if (!code) {
                return;
            }
            const current = activeKinds.get(code);
            if (!current || eventKindPriority(kind) > eventKindPriority(current)) {
                activeKinds.set(code, kind);
            }
        }

        function buildTurnActiveCountryKinds(turn) {
            const currentRows = rowsForTurn(turn);
            const event = state.eventsByTurn.get(turn) || { conflict_events: [], cooperation_transfers: [], domestic_events: [] };
            const activeKinds = new Map();

            for (const item of event.conflict_events || []) {
                if (isCountryVisible(item.actor, currentRows.get(item.actor))) {
                    registerActiveCountry(activeKinds, item.actor, "conflict");
                }
                if (isCountryVisible(item.target, currentRows.get(item.target))) {
                    registerActiveCountry(activeKinds, item.target, "conflict");
                }
            }

            for (const item of event.domestic_events || []) {
                if (isCountryVisible(item.country, currentRows.get(item.country))) {
                    registerActiveCountry(activeKinds, item.country, "domestic");
                }
            }

            for (const item of event.cooperation_transfers || []) {
                if (isCountryVisible(item.donor, currentRows.get(item.donor))) {
                    registerActiveCountry(activeKinds, item.donor, "cooperation");
                }
                if (isCountryVisible(item.target, currentRows.get(item.target))) {
                    registerActiveCountry(activeKinds, item.target, "cooperation");
                }
            }

            return activeKinds;
        }

        function renderMapFocusCard() {
            if (!state.turns.length) {
                mapFocusCard.hidden = true;
                mapFocusCard.innerHTML = "";
                return;
            }

            const turn = state.turns[state.turnIndex];
            const rows = rowsForTurn(turn);
            const focusRow = state.mapFocusCountry ? rows.get(state.mapFocusCountry) : null;
            if (!rows.size || !state.mapFocusCountry || !focusRow || !isCountryVisible(state.mapFocusCountry, focusRow)) {
                mapFocusCard.hidden = true;
                mapFocusCard.innerHTML = "";
                return;
            }

            const code = state.mapFocusCountry;
            const row = focusRow;
            const warLabel = warBadgeLabel(row);
            const domesticLabel = domesticBadgeLabel(row);
            const pills = [];

            if (warLabel) {
                pills.push(`<span class="map-focus-pill is-war">${warLabel}</span>`);
            }
            if (domesticLabel) {
                pills.push(`<span class="map-focus-pill is-domestic">${domesticLabel}</span>`);
            }

            pills.push(`<span class="map-focus-pill">${modeLabel(row.likely_mode)}</span>`);
            pills.push(`<span class="map-focus-pill">${stageLabel(row.domestic_stage || "stable")}</span>`);

            mapFocusCard.hidden = false;
            mapFocusCard.innerHTML = `
                <div class="map-focus-kicker">地図上の詳細</div>
                <div class="map-focus-head">
                    <div class="map-focus-title">
                        <strong>${countryLabel(code, row.name)}</strong>
                        <span>${code} / ${formatElapsed(turn)}</span>
                    </div>
                </div>
                <div class="map-focus-pills">
                    ${pills.join("")}
                </div>
                <div class="map-focus-stats">
                    <div class="map-focus-stat">
                        <span>構造持続指数</span>
                        <strong>${format(row.S)}</strong>
                    </div>
                    <div class="map-focus-stat">
                        <span>経済安定度</span>
                        <strong>${format(row.cash_stability)}</strong>
                    </div>
                    <div class="map-focus-stat">
                        <span>外部支援必要度</span>
                        <strong>${format(row.support_needed)}</strong>
                    </div>
                    <div class="map-focus-stat">
                        <span>持続見込み</span>
                        <strong>${format(row.horizon_turns, 1)}</strong>
                    </div>
                </div>
                <div class="map-focus-note">
                    地図の空白をクリックすると閉じます。円の色と大きさは国内不安定化の強さです。
                </div>
            `;
            applyMapFocusCardPosition();
        }

        function renderMapEventPopups() {
            if (!state.turns.length) {
                mapEventLayer.innerHTML = "";
                return;
            }
            const turn = state.turns[state.turnIndex];
            const currentRows = rowsForTurn(turn);
            const event = state.eventsByTurn.get(turn) || { conflict_events: [], cooperation_transfers: [], domestic_events: [] };
            const popups = [];
            let order = 1;

            for (const item of (event.conflict_events || []).slice(0, 3)) {
                const actorVisible = isCountryVisible(item.actor, currentRows.get(item.actor));
                const targetVisible = isCountryVisible(item.target, currentRows.get(item.target));
                if (!actorVisible && !targetVisible) {
                    continue;
                }
                popups.push(`
                    <article class="map-popup conflict">
                        <div class="map-popup-order">${order}</div>
                        <div class="map-popup-copy">
                            <div class="map-popup-kicker">対外イベント</div>
                            <div class="map-popup-title">${countryLabel(item.actor, item.actor)} → ${countryLabel(item.target, item.target)}</div>
                            <div class="map-popup-body">${modeLabel(item.mode)} / 強度 ${Number(item.intensity).toFixed(2)}</div>
                        </div>
                    </article>
                `);
                order += 1;
            }

            for (const item of (event.domestic_events || []).slice(0, 3)) {
                if (!isCountryVisible(item.country, currentRows.get(item.country))) {
                    continue;
                }
                popups.push(`
                    <article class="map-popup domestic">
                        <div class="map-popup-order">${order}</div>
                        <div class="map-popup-copy">
                            <div class="map-popup-kicker">国内イベント</div>
                            <div class="map-popup-title">${countryLabel(item.country, item.country)} / ${stageLabel(item.to_stage)}</div>
                            <div class="map-popup-body">デモ圧力 ${format(item.protest_pressure)} / 暴動圧力 ${format(item.riot_pressure)}</div>
                        </div>
                    </article>
                `);
                order += 1;
            }

            for (const item of (event.cooperation_transfers || []).slice(0, 2)) {
                const donorVisible = isCountryVisible(item.donor, currentRows.get(item.donor));
                const targetVisible = isCountryVisible(item.target, currentRows.get(item.target));
                if (!donorVisible && !targetVisible) {
                    continue;
                }
                popups.push(`
                    <article class="map-popup cooperation">
                        <div class="map-popup-order">${order}</div>
                        <div class="map-popup-copy">
                            <div class="map-popup-kicker">支援イベント</div>
                            <div class="map-popup-title">${countryLabel(item.donor, item.donor)} → ${countryLabel(item.target, item.target)}</div>
                            <div class="map-popup-body">支援量 ${Number(item.amount).toFixed(4)}</div>
                        </div>
                    </article>
                `);
                order += 1;
            }

            mapEventLayer.innerHTML = popups.join("");
        }

        function buildTurnMessages(turn) {
            const currentRows = Array.from(rowsForTurn(turn).values())
                .sort((a, b) => Number(b.population_weight) - Number(a.population_weight));
            const currentRowsMap = rowsForTurn(turn);
            const aggregate = state.aggregateByTurn.get(turn);
            const event = state.eventsByTurn.get(turn) || { conflict_events: [], cooperation_transfers: [], domestic_events: [], name: "Baseline dynamics", description: "No exogenous event." };
            const { rising, falling } = topChangesForTurn(turn);
            const risingText = rising.length
                ? rising.map(item => `${item.code} ${item.delta >= 0 ? "+" : ""}${item.delta.toFixed(2)}`).join(", ")
                : "なし";
            const fallingText = falling.length
                ? falling.map(item => `${item.code} ${item.delta >= 0 ? "+" : ""}${item.delta.toFixed(2)}`).join(", ")
                : "なし";

            const messages = [
                {
                    type: "world",
                    from: "世界",
                    to: "全体",
                    time: formatElapsed(turn),
                    body: `［${scenarioLabel(state.scenarioName)}］${eventNameLabel(event.name)}。平均構造持続指数=${format(aggregate.avg_S, 3)}、平均経済安定度=${format(aggregate.avg_cash_stability, 3)}、戦争負荷=${format(aggregate.avg_war_burden, 3)}、平均国内不安定度=${format(aggregate.avg_domestic_burden || 0, 3)}、平均デモ圧力=${format(aggregate.avg_protest_pressure || 0, 3)}。上昇: ${risingText}。低下: ${fallingText}。`,
                    note: "世界レベルの変化をまとめた要約です。",
                },
            ];

            for (const item of event.cooperation_transfers || []) {
                const donorVisible = isCountryVisible(item.donor, currentRowsMap.get(item.donor));
                const targetVisible = isCountryVisible(item.target, currentRowsMap.get(item.target));
                if (!donorVisible && !targetVisible) {
                    continue;
                }
                messages.push({
                    type: "cooperation",
                    from: countryLabel(item.donor, item.donor),
                    to: countryLabel(item.target, item.target),
                    time: formatElapsed(turn),
                    body: `越境支援ルートを開設。支援量 ${Number(item.amount).toFixed(4)}。分配能力と同盟支援の補強を狙っています。`,
                    note: "越境レジリエンス投資の要約です。",
                });
            }

            for (const item of event.conflict_events || []) {
                const actorVisible = isCountryVisible(item.actor, currentRowsMap.get(item.actor));
                const targetVisible = isCountryVisible(item.target, currentRowsMap.get(item.target));
                if (!actorVisible && !targetVisible) {
                    continue;
                }
                messages.push({
                    type: item.mode,
                    from: countryLabel(item.actor, item.actor),
                    to: countryLabel(item.target, item.target),
                    time: formatElapsed(turn),
                    body: `${modeLabel(item.mode)}圧力が ${domainLabel(item.domain)} で発火。強度 ${Number(item.intensity).toFixed(2)}。対象国の戦争負荷と脆弱性を押し上げます。`,
                    note: "生存圧力に押し上げられた対外圧力イベントです。",
                });
            }

            for (const item of event.domestic_events || []) {
                if (!isCountryVisible(item.country, currentRowsMap.get(item.country))) {
                    continue;
                }
                messages.push({
                    type: "domestic",
                    from: countryLabel(item.country, item.country),
                    to: "国内",
                    time: formatElapsed(turn),
                    body: `${stageLabel(item.from_stage)} → ${stageLabel(item.to_stage)}。デモ圧力 ${format(item.protest_pressure)}、暴動圧力 ${format(item.riot_pressure)}、内乱圧力 ${format(item.civil_conflict_pressure)}。`,
                    note: "国内不安定化イベントです。",
                });
            }

            return messages;
        }

        function buildCountryThought(row, prevRow, event) {
            const considerations = [];
            const deltaS = prevRow ? Number(row.S) - Number(prevRow.S) : 0;
            const deltaCash = prevRow ? Number(row.cash_stability) - Number(prevRow.cash_stability) : 0;

            if (Number(row.support_needed) > 0.25) {
                considerations.push(`外部支援必要度が ${format(row.support_needed)} まで上がっていて、外部支援なしでは持続見込み ${format(row.horizon_turns, 1)} が短いです。`);
            }
            if (Number(row.war_pressure) > 0.30) {
                considerations.push(`戦争圧力が ${format(row.war_pressure)} と高く、対外エスカレーションを前提に姿勢を調整する必要があります。`);
            }
            if (Number(row.cash_stability) < 0.60) {
                considerations.push(`経済安定度が ${format(row.cash_stability)} まで落ちていて、短期の生活・制度安定を崩しやすい状態です。`);
            }
            if ((row.domestic_stage || "stable") !== "stable") {
                considerations.push(`国内段階は ${stageLabel(row.domestic_stage || "stable")} で、国内不安定度 ${format(row.domestic_burden)} が残っています。`);
            }
            if (Number(row.protest_pressure || 0) > 0.52) {
                considerations.push(`デモ圧力が ${format(row.protest_pressure)} と高く、デモや大規模デモの持続を想定した対応が必要です。`);
            }
            if (Number(row.riot_pressure || 0) > 0.50) {
                considerations.push(`暴動圧力が ${format(row.riot_pressure)} に達していて、国内治安の破綻が対外姿勢にも波及しかねません。`);
            }
            if (Number(row.civil_conflict_pressure || 0) > 0.48) {
                considerations.push(`内乱圧力が ${format(row.civil_conflict_pressure)} と高く、内乱化を避ける再分配か鎮静化が急務です。`);
            }
            if (Number(row.labor_displacement) > 0.20) {
                considerations.push(`労働代替が ${format(row.labor_displacement)} と高く、AI 起因の雇用代替が社会の結束を削り始めています。`);
            }
            if (deltaS < -0.015) {
                considerations.push(`前ターン比で構造持続指数が ${deltaS.toFixed(2)} 低下していて、今は防衛的な再均衡が優先です。`);
            } else if (deltaS > 0.015) {
                considerations.push(`前ターン比で構造持続指数が +${deltaS.toFixed(2)} 改善していて、この改善を次ターンでも固定化する余地があります。`);
            }
            if (deltaCash < -0.02) {
                considerations.push(`経済安定度も ${deltaCash.toFixed(2)} 変化していて、分配か外貨調達のどちらかを急がないと不安定化します。`);
            }

            const directConflict = (event.conflict_events || []).find(item => item.actor === row.code || item.target === row.code);
            if (directConflict) {
                if (directConflict.actor === row.code) {
                    considerations.push(`このターンは ${countryLabel(directConflict.target, directConflict.target)} に対する ${modeLabel(directConflict.mode)}イベントの当事者で、外部化による自国維持を選び始めています。`);
                } else {
                    considerations.push(`このターンは ${countryLabel(directConflict.actor, directConflict.actor)} から ${modeLabel(directConflict.mode)}圧力を受けていて、抑止と同盟支援の再計算が必要です。`);
                }
            }

            const directTransfer = (event.cooperation_transfers || []).find(item => item.donor === row.code || item.target === row.code);
            if (directTransfer) {
                if (directTransfer.donor === row.code) {
                    considerations.push(`このターンは ${countryLabel(directTransfer.target, directTransfer.target)} への支援供与側で、自国の余剰をレジリエンス投資に回しています。`);
                } else {
                    considerations.push(`このターンは ${countryLabel(directTransfer.donor, directTransfer.donor)} から支援を受けていて、見込期間改善の余地があります。`);
                }
            }

            const directDomestic = (event.domestic_events || []).find(item => item.country === row.code);
            if (directDomestic) {
                considerations.push(`このターンは ${stageLabel(directDomestic.from_stage)} から ${stageLabel(directDomestic.to_stage)} へ国内段階が動き、内政対応が安全保障と同じくらい重要になっています。`);
            }

            if (!considerations.length) {
                considerations.push("このターンは大きな直接イベントがなく、内部バランスの維持と次の衝撃への備えが中心です。");
            }

            return {
                snapshot: `構造持続指数=${format(row.S)}、持続見込み=${format(row.horizon_turns, 1)}、経済安定度=${format(row.cash_stability)}、外部支援必要度=${format(row.support_needed)}、国内段階=${stageLabel(row.domestic_stage)}、デモ圧力=${format(row.protest_pressure || 0)}、戦争圧力=${format(row.war_pressure)}、モード=${modeLabel(row.likely_mode)}。`,
                reasoning: modeReasoning(row),
                considerations,
            };
        }

        function buildCountryNarrative(row) {
            const headline =
                Number(row.civil_conflict_pressure || 0) > 0.48 ? "国内の断裂リスクがかなり高い状態です。" :
                Number(row.riot_pressure || 0) > 0.50 ? "暴動化の圧力が強く、内政対応が急務です。" :
                Number(row.war_pressure) > 0.35 ? "対外圧力が強く、安全保障リスクが前面に出ています。" :
                Number(row.support_needed) > 0.25 ? "外部支援への依存が強まりつつあります。" :
                Number(row.S) > 0.52 ? "構造持続はまだ比較的安定しています。" :
                "全体ストレスがじわじわ積み上がっています。";

            return {
                headline,
                pills: [
                    `モード ${modeLabel(row.likely_mode)}`,
                    `国内 ${stageLabel(row.domestic_stage || "stable")}`,
                    `構造持続指数 ${format(row.S)}`,
                ],
            };
        }

        function setRootLabel(label) {
            state.rootLabel = label;
            rootStatus.textContent = label;
        }

        function normalizeScenarioEntries(manifest) {
            const entries = manifest?.scenarios || [];
            return entries.map(entry => {
                if (typeof entry === "string") {
                    return { key: entry, name: scenarioLabel(entry) };
                }
                return {
                    key: entry.key,
                    name: scenarioLabel(entry.name || entry.key),
                };
            });
        }

        function applyViewerMeta(manifest) {
            state.viewerMeta = {
                turn_duration_months: Number(manifest?.viewer?.turn_duration_months ?? 1),
                default_scenario: manifest?.viewer?.default_scenario || "fracture",
            };
            setCountryMeta(manifest?.countries || []);
            state.graph = {
                cooperation: manifest?.graph?.cooperation || [],
                rivalries: manifest?.graph?.rivalries || [],
            };
        }

        async function fileExists(directoryHandle, fileName) {
            try {
                await directoryHandle.getFileHandle(fileName);
                return true;
            } catch (error) {
                return false;
            }
        }

        async function readManifestFromHandle(rootHandle) {
            try {
                const manifestText = await readRequiredFile(rootHandle, "manifest.json");
                return JSON.parse(manifestText);
            } catch (error) {
                return null;
            }
        }

        function buildFileMap(files) {
            const entries = Array.from(files || []);
            const rootName = entries[0]?.webkitRelativePath?.split("/")[0] || "selected-root";
            const fileMap = new Map();

            for (const file of entries) {
                const relativePath = file.webkitRelativePath || file.name;
                const segments = relativePath.split("/").filter(Boolean);
                const normalized = segments.length > 1 ? segments.slice(1).join("/") : segments[0];
                if (normalized) {
                    fileMap.set(normalized, file);
                }
            }

            return { rootName, fileMap };
        }

        async function readRequiredMappedFile(fileMap, relativePath) {
            const file = fileMap.get(relativePath);
            if (!file) {
                throw new Error(`missing required file: ${relativePath}`);
            }
            return file.text();
        }

        async function readManifestFromFiles(fileMap) {
            try {
                const manifestText = await readRequiredMappedFile(fileMap, "manifest.json");
                return JSON.parse(manifestText);
            } catch (error) {
                return null;
            }
        }

        function discoverScenarioFiles(fileMap, manifest, rootName) {
            const scenarios = [];
            const manifestEntries = normalizeScenarioEntries(manifest);

            if (manifestEntries.length) {
                for (const entry of manifestEntries) {
                    if (fileMap.has(`${entry.key}/turns.csv`)) {
                        scenarios.push({ ...entry, prefix: `${entry.key}/` });
                    }
                }
            }

            if (scenarios.length) {
                return scenarios;
            }

            if (fileMap.has("turns.csv")) {
                return [{ key: rootName, name: rootName, prefix: "" }];
            }

            const prefixes = new Set();
            for (const path of fileMap.keys()) {
                const match = path.match(/^([^/]+)\/turns\.csv$/);
                if (match) {
                    prefixes.add(match[1]);
                }
            }

            return Array.from(prefixes)
                .sort((a, b) => a.localeCompare(b))
                .map(prefix => ({ key: prefix, name: prefix, prefix: `${prefix}/` }));
        }

        async function discoverScenarioHandles(rootHandle, manifest) {
            const scenarios = [];
            const manifestEntries = normalizeScenarioEntries(manifest);

            if (manifestEntries.length) {
                for (const entry of manifestEntries) {
                    try {
                        const scenarioHandle = await rootHandle.getDirectoryHandle(entry.key);
                        if (await fileExists(scenarioHandle, "turns.csv")) {
                            scenarios.push({ ...entry, handle: scenarioHandle });
                        }
                    } catch (error) {
                        console.warn("scenario missing from root", entry.key, error);
                    }
                }
            }

            if (scenarios.length) {
                return scenarios;
            }

            if (await fileExists(rootHandle, "turns.csv")) {
                return [{ key: rootHandle.name, name: rootHandle.name, handle: rootHandle }];
            }

            for await (const [name, handle] of rootHandle.entries()) {
                if (handle.kind !== "directory") {
                    continue;
                }
                if (await fileExists(handle, "turns.csv")) {
                    scenarios.push({ key: name, name, handle });
                }
            }
            return scenarios;
        }

        function populateScenarioSelect(entries) {
            state.scenarioMeta = new Map(entries.map(entry => [entry.key, entry]));
            scenarioSelect.innerHTML = entries
                .map(entry => `<option value="${entry.key}">${entry.name}</option>`)
                .join("");
            scenarioSelect.disabled = !entries.length;
        }

        async function loadScenarioFromFiles(scenarioKey) {
            const prefix = state.scenarioFilePrefixes.get(scenarioKey);
            if (prefix == null) {
                return;
            }
            const fileMap = state.rootFiles;
            const [turnsText, aggregateText, eventsText] = await Promise.all([
                readRequiredMappedFile(fileMap, `${prefix}turns.csv`),
                readRequiredMappedFile(fileMap, `${prefix}aggregate.csv`),
                readRequiredMappedFile(fileMap, `${prefix}events.jsonl`),
            ]);

            ingestScenarioData(
                parseCSV(turnsText),
                parseCSV(aggregateText),
                parseJSONL(eventsText),
                scenarioKey,
                state.scenarioMeta.get(scenarioKey)?.name || scenarioKey,
            );
        }

        function resetPlaybackUi() {
            turnSlider.min = "1";
            turnSlider.max = "1";
            turnSlider.value = "1";
            turnSlider.disabled = true;
            playButton.disabled = true;
            prevButton.disabled = true;
            nextButton.disabled = true;
            document.getElementById("turnValue").textContent = "-";
            document.getElementById("avgSValue").textContent = "-";
            document.getElementById("avgCashValue").textContent = "-";
            document.getElementById("warBurdenValue").textContent = "-";
            document.getElementById("eventCountValue").textContent = "-";
        }
