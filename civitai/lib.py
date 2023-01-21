import json
import os
import requests
import re

from importlib import import_module
from basicsr.utils.download_util import load_file_from_url
from modules import shared, sd_models, sd_vae
from modules.paths import models_path
from extensions.sd_civitai_extension.civitai.models import ResourceRequest

try:
    base_url = shared.cmd_opts.civitai_endpoint
except:
    base_url = 'https://civitai.com/api/v1'

#region Utils
def log(message):
    """Log a message to the console."""
    print(f'Civitai: {message}')

def parse_hypernetwork(string):
    match = re.search(r'(.+)\(([^)]+)', string)
    if match:
        return {"name": match.group(1), "hash": match.group(2), "type": "Hypernetwork"}
    return {"name": "", "hash": "", "type": "Hypernetwork"}
#endregion Utils

#region API
def req(endpoint, method='GET', data=None, params=None, headers=None):
    """Make a request to the Civitai API."""
    if headers is None:
        headers = {}
    headers['User-Agent'] = 'Automatic1111'
    if data is not None:
        data = json.dumps(data)
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    if params is None:
        params = {}
    response = requests.request(method, base_url+endpoint, data=data, params=params, headers=headers)
    return response.json()

def get_models(query, creator, tag, type, page=1, page_size=20, sort='Most Downloaded', period='AllTime'):
    """Get a list of models from the Civitai API."""
    response = req('/models', params={
        'query': query,
        'username': creator,
        'tag': tag,
        'type': type,
        'sort': sort,
        'period': period,
        'page': page,
        'pageSize': page_size,
    })
    return response

def get_model_version(id):
    """Get a model version from the Civitai API."""
    response = req('/model-versions/'+id)
    return response

def get_model_version_by_hash(hash: str):
    response = req(f"/model-versions/by-hash/{hash}")
    return response

def get_creators(query, page=1, page_size=20):
    """Get a list of creators from the Civitai API."""
    response = req('/creators', params={
        'query': query,
        'page': page,
        'pageSize': page_size
    })
    return response

def get_tags(query, page=1, page_size=20):
    """Get a list of tags from the Civitai API."""
    response = req('/tags', params={
        'query': query,
        'page': page,
        'pageSize': page_size
    })
    return response
#endregion API

#region Auto Utils
def get_model_by_hash(hash: str):
    found = [info for info in sd_models.checkpoints_list.values() if hash == info.sha256 or hash == info.shorthash or hash == info.hash]
    if found:
        return found[0]

    return None
#endregion Auto Utils

#region Downloading
def load_if_missing(path, url):
    if os.path.exists(path): return True
    if url is None: return False

    dir, file = os.path.split(path)
    load_file_from_url(url, dir, True, file)
    return None

async def load_resource(resource: ResourceRequest):
    if resource.type == 'Checkpoint': await load_model(resource)
    if resource.type == 'CheckpointConfig': await load_model_config(resource)
    elif resource.type == 'Hypernetwork': await load_hypernetwork(resource)
    elif resource.type == 'TextualInversion': await load_textual_inversion(resource)
    elif resource.type == 'AestheticGradient': await load_aesthetic_gradient(resource)
    elif resource.type == 'VAE': await load_vae(resource)
    elif resource.type == 'LORA': await load_lora(resource)

async def fetch_model_by_hash(hash: str):
    model_version = get_model_version_by_hash(hash)
    if model_version is None:
        log(f'Could not find model version with hash {hash}')
        return None

    file = [x for x in model_version['files'] if x['primary'] == True][0]
    resource = ResourceRequest(
        name=file['name'],
        type='Checkpoint',
        hash=file['hashes']['SHA256'],
        url=file['downloadUrl']
    )
    await load_resource(resource)

async def load_model_config(resource: ResourceRequest):
    load_if_missing(os.path.join(models_path, 'stable-diffusion', resource.name), resource.url)

async def load_model(resource: ResourceRequest):
    if shared.opts.data["sd_checkpoint_hash"] == resource.hash: return

    model = get_model_by_hash(resource.hash)
    if model is not None:
        log('Found model in model list')
    if model is None and resource.url is not None:
        log('Downloading model')
        load_file_from_url(resource.url, os.path.join(models_path, 'stable-diffusion'), True, resource.name)
        sd_models.list_models()
        model = get_model_by_hash(resource.hash)

    if model is not None:
        sd_models.load_model(model)
        shared.opts.save(shared.config_filename)
    else: log('Could not find model and no URL was provided')

async def load_hypernetwork(resource: ResourceRequest):
    # TODO: rig some way to work with hashes instead of names to avoid collisions

    if shared.opts.sd_hypernetwork == resource.name:
        log('Hypernetwork already loaded')
        return

    full_path = os.path.join(models_path, 'hypernetworks', resource.name);
    if not full_path.endswith('.pt'): full_path += '.pt'
    isAvailable = load_if_missing(full_path, resource.url)
    if not isAvailable:
        log('Could not find hypernetwork')
        return

    shared.opts.sd_hypernetwork = resource.name
    shared.opts.save(shared.config_filename)
    shared.reload_hypernetworks()

async def load_textual_inversion(resource: ResourceRequest):
    # TODO: rig some way to work with hashes instead of names to avoid collisions
    load_if_missing(os.path.join('embeddings', resource.name), resource.url)

async def load_aesthetic_gradient(resource: ResourceRequest):
    # TODO: rig some way to work with hashes instead of names to avoid collisions
    load_if_missing(os.path.join('extensions/stable-diffusion-webui-aesthetic-gradients','aesthetic_embeddings', resource.name), resource.url)

async def load_vae(resource: ResourceRequest):
    # TODO: rig some way to work with hashes instead of names to avoid collisions

    if not resource.name.endswith('.pt'): resource.name += '.pt'
    full_path = os.path.join(models_path, 'VAE', resource.name)

    if sd_vae.loaded_vae_file is not None and sd_vae.get_filename(sd_vae.loaded_vae_file) == resource.name:
        log('VAE already loaded')
        return

    isAvailable = load_if_missing(full_path, resource.url)
    if not isAvailable:
        log('Could not find VAE')
        return

    sd_vae.refresh_vae_list()
    sd_vae.load_vae(shared.sd_model, full_path)

async def load_lora(resource: ResourceRequest):
    isAvailable = load_if_missing(os.path.join('extensions/sd-webui-additional-networks/models/lora', resource.name), resource.url)

    # TODO: Auto refresh LORA
    # lora = import_module('extensions.sd-webui-additional-networks.scripts.additional_networks')
    # if lora is None:
    #     log('LORA extension not installed')
    #     return
    # if isAvailable is None: # isAvailable is None if the file was downloaded
    #     lora.update_lora_models()

    # TODO: Select LORA
    # ¯\_(ツ)_/¯

async def old_load_model(name, url=None):
    if shared.opts.sd_model_checkpoint == name: return

    model = sd_models.get_closet_checkpoint_match(name)
    if model is None and url is not None:
        log('Downloading model')
        load_if_missing(os.path.join(models_path, 'stable-diffusion', name), url)
        sd_models.list_models()
        model = sd_models.get_closet_checkpoint_match(name)
    elif shared.opts.sd_model_checkpoint == model.title:
        log('Model already loaded')
        return
    else:
        log('Found model in model list')

    if model is not None:
        sd_models.load_model(model)
        shared.opts.sd_model_checkpoint = model.title
        shared.opts.save(shared.config_filename)
    else: log('Could not find model in model list')


async def download_textual_inversion(name, url):
    load_if_missing(os.path.join('embeddings', name), url)

async def download_aesthetic_gradient(name, url):
    load_if_missing(os.path.join('extensions/stable-diffusion-webui-aesthetic-gradients','aesthetic_embeddings', name), url)

async def old_load_hypernetwork(name, url=None):
    if shared.opts.sd_hypernetwork == name:
        log('Hypernetwork already loaded')
        return

    full_path = os.path.join(models_path, 'hypernetworks', name);
    if not full_path.endswith('.pt'): full_path += '.pt'
    isAvailable = load_if_missing(full_path, url)
    if not isAvailable:
        log('Could not find hypernetwork')
        return

    shared.opts.sd_hypernetwork = name
    shared.opts.save(shared.config_filename)
    shared.reload_hypernetworks()

def clear_hypernetwork():
    if (shared.opts.sd_hypernetwork == 'None'): return

    log('Clearing hypernetwork')
    shared.opts.sd_hypernetwork = 'None'
    shared.opts.save(shared.config_filename)
    shared.reload_hypernetworks()

async def load_vae(name, url=None):
    if not name.endswith('.pt'): name += '.pt'
    full_path = os.path.join(models_path, 'VAE', name)

    if sd_vae.loaded_vae_file is not None and sd_vae.get_filename(sd_vae.loaded_vae_file) == name:
        log('VAE already loaded')
        return

    isAvailable = load_if_missing(full_path, url)
    if not isAvailable:
        log('Could not find VAE')
        return

    sd_vae.refresh_vae_list()
    sd_vae.load_vae(shared.sd_model, full_path)

def clear_vae():
    log('Clearing VAE')
    sd_vae.clear_loaded_vae()

#endregion Downloading
