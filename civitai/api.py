import json
import os
import requests
import re

from basicsr.utils.download_util import load_file_from_url
from modules import shared, sd_models
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
    if os.path.exists(path): return

    dir, file = os.path.split(path)
    load_file_from_url(url, dir, True, file)

async def load_model(name, url):
    model = sd_models.get_closet_checkpoint_match(name)

    if model is None:
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

async def load_hypernetwork(name, url):
    load_if_missing(os.path.join(models_path, 'hypernetworks', name), url)
    shared.opts.sd_hypernetwork = name
    shared.opts.save(shared.config_filename)
    shared.reload_hypernetworks()

#endregion Downloading
