(async function () {
    // #region [utils]
    const log = (...args) => console.log(`[civitai]`, ...args);
    const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
    const getElement = (selector, timeout = 10000) => new Promise((resolve, reject) => {
        const interval = setInterval(() => {
            const el = gradioApp().querySelector(selector);
            timeout -= 100;
            if (timeout < 0) {
                reject('timeout');
                clearInterval(interval);
            } else if (el) {
                resolve(el);
                clearInterval(interval);
            }
        }, 100);
    })
    // #endregion


    async function generate() {
        const generateButton = await getElement('#txt2img_generate');
        generateButton.click();
        log('generating image');
    }

    async function handlePrompt(prompt, andGenerate = false, delayMs = 3000) {
        log('injecting prompt', prompt);
        const promptEl = await getElement('#txt2img_prompt textarea');
        promptEl.value = prompt;
        promptEl.dispatchEvent(new Event("input", { bubbles: true })); // internal Svelte trigger

        const pastePromptButton = await getElement('#paste');
        pastePromptButton.click();
        log('applying prompt');

        if (andGenerate) {
            await delay(delayMs);
            await generate();
            notifyParent({generate: true});
        }
    }

    function notifyParent(msg) {
        if (child && child.sendMessageToParent)
            child.sendMessageToParent(msg);
    }

    async function refreshModels() {
        const refreshModelsButton = await getElement('#refresh_sd_model_checkpoint');
        refreshModelsButton.click();
    }

    let child;
    async function hookChild() {
        child = new AcrossTabs.default.Child({
            // origin: 'https://civitai.com',
            origin: 'http://localhost:3000',
            onParentCommunication: commandHandler
        });
    }

    function commandHandler({ command, ...data }) {
        log('tab communication', { command, data })
        switch (command) {
            case 'generate': return handlePrompt(data.generationParams, true, 500);
            case 'refresh-models': return refreshModels();
        }
    }

    let statusElement = document.createElement('div');
    let currentStatus = false;
    async function checkStatus() {
        const { connected } = await fetch('/civitai/v1/link-status').then(x=>x.json());
        if (currentStatus != connected) {
            currentStatus = connected;
            statusElement.classList.toggle('connected', connected);
        }
    }
    async function startStatusChecks() {
        statusElement.id = 'civitai-status';
        statusElement.classList.add('civitai-status');
        await getElement('.gradio-container'); // wait for gradio to load
        gradioApp().appendChild(statusElement);

        setInterval(checkStatus, 1000 * 10);
        checkStatus();
    }

    // Bootstrap
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.has('civitai_prompt'))
        handlePrompt(atob(searchParams.get('civitai_prompt')), searchParams.has('civitai_generate'));
    if (searchParams.has('civitai_refresh_models'))
        refreshModels()
    if (searchParams.has('civitai_hook_child'))
        hookChild();

    // clear search params
    history.replaceState({}, document.title, location.href);
    await startStatusChecks();
})();
