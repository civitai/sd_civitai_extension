import json
import os
import requests

from modules import shared, sd_models, generation_parameters_copypaste

try:
    base_url = shared.cmd_options.civitai_endpoint
except:
    base_url = 'https://civitai.com/api/v1'

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
    'model': os.path.join('models', 'stable-diffusion'),
    'textual_inversion': os.path.join('embeddings'),
    'aesthetic_gradient': os.path.join('aesthetic_embeddings'),
    'hypernetwork': os.path.join('models', 'hypernetworks'),
}

def download(url, type):
    """Download a file from the Civitai API using requests and save file to type specific location with the filename from the content disposition header."""
    response = requests.get(url, stream=True)
    filename = response.headers['content-disposition'].split('filename=')[1]
    with open(os.path.join(download_locations[type], filename), 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    # update model list
    if type == 'model': sd_models.list_models()

    return filename

def download_model(url):
    return download(url, 'model')

def download_textual_inversion(url):
    return download(url, 'textual_inversion')

def download_aesthetic_gradient(url):
    return download(url, 'aesthetic_gradient')

def download_hypernetwork(url):
    return download(url, 'hypernetwork')

#endregion Downloading
