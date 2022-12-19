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

async function handlePrompt(encodedPrompt, andGenerate = false) {
    const prompt = atob(encodedPrompt);
    log('injecting prompt', prompt);
    const promptEl = await getElement('#txt2img_prompt textarea');
    promptEl.value = prompt;

    const pastePromptButton = await getElement('#paste');
    pastePromptButton.click();
    log('applying prompt');

    if (andGenerate) {
        await delay(3000);
        await generate();
    }
}

// Bootstrap
(async () => {
    const searchParams = new URLSearchParams(location.search);
    if (searchParams.has('civitai_prompt'))
        handlePrompt(searchParams.get('civitai_prompt'), searchParams.has('civitai_generate'));

    // clear search params
    history.replaceState({}, document.title, location.pathname);
})()