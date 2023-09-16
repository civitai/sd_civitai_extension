from typing import List
import gradio as gr
import threading
import json
from pathlib import Path

import civitai.lib as civitai

from modules import script_callbacks, shared

actionable_types = ['LORA', 'LoCon', 'Hypernetwork', 'TextualInversion', 'Checkpoint']


def load_info():
    download_missing_previews = shared.opts.data.get('civitai_download_triggers', True)
    if not download_missing_previews:
        return

    civitai.log("Check resources for missing info files")
    resources = civitai.load_resource_list()
    resources = [r for r in resources if r['type'] in actionable_types]

    # get all resources that have no info files
    missing_info = [r for r in resources if r['hasInfo'] is False]
    civitai.log(f"Found {len(missing_info)} resources missing info files")
    hashes = [r['hash'] for r in missing_info]

    # split hashes into batches of 100 and fetch into results
    results = []
    try:
        for i in range(0, len(hashes), 100):
            batch = hashes[i:i + 100]
            results.extend(civitai.get_all_by_hash(batch))
    except:
        civitai.log("Failed to fetch info from Civitai")
        return

    if len(results) == 0:
        civitai.log("No info found on Civitai")
        return

    civitai.log(f"Found {len(results)} hash matches")

    # update the resources with the new info
    updated = 0
    for r in results:
        if (r is None):
            continue

        for file in r['files']:
            if not 'hashes' in file or not 'SHA256' in file['hashes']: 
                continue
            file_hash = file['hashes']['SHA256']
            if file_hash.lower() not in hashes: 
                continue

            if "SD 1" in r['baseModel']:
                sd_version = "SD1"
            elif "SD 2" in r['baseModel']:
                sd_version = "SD2"
            elif "SDXL" in r['baseModel']:
                sd_version = "SDXL"
            else:
                sd_version = "unknown"
            data = {
                "description": r['description'],
                "sd version": sd_version,
                "activation text": ", ".join(r['trainedWords']),
                "notes": "",
            }
            
            matches = [resource for resource in missing_info if file_hash.lower() == resource['hash']]
            if len(matches) == 0: 
                continue

            for resource in matches:
                Path(resource['path']).with_suffix(".json").write_text(json.dumps(data, indent=4))
            updated += 1

    civitai.log(f"Updated {updated} info files")


# Automatically pull model with corresponding hash from Civitai
def start_load_info(demo: gr.Blocks, app):
    thread = threading.Thread(target=load_info)
    thread.start()


script_callbacks.on_app_started(start_load_info)
