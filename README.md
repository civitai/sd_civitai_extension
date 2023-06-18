# Civitai Extension for Automatic 1111 Stable Diffusion Web UI

Manage and interact with your Automatic 1111 SD instance right from Civitai

https://user-images.githubusercontent.com/607609/234462691-ecd578cc-b0ec-49e4-8e50-a917395a6874.mp4

## Features
- [x] Automatically download preview images for all models, LORAs, hypernetworks, and embeds
- [x] Automatically download a model based on the model hash upon applying pasted generation params
- [x] Resources in Metadata: Include the SHA256 hash of all resources used in an image to be able to automatically link to corresponding resources on Civitai
- [x] Flexible Resource Naming in Metadata: Hashify the names of resources in prompts to avoid issues with resource renaming and make prompts more portable
- [x] **[Civitai Link (Alpha)](https://civitai.com/v/civitai-link-intro):** Optional websocket connection to be able to add/remove resources and more in your SD instance while browsing Civitai or other Civitai Link enabled sites.

## Installation

### Through the Extensions UI (Recommended)
1. Open the Extensions Tab in Automatic1111 SD Web UI
2. In the Extension Tab Open the "Instal from URL" tab
3. Paste `https://github.com/civitai/sd_civitai_extension.git` into the URL input
4. Press install and wait for it to complete
5. **Restart Automatic1111** (Reloading the UI will not install the necessary requirements)

### Manually
1. Download the repo using any method (zip download or cloning)
```sh
git clone https://github.com/civitai/sd_civitai_extension.git
```

2. After downloading the repo, open a command prompt in that location
```sh
cd C:\path\to\sd_civitai_extension
```

3. Then run the included install.py script
```sh
py install.py
# OR
python install.py
```

## Frequently Asked Questions

### What the Civitai Link Key? Where do I get it?
The Civitai Link Key is a short 6 character token that you'll receive when setting up your Civitai Link instance (you can see it referenced here in this [Civitai Link installation video](https://civitai.com/v/civitai-link-installation)). The Link Key acts as a temporary secret key to connect your Stable Diffusion instance to your Civitai Account inside our link service.

Since Civitai Link is still in alpha, it is currently only available to Supporters as part of the Civitai Early Access program. You can get access to Civitai Link today by [becoming a supporter](https://civitai.com/pricing) 🥰 or you can wait until we've gotten it to a state that we're ready for a full release.

## Contribute

Hop into the development channel in our [Discord server](https://discord.gg/UwX5wKwm6c) and let's chat!
