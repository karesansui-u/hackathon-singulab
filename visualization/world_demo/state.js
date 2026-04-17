        const SIDEBAR_TAB_PREF_KEY = "world-demo:sidebar-tab";
        const SCENARIO_PREF_KEY_PREFIX = "world-demo:scenario";
        const ROOT_HANDLE_KEY = "root-handle";
        const HANDLE_DB_NAME = "world-demo-handles";
        const HANDLE_STORE_NAME = "handles";
        const DEFAULT_ROOT_URL = "../output/world_demo/major_powers_20year_outlook";
        const VIEW_WIDTH = 2000;
        const VIEW_HEIGHT = 1000;
        const CENTER_LON = 140;

        const MODE_COLORS = {
            none: "#8aa4bf",
            pressure_only: "#5ec4ff",
            gray_zone: "#b388ff",
            proxy: "#ff7b72",
            limited_war: "#0f1115",
        };

        const BAR_COLORS = {
            S: "#66d18f",
            cash: "#5ec4ff",
            support: "#ffb454",
            war: "#ff6c5c",
            horizon: "#8aa4bf",
        };

        const MODE_LABELS_JA = {
            none: "平時",
            pressure_only: "圧力上昇",
            gray_zone: "境界的圧力",
            proxy: "間接衝突",
            limited_war: "限定戦争",
        };

        const STAGE_LABELS_JA = {
            stable: "安定",
            grievance: "不満拡大",
            protest: "抗議",
            mass_protest: "大規模抗議",
            riot: "暴動",
            insurgency: "武装化",
            civil_conflict: "内乱",
        };

        const SCENARIO_NAME_JA = {
            "20-year fracture path": "20年 崩壊シナリオ",
            "20-year managed transition": "20年 管理移行シナリオ",
            "20-year complement path": "20年 補完シナリオ",
        };

        const EVENT_NAME_JA = {
            "Baseline dynamics": "平常推移",
        };

        const EVENT_DESC_JA = {
            "No exogenous event.": "外生イベントなし。",
        };

        const DOMAIN_LABELS_JA = {
            technology_maritime: "技術・海洋",
            maritime_island_chain: "海洋・島嶼線",
            border_himalaya: "国境・ヒマラヤ",
            continental_energy: "大陸・エネルギー",
            nuclear_coercion: "核抑止・威圧",
        };

        const REGION_LABELS_JA = {
            east_asia: "東アジア",
            southeast_asia: "東南アジア",
            south_asia: "南アジア",
            middle_east: "中東",
            eurasia: "ユーラシア",
            europe: "欧州",
            north_america: "北米",
            latin_america: "中南米",
            north_africa: "北アフリカ",
            west_africa: "西アフリカ",
            southern_africa: "南部アフリカ",
            oceania: "オセアニア",
            other: "その他",
        };

        const COUNTRY_LABELS_JA = {
            JPN: "日本",
            USA: "アメリカ",
            CHN: "中国",
            RUS: "ロシア",
            IND: "インド",
            BRA: "ブラジル",
            DEU: "ドイツ",
            FRA: "フランス",
            GBR: "イギリス",
            ITA: "イタリア",
            UKR: "ウクライナ",
            KOR: "韓国",
            TWN: "台湾",
            IDN: "インドネシア",
            AUS: "オーストラリア",
            CAN: "カナダ",
            MEX: "メキシコ",
            TUR: "トルコ",
            IRN: "イラン",
            ISR: "イスラエル",
            SAU: "サウジアラビア",
            ARE: "アラブ首長国連邦",
            QAT: "カタール",
            EGY: "エジプト",
            MAR: "モロッコ",
            NGA: "ナイジェリア",
            ZAF: "南アフリカ",
            NOR: "ノルウェー",
            NLD: "オランダ",
            CHE: "スイス",
            OMN: "オマーン",
            PAK: "パキスタン",
        };

        const DEFAULT_COUNTRY_COORDS = {
            JPN: { lon: 138.0, lat: 36.2 },
            USA: { lon: -98.5, lat: 39.8 },
            CHN: { lon: 104.0, lat: 35.0 },
            RUS: { lon: 97.0, lat: 61.0 },
            IND: { lon: 78.5, lat: 22.8 },
            BRA: { lon: -52.0, lat: -14.2 },
            DEU: { lon: 10.5, lat: 51.0 },
            FRA: { lon: 2.3, lat: 46.2 },
            GBR: { lon: -2.5, lat: 54.0 },
            KOR: { lon: 127.8, lat: 36.4 },
        };

        var state = {
            accessMode: "none",
            rootHandle: null,
            rootUrl: "",
            rootLabel: "同梱デモ",
            rootFiles: new Map(),
            scenarioHandles: new Map(),
            scenarioUrls: new Map(),
            scenarioFilePrefixes: new Map(),
            scenarioMeta: new Map(),
            graph: {
                cooperation: [],
                rivalries: [],
            },
            viewerMeta: {
                turn_duration_months: 1,
                default_scenario: "fracture",
            },
            countryMeta: new Map(),
            scenarioKey: "",
            scenarioName: "",
            turns: [],
            turnIndex: 0,
            rowsByTurn: new Map(),
            aggregateByTurn: new Map(),
            eventsByTurn: new Map(),
            selectedCountry: "JPN",
            mapFocusCountry: null,
            sidebarTab: localStorage.getItem(SIDEBAR_TAB_PREF_KEY) || "chat",
            filterPanelOpen: false,
            hiddenRegions: new Set(),
            hiddenCountries: new Set(),
            playing: false,
            playTimer: null,
            mapView: {
                scale: 1,
                translateX: 0,
                translateY: 0,
                dragging: false,
                pointerId: null,
                downCountryCode: null,
                lastX: 0,
                lastY: 0,
                moved: false,
                suppressClickUntil: 0,
            },
            mapFocusCard: {
                x: 16,
                y: 16,
                dragging: false,
                pointerId: null,
                lastX: 0,
                lastY: 0,
            },
        };

        var stage = document.getElementById("stage");
        var mapViewport = document.getElementById("mapViewport");
        var overlay = document.getElementById("overlay");
        var mapEventLayer = document.getElementById("mapEventLayer");
        var mapFocusCard = document.getElementById("mapFocusCard");
        var emptyState = document.getElementById("emptyState");
        var openButton = document.getElementById("openButton");
        var rootInput = document.getElementById("rootInput");
        var filterToggleButton = document.getElementById("filterToggleButton");
        var filterPanel = document.getElementById("filterPanel");
        var filterResetButton = document.getElementById("filterResetButton");
        var filterCloseButton = document.getElementById("filterCloseButton");
        var regionFilterList = document.getElementById("regionFilterList");
        var countryFilterList = document.getElementById("countryFilterList");
        var regionFilterSummary = document.getElementById("regionFilterSummary");
        var countryFilterSummary = document.getElementById("countryFilterSummary");
        var playButton = document.getElementById("playButton");
        var prevButton = document.getElementById("prevButton");
        var nextButton = document.getElementById("nextButton");
        var turnSlider = document.getElementById("turnSlider");
        var scenarioSelect = document.getElementById("scenarioSelect");
        var rootStatus = document.getElementById("rootStatus");
        var tabButtons = Array.from(document.querySelectorAll(".tab-button"));

        function parseCSV(text) {
            const rows = [];
            let row = [];
            let field = "";
            let inQuotes = false;

            for (let index = 0; index < text.length; index += 1) {
                const char = text[index];
                const next = text[index + 1];

                if (char === "\"") {
                    if (inQuotes && next === "\"") {
                        field += "\"";
                        index += 1;
                    } else {
                        inQuotes = !inQuotes;
                    }
                } else if (char === "," && !inQuotes) {
                    row.push(field);
                    field = "";
                } else if ((char === "\n" || char === "\r") && !inQuotes) {
                    if (char === "\r" && next === "\n") {
                        index += 1;
                    }
                    row.push(field);
                    if (row.length > 1 || row[0] !== "") {
                        rows.push(row);
                    }
                    row = [];
                    field = "";
                } else {
                    field += char;
                }
            }

            if (field || row.length) {
                row.push(field);
                rows.push(row);
            }

            const [header, ...body] = rows;
            return body.map(cols => Object.fromEntries(header.map((key, idx) => [key, cols[idx] ?? ""])));
        }

        function parseJSONL(text) {
            return text
                .split(/\r?\n/)
                .map(line => line.trim())
                .filter(Boolean)
                .map(line => JSON.parse(line));
        }

        function scenarioPrefStorageKey(rootIdentifier) {
            const safeRoot = String(rootIdentifier || "default")
                .replace(/[^a-zA-Z0-9_-]+/g, "_")
                .replace(/^_+|_+$/g, "") || "default";
            return `${SCENARIO_PREF_KEY_PREFIX}:${safeRoot}`;
        }

        function readScenarioPreference(rootIdentifier) {
            return localStorage.getItem(scenarioPrefStorageKey(rootIdentifier));
        }

        function persistScenarioPreference(scenarioKey) {
            const rootIdentifier = state.rootUrl || state.rootLabel || "default";
            localStorage.setItem(scenarioPrefStorageKey(rootIdentifier), scenarioKey);
        }

        function clampMapTranslation(scale, translateX, translateY) {
            const width = stage.clientWidth || 0;
            const height = stage.clientHeight || 0;
            const maxX = Math.max(0, (width * (scale - 1)) / 2);
            const maxY = Math.max(0, (height * (scale - 1)) / 2);
            return {
                translateX: clamp(translateX, -maxX, maxX),
                translateY: clamp(translateY, -maxY, maxY),
            };
        }

        function applyMapTransform() {
            const { scale, translateX, translateY } = state.mapView;
            const clamped = clampMapTranslation(scale, translateX, translateY);
            state.mapView.translateX = clamped.translateX;
            state.mapView.translateY = clamped.translateY;
            mapViewport.style.transform = `translate(${clamped.translateX}px, ${clamped.translateY}px) scale(${scale})`;
            stage.classList.toggle("dragging", Boolean(state.mapView.dragging));
        }

        function clampMapFocusCardPosition(x, y) {
            const stageWidth = stage.clientWidth || 0;
            const stageHeight = stage.clientHeight || 0;
            const cardWidth = mapFocusCard.offsetWidth || 272;
            const cardHeight = mapFocusCard.offsetHeight || 180;
            const margin = 12;
            return {
                x: clamp(x, margin, Math.max(margin, stageWidth - cardWidth - margin)),
                y: clamp(y, margin, Math.max(margin, stageHeight - cardHeight - margin)),
            };
        }

        function applyMapFocusCardPosition() {
            if (mapFocusCard.hidden) {
                return;
            }
            const clamped = clampMapFocusCardPosition(state.mapFocusCard.x, state.mapFocusCard.y);
            state.mapFocusCard.x = clamped.x;
            state.mapFocusCard.y = clamped.y;
            mapFocusCard.style.left = `${clamped.x}px`;
            mapFocusCard.style.top = `${clamped.y}px`;
            mapFocusCard.classList.toggle("dragging", Boolean(state.mapFocusCard.dragging));
        }

        function resetMapView() {
            state.mapView.scale = 1;
            state.mapView.translateX = 0;
            state.mapView.translateY = 0;
            state.mapView.dragging = false;
            state.mapView.pointerId = null;
            state.mapView.downCountryCode = null;
            state.mapView.moved = false;
            applyMapTransform();
        }

        function zoomMapAt(clientX, clientY, scaleMultiplier) {
            const rect = stage.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const pointerX = clientX - centerX;
            const pointerY = clientY - centerY;
            const previousScale = state.mapView.scale;
            const nextScale = clamp(previousScale * scaleMultiplier, 1, 4);
            if (Math.abs(nextScale - previousScale) < 1e-4) {
                return;
            }
            const ratio = nextScale / previousScale;
            state.mapView.translateX += pointerX * (1 - ratio);
            state.mapView.translateY += pointerY * (1 - ratio);
            state.mapView.scale = nextScale;
            applyMapTransform();
        }

        function openHandleDb() {
            return new Promise((resolve, reject) => {
                const request = indexedDB.open(HANDLE_DB_NAME, 1);
                request.onupgradeneeded = () => {
                    request.result.createObjectStore(HANDLE_STORE_NAME);
                };
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        }

        async function saveRootHandle(handle) {
            if (!("indexedDB" in window)) {
                return;
            }
            try {
                const db = await openHandleDb();
                await new Promise((resolve, reject) => {
                    const tx = db.transaction(HANDLE_STORE_NAME, "readwrite");
                    tx.objectStore(HANDLE_STORE_NAME).put(handle, ROOT_HANDLE_KEY);
                    tx.oncomplete = resolve;
                    tx.onerror = () => reject(tx.error);
                });
                db.close();
            } catch (error) {
                console.warn("failed to save root handle", error);
            }
        }

        async function loadSavedRootHandle() {
            if (!("indexedDB" in window)) {
                return null;
            }
            const db = await openHandleDb();
            const result = await new Promise((resolve, reject) => {
                const tx = db.transaction(HANDLE_STORE_NAME, "readonly");
                const request = tx.objectStore(HANDLE_STORE_NAME).get(ROOT_HANDLE_KEY);
                request.onsuccess = () => resolve(request.result ?? null);
                request.onerror = () => reject(request.error);
            });
            db.close();
            return result;
        }

        async function verifyPermission(handle, requestWrite = false) {
            if (!handle || typeof handle.queryPermission !== "function") {
                return false;
            }
            const options = { mode: requestWrite ? "readwrite" : "read" };
            const queried = await handle.queryPermission(options);
            if (queried === "granted") {
                return true;
            }
            if (queried === "prompt" && requestWrite) {
                return (await handle.requestPermission(options)) === "granted";
            }
            return false;
        }

        async function readRequiredFile(directoryHandle, fileName) {
            const handle = await directoryHandle.getFileHandle(fileName);
            return handle.getFile().then(file => file.text());
        }

        async function fetchRequiredText(url) {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Failed to fetch ${url}: ${response.status}`);
            }
            return response.text();
        }

        function wrapLongitude(lon) {
            return ((lon - CENTER_LON + 540) % 360) - 180;
        }

        function setCountryMeta(entries) {
            state.countryMeta = new Map();
            for (const entry of entries || []) {
                if (!entry?.code) {
                    continue;
                }
                const lon = Number(entry.lon);
                const lat = Number(entry.lat);
                state.countryMeta.set(entry.code, entry);
                if (Number.isFinite(lon) && Number.isFinite(lat)) {
                    state.countryMeta.set(entry.code, { ...entry, lon, lat });
                }
            }
        }

        function resolveGeo(code, row = null) {
            const rowLon = Number(row?.lon);
            const rowLat = Number(row?.lat);
            if (Number.isFinite(rowLon) && Number.isFinite(rowLat)) {
                return { lon: rowLon, lat: rowLat };
            }
            const meta = state.countryMeta.get(code);
            const metaLon = Number(meta?.lon);
            const metaLat = Number(meta?.lat);
            if (Number.isFinite(metaLon) && Number.isFinite(metaLat)) {
                return { lon: metaLon, lat: metaLat };
            }
            return DEFAULT_COUNTRY_COORDS[code] || null;
        }

        function project(code, row = null) {
            const geo = resolveGeo(code, row);
            if (!geo) {
                return {
                    x: VIEW_WIDTH / 2,
                    y: VIEW_HEIGHT / 2,
                };
            }
            const wrapped = wrapLongitude(geo.lon);
            return {
                x: ((wrapped + 180) / 360) * VIEW_WIDTH,
                y: ((90 - geo.lat) / 180) * VIEW_HEIGHT,
            };
        }

        function clamp(value, min, max) {
            return Math.max(min, Math.min(max, value));
        }

        function mixColor(a, b, t) {
            const ar = parseInt(a.slice(1, 3), 16);
            const ag = parseInt(a.slice(3, 5), 16);
            const ab = parseInt(a.slice(5, 7), 16);
            const br = parseInt(b.slice(1, 3), 16);
            const bg = parseInt(b.slice(3, 5), 16);
            const bb = parseInt(b.slice(5, 7), 16);
            const r = Math.round(ar + (br - ar) * t).toString(16).padStart(2, "0");
            const g = Math.round(ag + (bg - ag) * t).toString(16).padStart(2, "0");
            const bHex = Math.round(ab + (bb - ab) * t).toString(16).padStart(2, "0");
            return `#${r}${g}${bHex}`;
        }

        function domesticInstabilityScore(row) {
            const domestic = Number(row.domestic_burden || 0);
            const protest = Number(row.protest_pressure || 0);
            const riot = Number(row.riot_pressure || 0);
            const civil = Number(row.civil_conflict_pressure || 0);
            const fragility = clamp(1 - Number(row.S), 0, 1);
            const stageFloor = {
                stable: 0.04,
                grievance: 0.18,
                protest: 0.36,
                mass_protest: 0.54,
                riot: 0.72,
                insurgency: 0.86,
                civil_conflict: 0.97,
            }[row.domestic_stage || "stable"] ?? 0.04;

            const weighted = domestic * 0.40 + protest * 0.16 + riot * 0.20 + civil * 0.24;
            return clamp(
                Math.max(weighted, stageFloor, domestic * 0.92, protest * 0.78, riot * 0.96, civil, fragility * 0.66),
                0,
                1,
            );
        }

        function isStructureCollapse(row) {
            return Number(row.S) < 0.18
                || Number(row.civil_conflict_pressure || 0) > 0.82
                || (
                    (row.domestic_stage || "stable") === "civil_conflict"
                    && Number(row.cash_stability || 0) < 0.28
                );
        }

        function instabilityColor(row) {
            if (isStructureCollapse(row)) {
                return "#15181f";
            }
            const t = domesticInstabilityScore(row);
            if (t < 0.5) {
                return mixColor("#63d98f", "#ffbe55", t / 0.5);
            }
            return mixColor("#ffbe55", "#ff5f57", (t - 0.5) / 0.5);
        }

        function instabilityRadius(row) {
            const base = 11 + domesticInstabilityScore(row) * 18;
            return base + (isStructureCollapse(row) ? 8 : 0);
        }

        function countryLabel(code, fallback = "") {
            const dynamic = state.countryMeta.get(code);
            return dynamic?.name_ja || COUNTRY_LABELS_JA[code] || fallback || code;
        }

        function regionLabel(regionId) {
            return REGION_LABELS_JA[regionId] || regionId || "その他";
        }

        function rowsForTurn(turn) {
            return state.rowsByTurn.get(turn) || new Map();
        }

        function regionIdForCountry(code, row = null) {
            return row?.region_id || state.countryMeta.get(code)?.region_id || "other";
        }

        function isCountryVisible(code, row = null) {
            const regionId = regionIdForCountry(code, row);
            return !state.hiddenRegions.has(regionId) && !state.hiddenCountries.has(code);
        }

        function visibleRowsForTurn(turn) {
            return Array.from(rowsForTurn(turn).values()).filter(row => isCountryVisible(row.code, row));
        }

        function fallbackRowForTurn(turn) {
            const visible = visibleRowsForTurn(turn);
            if (visible.length) {
                return visible[0];
            }
            return Array.from(rowsForTurn(turn).values())[0] || null;
        }

        function ensureSelectedCountryVisible() {
            if (!state.turns.length) {
                state.selectedCountry = "";
                state.mapFocusCountry = null;
                return null;
            }

            const turn = state.turns[state.turnIndex];
            const currentRows = rowsForTurn(turn);
            const selectedRow = state.selectedCountry ? currentRows.get(state.selectedCountry) : null;

            if (selectedRow && isCountryVisible(selectedRow.code, selectedRow)) {
                if (state.mapFocusCountry) {
                    const focusRow = currentRows.get(state.mapFocusCountry);
                    if (!focusRow || !isCountryVisible(state.mapFocusCountry, focusRow)) {
                        state.mapFocusCountry = null;
                    }
                }
                return selectedRow;
            }

            const visibleFallback = visibleRowsForTurn(turn)[0] || null;
            if (visibleFallback) {
                state.selectedCountry = visibleFallback.code;
            } else {
                const anyRow = Array.from(currentRows.values())[0] || null;
                state.selectedCountry = anyRow?.code || "";
            }

            if (state.mapFocusCountry) {
                const focusRow = currentRows.get(state.mapFocusCountry);
                if (!focusRow || !isCountryVisible(state.mapFocusCountry, focusRow)) {
                    state.mapFocusCountry = null;
                }
            }

            return currentRows.get(state.selectedCountry) || null;
        }

        function scenarioCountryEntries() {
            if (!state.turns.length) {
                return Array.from(state.countryMeta.values());
            }

            const firstTurn = state.turns[0];
            const rows = Array.from(rowsForTurn(firstTurn).values());
            if (rows.length) {
                return rows;
            }
            return Array.from(state.countryMeta.values());
        }

        function renderFilterPanel() {
            filterPanel.hidden = !state.filterPanelOpen;
            filterToggleButton.classList.toggle("is-active", state.filterPanelOpen);

            const entries = scenarioCountryEntries()
                .map(entry => ({
                    code: entry.code,
                    name: countryLabel(entry.code, entry.name),
                    regionId: regionIdForCountry(entry.code, entry),
                }))
                .sort((a, b) => {
                    const regionCmp = regionLabel(a.regionId).localeCompare(regionLabel(b.regionId), "ja");
                    if (regionCmp !== 0) {
                        return regionCmp;
                    }
                    return a.name.localeCompare(b.name, "ja");
                });

            if (!entries.length) {
                regionFilterSummary.textContent = "-";
                countryFilterSummary.textContent = "-";
                regionFilterList.innerHTML = `<div class="filter-empty">シナリオを読み込むと地域フィルタが表示されます。</div>`;
                countryFilterList.innerHTML = `<div class="filter-empty">シナリオを読み込むと国フィルタが表示されます。</div>`;
                return;
            }

            const regionCounts = new Map();
            for (const entry of entries) {
                if (!regionCounts.has(entry.regionId)) {
                    regionCounts.set(entry.regionId, { total: 0, visible: 0 });
                }
                const counter = regionCounts.get(entry.regionId);
                counter.total += 1;
                if (isCountryVisible(entry.code, entry)) {
                    counter.visible += 1;
                }
            }

            const visibleRegionCount = Array.from(regionCounts.keys()).filter(regionId => !state.hiddenRegions.has(regionId)).length;
            const visibleCountryCount = entries.filter(entry => isCountryVisible(entry.code, entry)).length;
            regionFilterSummary.textContent = `${visibleRegionCount}/${regionCounts.size} 地域を表示`;
            countryFilterSummary.textContent = `${visibleCountryCount}/${entries.length} か国を表示`;

            const regionEntries = Array.from(regionCounts.entries()).sort((a, b) =>
                regionLabel(a[0]).localeCompare(regionLabel(b[0]), "ja"),
            );

            regionFilterList.innerHTML = regionEntries.map(([regionId, count]) => `
                <label class="filter-option">
                    <input type="checkbox" data-region="${regionId}" ${state.hiddenRegions.has(regionId) ? "" : "checked"}>
                    <div class="filter-option-copy">
                        <strong>
                            <span>${regionLabel(regionId)}</span>
                            <span>${count.visible}/${count.total}</span>
                        </strong>
                        <small>この地域に属する国をまとめて表示・非表示にします。</small>
                    </div>
                </label>
            `).join("");

            countryFilterList.innerHTML = entries.map(entry => {
                const regionHidden = state.hiddenRegions.has(entry.regionId);
                const hidden = state.hiddenCountries.has(entry.code);
                return `
                    <label class="filter-option ${regionHidden ? "region-hidden" : ""}">
                        <input type="checkbox" data-country="${entry.code}" ${hidden ? "" : "checked"} ${regionHidden ? "disabled" : ""}>
                        <div class="filter-option-copy">
                            <strong>
                                <span>${entry.name}</span>
                                <span>${entry.code}</span>
                            </strong>
                            <small>${regionLabel(entry.regionId)}${regionHidden ? " / 地域ごと非表示中" : ""}</small>
                        </div>
                    </label>
                `;
            }).join("");
        }
