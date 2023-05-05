from typing import List
import gradio as gr
import threading

import civitai.lib as civitai

from modules import script_callbacks, shared

previewable_types = ['LORA', 'Hypernetwork', 'TextualInversion', 'Checkpoint']
def load_previews():
    download_missing_previews = shared.opts.data.get('civitai_download_previews', True)
    download_missing_triggers = shared.opts.data.get('civitai_download_triggers', True)
    if not download_missing_previews and not download_missing_triggers: return
    nsfw_previews = shared.opts.data.get('civitai_nsfw_previews', True)

    civitai.log(f"Check resources for missing preview images or trigger words")
    resources = civitai.load_resource_list()
    resources = [r for r in resources if r['type'] in previewable_types]

    # get all resources that are missing previews
    missing_preview_hashes = [r['hash'] for r in resources if r['hasPreview'] is False]
    missing_trigger_hashes = [r['hash'] for r in resources if r['hasInfo'] is False]
    hashes = list(set(missing_preview_hashes + missing_trigger_hashes))
    civitai.log(f"Found {len(hashes)} resources missing preview images or trigger words")

    # split hashes into batches of 100 and fetch into results
    results = []
    try:
        for i in range(0, len(hashes), 100):
            batch = hashes[i:i + 100]
            results.extend(civitai.get_all_by_hash(batch))
    except:
        civitai.log("Failed to fetch preview images and/or trigger words from Civitai")
        return

    if len(results) == 0:
        civitai.log("No preview images and/or trigger words found on Civitai")
        return

    civitai.log(f"Found {len(results)} hash matches")

    # update the resources with the new preview
    updated = 0
    for r in results:
        if (r is None): continue

        for file in r['files']:
            if not 'hashes' in file or not 'SHA256' in file['hashes']:
                continue
            hash = file['hashes']['SHA256']
            to_update = {}
            if hash.lower() in missing_preview_hashes:
                images = r['images']
                if (nsfw_previews is False):
                    images = [i for i in images if i['nsfw'] is False]
                if (len(images) > 0):
                    to_update['image_url'] = images[0]['url']

            if hash.lower() in missing_trigger_hashes:
                orig_len = len(r['trainedWords'])
                triggers = [w for w in r['trainedWords'] if w.isprintable()]
                if orig_len != len(triggers):
                    info = (file['name'], file['hashes']['AutoV2'])
                    civitai.log("Skipped non-ascii trigger(s): model %s, %s" % info)
                if (len(triggers) > 0):
                    to_update['triggers'] = ', '.join(triggers)
            civitai.update_resource_preview(hash, to_update)
            updated += 1

    civitai.log(f"Updated {updated} preview images and/or trigger words")

# Automatically pull model with corresponding hash from Civitai
def start_load_previews(demo: gr.Blocks, app):
    thread = threading.Thread(target=load_previews)
    thread.start()

script_callbacks.on_app_started(start_load_previews)
