import json
import re
import os

import civitai.lib as civitai
from modules import script_callbacks, sd_vae, shared

additional_network_type_map = {
    'lora': 'LORA',
    'hypernet': 'Hypernetwork'
}
additional_network_pattern = r'<(lora|hypernet):([a-zA-Z0-9_\.\-\s]+):([0-9.]+)(?:[:].*)?>'
model_hash_pattern = r'Model hash: ([0-9a-fA-F]{10})'

# Automatically pull model with corresponding hash from Civitai
def add_resource_hashes(params):
    if 'parameters' not in params.pnginfo: return

    hashify_resources = shared.opts.data.get('civitai_hashify_resources', True)
    if not hashify_resources: return

    lines = params.pnginfo['parameters'].split('\n')
    generation_params = lines.pop()
    prompt_parts = '\n'.join(lines).split('Negative prompt:')
    prompt, negative_prompt = [s.strip() for s in prompt_parts[:2] + ['']*(2-len(prompt_parts))]

    hashed_prompt = prompt
    hashed_negative_prompt = negative_prompt

    resources = civitai.load_resource_list([])
    resource_hashes = {}

    # Hash the VAE
    if hashify_resources and sd_vae.loaded_vae_file is not None:
        vae_name = os.path.splitext(sd_vae.get_filename(sd_vae.loaded_vae_file))[0]
        vae_matches = [r for r in resources if r['type'] == 'VAE' and r['name'] == vae_name]
        if len(vae_matches) > 0:
            short_hash = vae_matches[0]['hash'][:10]
            resource_hashes['vae'] = short_hash


    # Check for embeddings in prompt
    embeddings = [r for r in resources if r['type'] == 'TextualInversion']
    for embedding in embeddings:
        embedding_name = embedding['name']
        embedding_pattern = re.compile(r'(?<![^\s:(|\[\]])' + re.escape(embedding_name) + r'(?![^\s:)|\[\]\,])', re.MULTILINE | re.IGNORECASE)

        match_prompt = embedding_pattern.search(prompt)
        match_negative = embedding_pattern.search(negative_prompt)
        if not match_prompt and not match_negative: continue

        short_hash = embedding['hash'][:10]
        resource_hashes[f'embed:{embedding_name}'] = short_hash

    # Check for additional networks in prompt
    network_matches = re.findall(additional_network_pattern, prompt)
    for match in network_matches:
        network_type, network_name, network_weight = match
        resource_type = additional_network_type_map[network_type]
        matching_resource = [r for r in resources if r['type'] == resource_type and (r['name'].lower() == network_name.lower() or r['name'].lower().split('-')[0] == network_name.lower())]
        if len(matching_resource) > 0:
            short_hash = matching_resource[0]['hash'][:10]
            resource_hashes[f'{network_type}:{network_name}'] = short_hash

    # Check for model hash in generation parameters
    model_match = re.search(model_hash_pattern, generation_params)
    if hashify_resources and model_match:
        model_hash = model_match.group(1)
        matching_resource = [r for r in resources if r['type'] == 'Checkpoint' and r['hash'].startswith(model_hash)]
        if len(matching_resource) > 0:
            short_hash = matching_resource[0]['hash'][:10]
            resource_hashes['model'] = short_hash

    if len(resource_hashes) > 0:
        params.pnginfo['parameters'] += f", Hashes: {json.dumps(resource_hashes)}"

script_callbacks.on_before_image_saved(add_resource_hashes)
