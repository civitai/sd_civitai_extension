import json
import re
import os

import extensions.sd_civitai_extension.civitai.lib as civitai
from modules import script_callbacks, sd_vae, shared

additional_network_type_map = {
    'lora': 'LORA',
    'hypernet': 'Hypernetwork'
}
additional_network_pattern = r'<(lora|hypernet):([a-zA-Z0-9_\.]+):([0-9.]+)>'
model_hash_pattern = r'Model hash: ([0-9a-fA-F]{10})'

# Automatically pull model with corresponding hash from Civitai
def add_resource_hashes(params):
    if 'parameters' not in params.pnginfo: return

    hashify_prompt = shared.opts.data.get('civitai_hashify_prompt', True)
    hashify_resources = shared.opts.data.get('civitai_hashify_resources', True)
    if not hashify_prompt and not hashify_resources: return

    lines = params.pnginfo['parameters'].split('\n')
    generation_params = lines.pop()
    prompt_parts = '\n'.join(lines).split('Negative prompt:')
    prompt, negative_prompt = [s.strip() for s in prompt_parts[:2] + ['']*(2-len(prompt_parts))]

    hashed_prompt = prompt
    hashed_negative_prompt = negative_prompt

    resources = civitai.load_resource_list([])
    resource_hashes = []

    # Hash the VAE
    if hashify_resources and sd_vae.loaded_vae_file is not None:
        vae_name = os.path.splitext(sd_vae.get_filename(sd_vae.loaded_vae_file))[0]
        vae_matches = [r for r in resources if r['type'] == 'VAE' and r['name'] == vae_name]
        if len(vae_matches) > 0:
            resource_hashes.append(vae_matches[0]['hash'])


    # Check for embeddings in prompt
    embeddings = [r for r in resources if r['type'] == 'TextualInversion']
    for embedding in embeddings:
        embedding_pattern = re.compile(r'(?<![^\s:(|\[\]])' + re.escape(embedding['name']) + r'(?![^\s:)|\[\]])', re.MULTILINE | re.IGNORECASE)

        match_prompt = embedding_pattern.search(prompt)
        match_negative = embedding_pattern.search(negative_prompt)
        if not match_prompt and not match_negative: continue

        short_hash = embedding['hash'][:10]
        if match_negative and hashify_prompt:
            hashed_negative_prompt = embedding_pattern.sub(short_hash, hashed_negative_prompt)
        if match_prompt and hashify_prompt:
            hashed_prompt = embedding_pattern.sub(short_hash, hashed_prompt)

        resource_hashes.append(embedding['hash'])

    # Check for additional networks in prompt
    network_matches = re.findall(additional_network_pattern, prompt)
    for match in network_matches:
        network_type, network_name, network_weight = match
        resource_type = additional_network_type_map[network_type]
        matching_resource = [r for r in resources if r['type'] == resource_type and r['name'].lower() == network_name.lower()]
        if len(matching_resource) > 0:
            short_hash = matching_resource[0]['hash'][:10]
            if hashify_prompt:
                hashed_prompt = hashed_prompt.replace(f'<{network_type}:{network_name}:{network_weight}>', f'<{network_type}:{short_hash}:{network_weight}>')
            resource_hashes.append(matching_resource[0]['hash'])

    # Check for model hash in generation parameters
    model_match = re.search(model_hash_pattern, generation_params)
    if hashify_resources and model_match:
        model_hash = model_match.group(1)
        matching_resource = [r for r in resources if r['type'] == 'Checkpoint' and r['hash'].startswith(model_hash)]
        if len(matching_resource) > 0:
            resource_hashes.append(matching_resource[0]['hash'])

    if hashify_resources:
        params.pnginfo['parameters'] += f", Resources: {json.dumps(resource_hashes)}"
    if hashify_prompt and hashed_prompt != prompt:
        params.pnginfo['parameters'] += f", Hashed prompt: {json.dumps(hashed_prompt)}"
    if hashify_prompt and hashed_negative_prompt != negative_prompt:
        params.pnginfo['parameters'] += f", Hashed Negative prompt: {json.dumps(hashed_negative_prompt)}"

script_callbacks.on_before_image_saved(add_resource_hashes)
