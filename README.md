# Civitai Extension for Automatic 1111 Stable Diffusion Web UI

Bringing together the power of Civitai and Automatic 1111

**⚠️ This is a work in progress and not something you can use yet.**

## Features
- [x] Automatically download preview images for all models, LORAs, hypernetworks, and embeds
- [x] Automatically download a model based on the model hash upon applying pasted generation params
- [x] Resources in Metadata: Include the SHA256 hash of all resources used in an image to be able to automatically link to corresponding resources on Civitai
- [x] Flexible Resource Naming in Metadata: Hashify the names of resources in prompts to avoid issues with resource renaming and make prompts more portable
- [ ] Civitai Link: Optional websocket connection to be able to add/remove resources and more in your SD instance while browsing Civitai or other Civitai Link enabled sites.

## Usage

Download the repo using any method (zip download or cloning)
```
git clone https://github.com/civitai/sd_civitai_extension.git
```
After downloading the repo, open a command prompt in that location
```
cd C:\path\to\sd_civitai_extension
```
Then run the included install.py script
```
py install.py
      OR
python install.py
```

## Here to help?

Hop into the development channel in our [Discord server](https://discord.gg/UwX5wKwm6c) and let's chat!