from typing import List
import gradio as gr
import threading

import extensions.sd_civitai_extension.civitai.lib as civitai

from modules import script_callbacks, shared

previewable_types = ['LORA', 'Hypernetwork', 'TextualInversion', 'Checkpoint']
def load_previews():
    download_missing_previews = shared.opts.data.get('civitai_download_previews', True)
    if not download_missing_previews: return

    civitai.log(f"Check resources for missing preview images")
    resources = civitai.load_resource_list()
    resources = [r for r in resources if r['type'] in previewable_types]

    # get all resources that are missing previews
    missing_previews = [r for r in resources if r['hasPreview'] is False]
    civitai.log(f"Found {len(missing_previews)} resources missing preview images")
    hashes = [r['hash'] for r in missing_previews]

    # split hashes into batches of 100 and fetch into results
    results = []
    try:
        for i in range(0, len(hashes), 100):
            batch = hashes[i:i + 100]
            results.extend(civitai.get_all_by_hash(batch))
    except:
        civitai.log("Failed to fetch preview images from Civitai")
        return

    if len(results) == 0:
        civitai.log("No preview images found on Civitai")
        return

    civitai.log(f"Found {len(results)} hash matches")

    # update the resources with the new preview
    updated = 0
    for r in results:
        if (r is None): continue

        for file in r['files']:
            hash = file['hashes']['SHA256']
            if hash.lower() not in hashes: continue
            image_url = r['images'][0]['url']
            civitai.update_resource_preview(hash, image_url)
            updated += 1

    civitai.log(f"Updated {updated} preview images")

# Automatically pull model with corresponding hash from Civitai
def start_load_previews(demo: gr.Blocks, app):
    thread = threading.Thread(target=load_previews)
    thread.start()

script_callbacks.on_app_started(start_load_previews)
