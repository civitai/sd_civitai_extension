import extensions.sd_civitai_extension.civitai.lib as civitai
from extensions.sd_civitai_extension.scripts.link import on_civitai_link_key_changed

from modules import shared, script_callbacks

def on_ui_settings():
    section = ('civitai_link', "Civitai")
    shared.opts.add_option("civitai_link_key", shared.OptionInfo("", "Your Civitai Link Key", section=section, onchange=on_civitai_link_key_changed))
    shared.opts.add_option("civitai_api_key", shared.OptionInfo("", "Your Civitai API Key", section=section))

script_callbacks.on_ui_settings(on_ui_settings)