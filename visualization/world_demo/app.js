	        renderSidebarTabs();

	        (async () => {
	            const restored = await tryRestoreSavedRoot();
	            if (restored) {
	                return;
	            }
	            await tryLoadBundledRoot();
	        })();
