from civitai.link import on_civitai_link_key_changed
from modules import shared, script_callbacks

def on_ui_settings():
    section = ('civitai_link', "Civitai")
    shared.opts.add_option("civitai_link_key", shared.OptionInfo("", "Your Civitai Link Key", section=section, onchange=on_civitai_link_key_changed))
    shared.opts.add_option("civitai_link_logging", shared.OptionInfo(True, "Show Civitai Link events in the console", section=section))
    shared.opts.add_option("civitai_api_key", shared.OptionInfo("", "Your Civitai API Key", section=section))
    shared.opts.add_option("civitai_download_previews", shared.OptionInfo(True, "Download missing preview images on startup", section=section))
    shared.opts.add_option("civitai_download_triggers", shared.OptionInfo(True, "Download missing trigger text files on startup", section=section))
    shared.opts.add_option("civitai_nsfw_previews", shared.OptionInfo(False, "Download NSFW (adult) preview images", section=section))
    shared.opts.add_option("civitai_download_missing_models", shared.OptionInfo(True, "Download missing models upon reading generation parameters from prompt", section=section))
    shared.opts.add_option("civitai_hashify_resources", shared.OptionInfo(True, "Include resource hashes in image metadata (for resource auto-detection on Civitai)", section=section))
    shared.opts.add_option("civitai_folder_lora", shared.OptionInfo("", "LoRA directory (if not default)", section=section))


script_callbacks.on_ui_settings(on_ui_settings)
