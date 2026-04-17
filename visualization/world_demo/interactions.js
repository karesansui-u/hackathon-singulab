        function setTurnFromValue(value) {
            const turn = Number(value);
            const index = state.turns.indexOf(turn);
            if (index >= 0) {
                state.turnIndex = index;
                render();
            }
        }

        function stopPlayback() {
            state.playing = false;
            if (state.playTimer) {
                window.clearInterval(state.playTimer);
                state.playTimer = null;
            }
            playButton.textContent = "再生";
        }

        function startPlayback() {
            if (!state.turns.length) {
                return;
            }
            stopPlayback();
            state.playing = true;
            playButton.textContent = "停止";
            state.playTimer = window.setInterval(() => {
                if (state.turnIndex >= state.turns.length - 1) {
                    state.turnIndex = 0;
                } else {
                    state.turnIndex += 1;
                }
                render();
            }, 1400);
        }

        function ingestScenarioData(turnsRows, aggregateRows, eventsRows, scenarioKey, scenarioName) {
            state.scenarioKey = scenarioKey;
            state.scenarioName = scenarioName;
            state.turns = Array.from(new Set(turnsRows.map(row => Number(row.turn)))).sort((a, b) => a - b);
            state.rowsByTurn = new Map();
            state.aggregateByTurn = new Map();
            state.eventsByTurn = new Map();

            for (const row of turnsRows) {
                const turn = Number(row.turn);
                if (!state.rowsByTurn.has(turn)) {
                    state.rowsByTurn.set(turn, new Map());
                }
                state.rowsByTurn.get(turn).set(row.code, row);
            }

            for (const row of aggregateRows) {
                state.aggregateByTurn.set(Number(row.turn), row);
            }

            for (const row of eventsRows) {
                state.eventsByTurn.set(Number(row.turn), row);
            }

            if (!state.countryMeta.size) {
                const countryEntries = [];
                const seen = new Set();
                for (const row of turnsRows) {
                    if (seen.has(row.code)) {
                        continue;
                    }
                    seen.add(row.code);
                    countryEntries.push({
                        code: row.code,
                        name: row.name,
                        name_ja: row.name_ja || row.name,
                        region_id: row.region_id,
                        lon: Number(row.lon),
                        lat: Number(row.lat),
                    });
                }
                setCountryMeta(countryEntries);
            }

            state.turnIndex = 0;
            state.selectedCountry = state.rowsByTurn.get(state.turns[0])?.has("JPN")
                ? "JPN"
                : turnsRows[0].code;

            stopPlayback();
            turnSlider.min = String(state.turns[0]);
            turnSlider.max = String(state.turns[state.turns.length - 1]);
            turnSlider.disabled = false;
            playButton.disabled = false;
            prevButton.disabled = false;
            nextButton.disabled = false;
            scenarioSelect.disabled = false;
            persistScenarioPreference(scenarioKey);
            resetMapView();
            render();
        }

        async function loadScenarioFromHandle(scenarioKey) {
            const directoryHandle = state.scenarioHandles.get(scenarioKey);
            if (!directoryHandle) {
                return;
            }
            const [turnsText, aggregateText, eventsText] = await Promise.all([
                readRequiredFile(directoryHandle, "turns.csv"),
                readRequiredFile(directoryHandle, "aggregate.csv"),
                readRequiredFile(directoryHandle, "events.jsonl"),
            ]);

            const turnsRows = parseCSV(turnsText);
            const aggregateRows = parseCSV(aggregateText);
            const eventsRows = parseJSONL(eventsText);

            ingestScenarioData(
                turnsRows,
                aggregateRows,
                eventsRows,
                scenarioKey,
                turnsRows[0]?.scenario_name || state.scenarioMeta.get(scenarioKey)?.name || directoryHandle.name,
            );
        }

        async function loadScenarioFromUrl(scenarioKey) {
            const baseUrl = state.scenarioUrls.get(scenarioKey);
            if (!baseUrl) {
                return;
            }
            const [turnsText, aggregateText, eventsText] = await Promise.all([
                fetchRequiredText(`${baseUrl}/turns.csv`),
                fetchRequiredText(`${baseUrl}/aggregate.csv`),
                fetchRequiredText(`${baseUrl}/events.jsonl`),
            ]);

            ingestScenarioData(
                parseCSV(turnsText),
                parseCSV(aggregateText),
                parseJSONL(eventsText),
                scenarioKey,
                state.scenarioMeta.get(scenarioKey)?.name || scenarioKey,
            );
        }

        async function connectRootHandle(rootHandle, options = {}) {
            const { persist = true, preferredScenario = null } = options;
            const manifest = await readManifestFromHandle(rootHandle);
            const scenarioEntries = await discoverScenarioHandles(rootHandle, manifest);
            if (!scenarioEntries.length) {
                throw new Error("選択したルート配下にシナリオのディレクトリが見つかりません。");
            }

            state.accessMode = "fs-root";
            state.rootHandle = rootHandle;
            state.rootUrl = "";
            state.rootFiles = new Map();
            state.scenarioHandles = new Map(scenarioEntries.map(entry => [entry.key, entry.handle]));
            state.scenarioUrls = new Map();
            state.scenarioFilePrefixes = new Map();
            applyViewerMeta(manifest);
            populateScenarioSelect(scenarioEntries);
            setRootLabel(rootHandle.name);

            if (persist) {
                await saveRootHandle(rootHandle);
            }

            const preferred =
                preferredScenario ||
                readScenarioPreference(rootHandle.name) ||
                state.viewerMeta.default_scenario ||
                scenarioEntries[0].key;
            const selectedKey = state.scenarioHandles.has(preferred) ? preferred : scenarioEntries[0].key;
            scenarioSelect.value = selectedKey;
            await loadScenarioFromHandle(selectedKey);
        }

        async function connectFileListRoot(files) {
            const { rootName, fileMap } = buildFileMap(files);
            const manifest = await readManifestFromFiles(fileMap);
            const scenarioEntries = discoverScenarioFiles(fileMap, manifest, rootName);
            if (!scenarioEntries.length) {
                throw new Error("選択したフォルダ配下にシナリオのディレクトリが見つかりません。");
            }

            state.accessMode = "file-root";
            state.rootHandle = null;
            state.rootUrl = "";
            state.rootFiles = fileMap;
            state.scenarioHandles = new Map();
            state.scenarioUrls = new Map();
            state.scenarioFilePrefixes = new Map(
                scenarioEntries.map(entry => [entry.key, entry.prefix]),
            );
            applyViewerMeta(manifest || {});
            populateScenarioSelect(scenarioEntries);
            setRootLabel(rootName);

            const preferred =
                state.viewerMeta.default_scenario ||
                scenarioEntries[0].key;
            const selectedKey = state.scenarioFilePrefixes.has(preferred) ? preferred : scenarioEntries[0].key;
            scenarioSelect.value = selectedKey;
            await loadScenarioFromFiles(selectedKey);
        }

        async function connectBundledRoot(rootUrl) {
            const manifest = JSON.parse(await fetchRequiredText(`${rootUrl}/manifest.json`));
            const scenarioEntries = normalizeScenarioEntries(manifest);
            if (!scenarioEntries.length) {
                throw new Error("同梱マニフェストにシナリオ定義が含まれていません。");
            }

            state.accessMode = "url-root";
            state.rootHandle = null;
            state.rootUrl = rootUrl;
            state.rootFiles = new Map();
            state.scenarioHandles = new Map();
            state.scenarioUrls = new Map(
                scenarioEntries.map(entry => [entry.key, `${rootUrl}/${entry.key}`]),
            );
            state.scenarioFilePrefixes = new Map();
            applyViewerMeta(manifest);
            populateScenarioSelect(scenarioEntries);
            setRootLabel(`同梱デモ・${rootUrl.split("/").pop()}`);

            const preferred =
                readScenarioPreference(rootUrl) ||
                state.viewerMeta.default_scenario ||
                scenarioEntries[0].key;
            const selectedKey = state.scenarioUrls.has(preferred) ? preferred : scenarioEntries[0].key;
            scenarioSelect.value = selectedKey;
            await loadScenarioFromUrl(selectedKey);
        }

        async function tryRestoreSavedRoot() {
            try {
                const rootHandle = await loadSavedRootHandle();
                if (!rootHandle) {
                    return false;
                }
                if (!(await verifyPermission(rootHandle))) {
                    return false;
                }
                await connectRootHandle(rootHandle, { persist: false });
                return true;
            } catch (error) {
                console.warn("failed to restore saved root", error);
                return false;
            }
        }

        async function tryLoadBundledRoot() {
            if (!location.protocol.startsWith("http")) {
                return false;
            }
            try {
                await connectBundledRoot(DEFAULT_ROOT_URL);
                return true;
            } catch (error) {
                console.warn("failed to load bundled root", error);
                return false;
            }
        }

        openButton.addEventListener("click", async () => {
            try {
                if (typeof window.showDirectoryPicker === "function") {
                    const rootHandle = await window.showDirectoryPicker({ id: "world-demo-root" });
                    await connectRootHandle(rootHandle);
                    return;
                }
                if (rootInput) {
                    rootInput.value = "";
                    rootInput.click();
                    return;
                }
                window.alert("このブラウザではフォルダ選択に対応していません。");
            } catch (error) {
                if (error && error.name !== "AbortError") {
                    console.error(error);
                    if (rootInput) {
                        rootInput.value = "";
                        rootInput.click();
                    } else {
                        window.alert("ルートディレクトリを読み込めませんでした。世界デモの出力ルートを選んでください。");
                    }
                }
            }
        });

        rootInput?.addEventListener("change", async event => {
            const files = event.target.files;
            if (!files || !files.length) {
                return;
            }
            try {
                await connectFileListRoot(files);
            } catch (error) {
                console.error(error);
                window.alert("選択したフォルダを読み込めませんでした。世界デモの出力ルートを選んでください。");
            } finally {
                rootInput.value = "";
            }
        });

        filterToggleButton.addEventListener("click", () => {
            state.filterPanelOpen = !state.filterPanelOpen;
            renderFilterPanel();
        });

        filterCloseButton.addEventListener("click", () => {
            state.filterPanelOpen = false;
            renderFilterPanel();
        });

        filterResetButton.addEventListener("click", () => {
            state.hiddenRegions.clear();
            state.hiddenCountries.clear();
            render();
        });

        regionFilterList.addEventListener("change", event => {
            const checkbox = event.target.closest?.("input[data-region]");
            if (!checkbox) {
                return;
            }
            const regionId = checkbox.dataset.region;
            if (!regionId) {
                return;
            }
            if (checkbox.checked) {
                state.hiddenRegions.delete(regionId);
            } else {
                state.hiddenRegions.add(regionId);
            }
            render();
        });

        countryFilterList.addEventListener("change", event => {
            const checkbox = event.target.closest?.("input[data-country]");
            if (!checkbox) {
                return;
            }
            const code = checkbox.dataset.country;
            if (!code) {
                return;
            }
            if (checkbox.checked) {
                state.hiddenCountries.delete(code);
            } else {
                state.hiddenCountries.add(code);
            }
            render();
        });

        scenarioSelect.addEventListener("change", async event => {
            const scenarioKey = event.target.value;
            stopPlayback();
            if (!scenarioKey) {
                return;
            }
            if (state.accessMode === "url-root") {
                await loadScenarioFromUrl(scenarioKey);
            } else if (state.accessMode === "file-root") {
                await loadScenarioFromFiles(scenarioKey);
            } else {
                await loadScenarioFromHandle(scenarioKey);
            }
        });

        tabButtons.forEach(button => {
            button.addEventListener("click", () => {
                state.sidebarTab = button.dataset.tab || "chat";
                renderSidebarTabs();
            });
        });

        playButton.addEventListener("click", () => {
            if (state.playing) {
                stopPlayback();
            } else {
                startPlayback();
            }
        });

        prevButton.addEventListener("click", () => {
            if (!state.turns.length) {
                return;
            }
            stopPlayback();
            state.turnIndex = (state.turnIndex - 1 + state.turns.length) % state.turns.length;
            render();
        });

        nextButton.addEventListener("click", () => {
            if (!state.turns.length) {
                return;
            }
            stopPlayback();
            state.turnIndex = (state.turnIndex + 1) % state.turns.length;
            render();
        });

        turnSlider.addEventListener("input", event => {
            stopPlayback();
            setTurnFromValue(event.target.value);
        });

        stage.addEventListener("wheel", event => {
            event.preventDefault();
            const multiplier = Math.exp(-event.deltaY * 0.0012);
            zoomMapAt(event.clientX, event.clientY, multiplier);
        }, { passive: false });

        stage.addEventListener("dblclick", event => {
            event.preventDefault();
            resetMapView();
        });

        stage.addEventListener("pointerdown", event => {
            if (event.button !== 0) {
                return;
            }
            state.mapView.dragging = true;
            state.mapView.pointerId = event.pointerId;
            state.mapView.downCountryCode = event.target.closest?.(".node-group")?.dataset.code || null;
            state.mapView.lastX = event.clientX;
            state.mapView.lastY = event.clientY;
            state.mapView.moved = false;
            stage.setPointerCapture(event.pointerId);
            applyMapTransform();
        });

        stage.addEventListener("pointermove", event => {
            if (!state.mapView.dragging || state.mapView.pointerId !== event.pointerId) {
                return;
            }
            const dx = event.clientX - state.mapView.lastX;
            const dy = event.clientY - state.mapView.lastY;
            if (Math.abs(dx) > 0 || Math.abs(dy) > 0) {
                state.mapView.translateX += dx;
                state.mapView.translateY += dy;
                state.mapView.lastX = event.clientX;
                state.mapView.lastY = event.clientY;
                if (Math.abs(dx) + Math.abs(dy) > 2) {
                    state.mapView.moved = true;
                }
                applyMapTransform();
            }
        });

        mapFocusCard.addEventListener("pointerdown", event => {
            if (event.button !== 0 || mapFocusCard.hidden) {
                return;
            }
            event.stopPropagation();
            state.mapFocusCard.dragging = true;
            state.mapFocusCard.pointerId = event.pointerId;
            state.mapFocusCard.lastX = event.clientX;
            state.mapFocusCard.lastY = event.clientY;
            mapFocusCard.setPointerCapture(event.pointerId);
            applyMapFocusCardPosition();
        });

        mapFocusCard.addEventListener("pointermove", event => {
            if (!state.mapFocusCard.dragging || state.mapFocusCard.pointerId !== event.pointerId) {
                return;
            }
            event.stopPropagation();
            const dx = event.clientX - state.mapFocusCard.lastX;
            const dy = event.clientY - state.mapFocusCard.lastY;
            state.mapFocusCard.x += dx;
            state.mapFocusCard.y += dy;
            state.mapFocusCard.lastX = event.clientX;
            state.mapFocusCard.lastY = event.clientY;
            applyMapFocusCardPosition();
        });

        function endMapFocusCardDrag(event) {
            if (state.mapFocusCard.pointerId !== event.pointerId) {
                return;
            }
            event.stopPropagation();
            if (mapFocusCard.hasPointerCapture(event.pointerId)) {
                mapFocusCard.releasePointerCapture(event.pointerId);
            }
            state.mapFocusCard.dragging = false;
            state.mapFocusCard.pointerId = null;
            applyMapFocusCardPosition();
        }

        mapFocusCard.addEventListener("pointerup", endMapFocusCardDrag);
        mapFocusCard.addEventListener("pointercancel", endMapFocusCardDrag);

        function endMapDrag(event) {
            if (state.mapView.pointerId !== event.pointerId) {
                return;
            }
            if (stage.hasPointerCapture(event.pointerId)) {
                stage.releasePointerCapture(event.pointerId);
            }
            state.mapView.dragging = false;
            state.mapView.pointerId = null;
            if (state.mapView.moved) {
                state.mapView.suppressClickUntil = Date.now() + 180;
            } else if (Date.now() >= state.mapView.suppressClickUntil) {
                if (state.mapView.downCountryCode) {
                    state.selectedCountry = state.mapView.downCountryCode;
                    state.mapFocusCountry = state.mapView.downCountryCode;
                } else {
                    state.mapFocusCountry = null;
                }
                render();
            }
            state.mapView.downCountryCode = null;
            applyMapTransform();
        }

        stage.addEventListener("pointerup", endMapDrag);
        stage.addEventListener("pointercancel", endMapDrag);
        window.addEventListener("resize", () => {
            applyMapTransform();
            applyMapFocusCardPosition();
        });

        document.addEventListener("keydown", event => {
            if (!state.turns.length) {
                return;
            }
            if (event.key === "ArrowRight") {
                stopPlayback();
                state.turnIndex = (state.turnIndex + 1) % state.turns.length;
                render();
            } else if (event.key === "ArrowLeft") {
                stopPlayback();
                state.turnIndex = (state.turnIndex - 1 + state.turns.length) % state.turns.length;
                render();
            } else if (event.key === " ") {
                event.preventDefault();
                if (state.playing) {
                    stopPlayback();
                } else {
                    startPlayback();
                }
            }
        });

        resetPlaybackUi();
        applyMapTransform();
