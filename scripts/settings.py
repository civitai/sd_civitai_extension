import extensions.sd_civitai_extension.civitai.lib as civitai
from extensions.sd_civitai_extension.scripts.link import on_civitai_link_key_changed

from modules import shared, script_callbacks

def on_ui_settings():
    section = ('civitai_link', "Civitai")
    shared.opts.add_option("civitai_link_key", shared.OptionInfo("", "Your Civitai Link Key", section=section, onchange=on_civitai_link_key_changed))
    shared.opts.add_option("civitai_api_key", shared.OptionInfo("", "Your Civitai API Key", section=section))
    shared.opts.add_option("civitai_download_previews", shared.OptionInfo(True, "Download missing preview images on startup", section=section))
    shared.opts.add_option("civitai_nsfw_previews", shared.OptionInfo(False, "Download NSFW (adult) preview images", section=section))
    shared.opts.add_option("civitai_download_missing_models", shared.OptionInfo(True, "Download missing models upon reading generation parameters from prompt", section=section))
    shared.opts.add_option("civitai_hashify_resources", shared.OptionInfo(True, "Include resource hashes in image metadata", section=section))
    shared.opts.add_option("civitai_hashify_prompt", shared.OptionInfo(True, "Add hashed version of embed, lora, and hypernetwork trigger words to image metadata", section=section))

script_callbacks.on_ui_settings(on_ui_settings)