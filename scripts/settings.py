import sys
import os
import gradio as gr

cwd = os.getcwd()
utils_dir = os.path.join(cwd, 'extensions', 'sd_civitai_extension', 'scripts')
sys.path.extend([utils_dir])

from civitai.link import on_civitai_link_key_changed
from previews import load_previews,previews_update_info

from modules import shared, script_callbacks


def on_ui_settings():
    section = ('civitai_link', "Civitai")
    shared.opts.add_option("civitai_link_key", shared.OptionInfo("", "Your Civitai Link Key", section=section, onchange=on_civitai_link_key_changed))
    shared.opts.add_option("civitai_link_logging", shared.OptionInfo(True, "Show Civitai Link events in the console", section=section))
    shared.opts.add_option("civitai_api_key", shared.OptionInfo("", "Your Civitai API Key", section=section))
    shared.opts.add_option("civitai_on_startup_download_previews", shared.OptionInfo(False, "Download missing preview images on startup", section=section))
    shared.opts.add_option("civitai_nsfw_previews", shared.OptionInfo(False, "Download NSFW (adult) preview images", section=section))
    shared.opts.add_option("civitai_download_missing_models", shared.OptionInfo(True, "Download missing models upon reading generation parameters from prompt", section=section))
    shared.opts.add_option("civitai_hashify_resources", shared.OptionInfo(True, "Include resource hashes in image metadata (for resource auto-detection on Civitai)", section=section))
    shared.opts.add_option("civitai_folder_lora", shared.OptionInfo("", "LoRA directory (if not default)", section=section))
    shared.opts.add_option("civitai_manual_download_previews", shared.OptionInfo(previews_update_info[0], "Last manually load time", gr.Dropdown, lambda: {"choices": previews_update_info},refresh=load_previews,section=section))

script_callbacks.on_ui_settings(on_ui_settings)
