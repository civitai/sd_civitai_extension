import civitai.lib as civitai

from modules import shared, script_callbacks

# Automatically pull model with corresponding hash from Civitai
def on_infotext_pasted(infotext, params):
    download_missing_models = shared.opts.data.get('civitai_download_missing_models', True)
    if (not download_missing_models or "Model hash" not in params or shared.opts.disable_weights_auto_swap):
        return

    model_hash = params["Model hash"]
    model = civitai.get_model_by_hash(model_hash)
    if (model is None):
        civitai.fetch_model_by_hash(model_hash)

script_callbacks.on_infotext_pasted(on_infotext_pasted)
