import json
import os
import shutil
import tempfile
import time
from typing import List
import requests
import glob

from tqdm import tqdm
from modules import shared, sd_models, sd_vae, hashes
from modules.paths import models_path
from civitai.models import Command, ResourceRequest

#region shared variables
try:
    base_url = shared.cmd_opts.civitai_endpoint
except:
    base_url = 'https://civitai.com/api/v1'

connected = False
user_agent = 'CivitaiLink:Automatic1111'
download_chunk_size = 8192
cache_key = 'civitai'
#endregion

#region Utils
def log(message):
    """Log a message to the console."""
    print(f'Civitai: {message}')

def download_file(url, dest, on_progress=None):
    if os.path.exists(dest):
        log(f'File already exists: {dest}')

    log(f'Downloading: "{url}" to {dest}\n')

    response = requests.get(url, stream=True, headers={"User-Agent": user_agent})
    total = int(response.headers.get('content-length', 0))
    start_time = time.time()

    dest = os.path.expanduser(dest)
    dst_dir = os.path.dirname(dest)
    f = tempfile.NamedTemporaryFile(delete=False, dir=dst_dir)

    try:
        current = 0
        with tqdm(total=total, unit='B', unit_scale=True, unit_divisor=1024) as bar:
            for data in response.iter_content(chunk_size=download_chunk_size):
                current += len(data)
                pos = f.write(data)
                bar.update(pos)
                if on_progress is not None:
                    should_stop = on_progress(current, total, start_time)
                    if should_stop == True:
                        raise Exception('Download cancelled')
        f.close()
        shutil.move(f.name, dest)
    except OSError as e:
       print(f"Could not write the preview file to {dst_dir}")
       print(e)
    finally:
        f.close()
        if os.path.exists(f.name):
            os.remove(f.name)
#endregion Utils

#region API
def req(endpoint, method='GET', data=None, params=None, headers=None):
    """Make a request to the Civitai API."""
    if headers is None:
        headers = {}
    headers['User-Agent'] = user_agent
    api_key = shared.opts.data.get("civitai_api_key", None)
    if api_key is not None:
        headers['Authorization'] = f'Bearer {api_key}'
    if data is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    if params is None:
        params = {}
    response = requests.request(method, base_url+endpoint, data=data, params=params, headers=headers)
    if response.status_code != 200:
        raise Exception(f'Error: {response.status_code} {response.text}')
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

def get_all_by_hash(hashes: List[str]):
    response = req(f"/model-versions/by-hash", method='POST', data=hashes)
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

#region Get Utils
def get_lora_dir():
    lora_dir = shared.opts.data.get('civitai_folder_lora', shared.cmd_opts.lora_dir).strip()
    if not lora_dir: lora_dir = shared.cmd_opts.lora_dir
    return lora_dir

def get_automatic_type(type: str):
    if type == 'Hypernetwork': return 'hypernet'
    return type.lower()

def get_automatic_name(type: str, filename: str, folder: str):
    abspath = os.path.abspath(filename)
    if abspath.startswith(folder):
        fullname = abspath.replace(folder, '')
    else:
        fullname = os.path.basename(filename)

    if fullname.startswith("\\") or fullname.startswith("/"):
        fullname = fullname[1:]

    if type == 'Checkpoint': return fullname
    return os.path.splitext(fullname)[0]

def has_preview(filename: str):
    return os.path.isfile(os.path.splitext(filename)[0] + '.preview.png')

def has_info(filename: str):
    return os.path.isfile(os.path.splitext(filename)[0] + '.info.json')

def get_resources_in_folder(type, folder, exts=[], exts_exclude=[]):
    resources = []
    os.makedirs(folder, exist_ok=True)

    candidates = []
    for ext in exts:
        candidates += glob.glob(os.path.join(folder, '**/*.' + ext), recursive=True)
    for ext in exts_exclude:
        candidates = [x for x in candidates if not x.endswith(ext)]

    folder = os.path.abspath(folder)
    automatic_type = get_automatic_type(type)
    for filename in sorted(candidates):
        if os.path.isdir(filename):
            continue

        name = os.path.splitext(os.path.basename(filename))[0]
        automatic_name = get_automatic_name(type, filename, folder)
        hash = hashes.sha256(filename, f"{automatic_type}/{automatic_name}")

        resources.append({'type': type, 'name': name, 'hash': hash, 'path': filename, 'hasPreview': has_preview(filename), 'hasInfo': has_info(filename) })

    return resources

resources = []
def load_resource_list(types=['LORA', 'LoCon', 'Hypernetwork', 'TextualInversion', 'Checkpoint', 'VAE', 'Controlnet']):
    global resources

    # If resources is empty and types is empty, load all types
    # This is a helper to be able to get the resource list without
    # having to worry about initialization. On subsequent calls, no work will be done
    if len(resources) == 0 and len(types) == 0:
        types = ['LORA', 'LoCon', 'Hypernetwork', 'TextualInversion', 'Checkpoint', 'VAE', 'Controlnet']

    if 'LORA' in types:
        resources = [r for r in resources if r['type'] != 'LORA']
        resources += get_resources_in_folder('LORA', get_lora_dir(), ['pt', 'safetensors', 'ckpt'])
    if 'LoCon' in types:
        resources = [r for r in resources if r['type'] != 'LoCon']
        resources += get_resources_in_folder('LoCon', get_lora_dir(), ['pt', 'safetensors', 'ckpt'])
    if 'Hypernetwork' in types:
        resources = [r for r in resources if r['type'] != 'Hypernetwork']
        resources += get_resources_in_folder('Hypernetwork', shared.cmd_opts.hypernetwork_dir, ['pt', 'safetensors', 'ckpt'])
    if 'TextualInversion' in types:
        resources = [r for r in resources if r['type'] != 'TextualInversion']
        resources += get_resources_in_folder('TextualInversion', shared.cmd_opts.embeddings_dir, ['pt'])
    if 'Checkpoint' in types:
        resources = [r for r in resources if r['type'] != 'Checkpoint']
        resources += get_resources_in_folder('Checkpoint', sd_models.model_path, ['safetensors', 'ckpt'], ['vae.safetensors', 'vae.ckpt'])
    if 'Controlnet' in types:
        resources = [r for r in resources if r['type'] != 'Controlnet']
        resources += get_resources_in_folder('Controlnet', os.path.join(models_path, "ControlNet"), ['safetensors', 'ckpt'], ['vae.safetensors', 'vae.ckpt'])
    if 'VAE' in types:
        resources = [r for r in resources if r['type'] != 'VAE']
        resources += get_resources_in_folder('VAE', sd_models.model_path, ['vae.pt', 'vae.safetensors', 'vae.ckpt'])
        resources += get_resources_in_folder('VAE', sd_vae.vae_path, ['pt', 'safetensors', 'ckpt'])

    return resources

def get_resource_by_hash(hash: str):
    resources = load_resource_list([])

    found = [resource for resource in resources if hash.lower() == resource['hash'] and ('downloading' not in resource or resource['downloading'] != True)]
    if found:
        return found[0]

    return None

def get_model_by_hash(hash: str):
    found = [info for info in sd_models.checkpoints_list.values() if hash == info.sha256 or hash == info.shorthash or hash == info.hash]
    if found:
        return found[0]

    return None

#endregion Get Utils

#region Removing
def remove_resource(resource: ResourceRequest):
    removed = None
    target = get_resource_by_hash(resource['hash'])
    if target is None or target['type'] != resource['type']: removed = False
    elif os.path.exists(target['path']):
        os.remove(target['path'])
        removed = True

    if removed == True:
        log(f'Removed resource')
        load_resource_list([resource['type']])
        if resource['type'] == 'Checkpoint':
            sd_models.list_models()
        elif resource['type'] == 'Hypernetwork':
            shared.reload_hypernetworks()
        # elif resource['type'] == 'LORA':
            # TODO: reload LORA
    elif removed == None:
        log(f'Resource not found')
#endregion Removing

#region Downloading
def load_if_missing(path, url, on_progress=None):
    if os.path.exists(path): return True
    if url is None: return False

    download_file(url, path, on_progress)
    return None

def load_resource(resource: ResourceRequest, on_progress=None):
    resource['hash'] = resource['hash'].lower()
    existing_resource = get_resource_by_hash(resource['hash'])
    if existing_resource:
        log(f'Already have resource: {resource["name"]}')
        return

    resources.append({'type': resource['type'], 'name': resource['name'], 'hash': resource['hash'], 'downloading': True })

    if resource['type'] == 'Checkpoint': load_model(resource, on_progress)
    elif resource['type'] == 'CheckpointConfig': load_model_config(resource, on_progress)
    elif resource['type'] == 'Controlnet': load_controlnet(resource, on_progress)
    elif resource['type'] == 'Hypernetwork': load_hypernetwork(resource, on_progress)
    elif resource['type'] == 'TextualInversion': load_textual_inversion(resource, on_progress)
    elif resource['type'] == 'LORA': load_lora(resource, on_progress)
    elif resource['type'] == 'LoCon': load_lora(resource, on_progress)

    load_resource_list([resource['type']])

def fetch_model_by_hash(hash: str):
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
    load_resource(resource)

def load_model_config(resource: ResourceRequest, on_progress=None):
    load_if_missing(os.path.join(sd_models.model_path, resource['name']), resource['url'], on_progress)

def load_model(resource: ResourceRequest, on_progress=None):
    model = get_model_by_hash(resource['hash'])
    if model is not None:
        log('Found model in model list')
    if model is None and resource['url'] is not None:
        log('Downloading model')
        download_file(resource['url'], os.path.join(sd_models.model_path, resource['name']), on_progress)
        sd_models.list_models()
        model = get_model_by_hash(resource['hash'])

    return model

def load_controlnet(resource: ResourceRequest, on_progress=None):
    isAvailable = load_if_missing(os.path.join(models_path, 'ControlNet', resource['name']), resource['url'], on_progress)
    # TODO: reload controlnet list - not sure best way to import this
    # if isAvailable is None:
        # controlnet.list_available_models()

def load_textual_inversion(resource: ResourceRequest, on_progress=None):
    load_if_missing(os.path.join(shared.cmd_opts.embeddings_dir, resource['name']), resource['url'], on_progress)

def load_lora(resource: ResourceRequest, on_progress=None):
    isAvailable = load_if_missing(os.path.join(get_lora_dir(), resource['name']), resource['url'], on_progress)
    # TODO: reload lora list - not sure best way to import this
    # if isAvailable is None:
        # lora.list_available_loras()

def load_vae(resource: ResourceRequest, on_progress=None):
    # TODO: find by hash instead of name
    if not resource['name'].endswith('.pt'): resource['name'] += '.pt'
    full_path = os.path.join(models_path, 'VAE', resource['name'])

    isAvailable = load_if_missing(full_path, resource['url'], on_progress)
    if isAvailable is None:
        sd_vae.refresh_vae_list()

def load_hypernetwork(resource: ResourceRequest, on_progress=None):
    full_path = os.path.join(shared.cmd_opts.hypernetwork_dir, resource['name']);
    if not full_path.endswith('.pt'): full_path += '.pt'
    isAvailable = load_if_missing(full_path, resource['url'], on_progress)
    if isAvailable is None:
        shared.reload_hypernetworks()

#endregion Downloading

#region Selecting Resources
def select_model(resource: ResourceRequest):
    if shared.opts.data["sd_checkpoint_hash"] == resource['hash']: return

    model = load_model(resource)

    if model is not None:
        sd_models.load_model(model)
        shared.opts.save(shared.config_filename)
    else: log('Could not find model and no URL was provided')

def select_vae(resource: ResourceRequest):
    # TODO: find by hash instead of name
    if not resource['name'].endswith('.pt'): resource['name'] += '.pt'
    full_path = os.path.join(models_path, 'VAE', resource['name'])

    if sd_vae.loaded_vae_file is not None and sd_vae.get_filename(sd_vae.loaded_vae_file) == resource['name']:
        log('VAE already loaded')
        return

    isAvailable = load_if_missing(full_path, resource['url'])
    if not isAvailable:
        log('Could not find VAE')
        return

    sd_vae.refresh_vae_list()
    sd_vae.load_vae(shared.sd_model, full_path)

def clear_vae():
    log('Clearing VAE')
    sd_vae.clear_loaded_vae()

def select_hypernetwork(resource: ResourceRequest):
    # TODO: find by hash instead of name
    if shared.opts.sd_hypernetwork == resource['name']:
        log('Hypernetwork already loaded')
        return

    full_path = os.path.join(shared.cmd_opts.hypernetwork_dir, resource['name']);
    if not full_path.endswith('.pt'): full_path += '.pt'
    isAvailable = load_if_missing(full_path, resource['url'])
    if not isAvailable:
        log('Could not find hypernetwork')
        return

    shared.opts.sd_hypernetwork = resource['name']
    shared.opts.save(shared.config_filename)
    shared.reload_hypernetworks()

def clear_hypernetwork():
    if (shared.opts.sd_hypernetwork == 'None'): return

    log('Clearing hypernetwork')
    shared.opts.sd_hypernetwork = 'None'
    shared.opts.save(shared.config_filename)
    shared.reload_hypernetworks()
#endregion

#region Resource Management
def update_resource_preview(hash: str, to_update: dict):
    resources = load_resource_list([])
    matches = [resource for resource in resources if hash.lower() == resource['hash']]
    if len(matches) == 0: return

    for resource in matches:
        if 'preview_url' in to_update:
            # download image and save to resource['path'] - ext + '.preview.png'
            preview_path = os.path.splitext(resource['path'])[0] + '.preview.png'
            if not os.path.isfile(preview_path):
                download_file(to_update['preview_url'], preview_path)
        if 'triggers' in to_update:
            trigger_path = os.path.splitext(resource['path'])[0] + '.txt'
            if not os.path.isfile(trigger_path):
                with open(trigger_path, 'w') as f:
                    f.write(to_update['triggers'])

#endregion Selecting Resources

#region Activities
activities = []
activity_history_length = 10
ignore_activity_types = ['resources:list','activities:list','activities:clear', 'activities:cancel']
def add_activity(activity: Command):
    global activities

    if activity['type'] in ignore_activity_types: return

    existing_activity_index = [i for i, x in enumerate(activities) if x['id'] == activity['id']]
    if len(existing_activity_index) > 0: activities[existing_activity_index[0]] = activity
    else: activities.insert(0, activity)

    if len(activities) > activity_history_length:
        activities.pop()
#endregion
