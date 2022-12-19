import json
import os
import requests
import re

from modules import shared, sd_models, generation_parameters_copypaste

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
download_locations = {
    'Checkpoint': os.path.join('models', 'stable-diffusion'),
    'TextualInversion': os.path.join('embeddings'),
    'AestheticGradient': os.path.join('extensions/stable-diffusion-webui-aesthetic-gradients','aesthetic_embeddings'),
    'Hypernetwork': os.path.join('models', 'hypernetworks'),
}

async def download(url, type):
    """Download a file from the Civitai API using requests and save file to type specific location with the filename from the content disposition header."""
    log(f'Downloading {type}: {url}')
    response = requests.get(url, stream=True)

    if response.status_code != 200:
        raise Exception(f'Error: {response.status_code}')

    filename = response.headers['content-disposition'].split('filename=')[1].strip('"')
    dest = os.path.join(download_locations[type], filename)

    if os.path.exists(dest):
        log(f'File already exists: {dest}')
        return (filename, False)

    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=4096):
            if chunk: f.write(chunk)

    log(f'Downloaded: {dest}')

    return (filename, True)

async def run_model(name, url):
    model = sd_models.get_closet_checkpoint_match(name)

    if model is None:
        (filename, downloaded) = await download(url, 'Checkpoint')
        if downloaded: sd_models.list_models()
        model = sd_models.get_closet_checkpoint_match(filename)
    elif shared.opts.sd_model_checkpoint == model.title:
        log('Model already loaded')
        return model.filename
    else:
        filename = model.filename
        log('Found model in model list')

    if model is not None:
        sd_models.load_model(model)
        shared.opts.sd_model_checkpoint = model.title
        shared.opts.save(shared.config_filename)
    else: log('Could not find model in model list')

    return filename


async def download_textual_inversion(url):
    (filename) = await download(url, 'TextualInversion')
    return filename

async def download_aesthetic_gradient(url):
    (filename, downloaded) = await download(url, 'AestheticGradient')

    return filename

async def download_hypernetwork(url):
    (filename, downloaded) = await download(url, 'Hypernetwork')
    shared.opts.sd_hypernetwork = filename
    shared.reload_hypernetworks()

    return filename

#endregion Downloading
