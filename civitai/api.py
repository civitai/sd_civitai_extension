import json
import os
import requests
import re

from basicsr.utils.download_util import load_file_from_url
from modules import shared, sd_models, sd_vae
from modules.paths import models_path

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
        return {"name": match.group(1), "hash": match.group(2)}
    return {"name": "", "hash": ""}
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

#region Downloading
def load_if_missing(path, url):
    if os.path.exists(path): return True
    if url is None: return False

    dir, file = os.path.split(path)
    load_file_from_url(url, dir, True, file)

async def load_config(name, url):
    load_if_missing(os.path.join(models_path, 'stable-diffusion', name), url)

async def load_model(name, url=None):
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

async def load_hypernetwork(name, url=None):
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
