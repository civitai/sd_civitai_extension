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
    }
}

async function refreshModels() {
    const refreshModelsButton = await getElement('#refresh_sd_model_checkpoint');
    refreshModelsButton.click();
}

async function hookChild() {
    const child = new AcrossTabs.default.Child({
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

// Bootstrap
(async () => {
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.has('civitai_prompt'))
        handlePrompt(atob(searchParams.get('civitai_prompt')), searchParams.has('civitai_generate'));
    if (searchParams.has('civitai_refresh_models'))
        refreshModels()
    if (searchParams.has('civitai_hook_child'))
        hookChild();

    // clear search params
    history.replaceState({}, document.title, location.pathname);
})()