# main ui
import time
import gradio as gr
import socketio
import os

import extensions.sd_civitai_extension.civitai.lib as civitai
from extensions.sd_civitai_extension.civitai.models import Command, CommandResourcesAdd, CommandResourcesList, CommandResourcesRemove, ErrorPayload, JoinedPayload, UpgradeKeyPayload

from modules import shared, sd_models, script_callbacks, hashes

#region Civitai Link Command Handlers
def on_resources_list(payload: CommandResourcesList):
    types = payload['types'] if 'types' in payload else []
    resources = civitai.load_resource_list(types)
    sio.emit('commandStatus', { 'type': payload['type'], 'resources': resources, 'status': 'success' })

report_interval = 10
def on_resources_add(payload: CommandResourcesAdd):
    resources = payload['resources']
    payload['status'] = 'processing'

    last_report = time.time()
    def report_status(force=False):
        nonlocal last_report
        current_time = time.time()
        if force or current_time - last_report > report_interval:
            sio.emit('commandStatus', { 'id': payload['id'], 'type': payload['type'], 'resources': resources, 'status': payload['status'] })
            last_report = current_time

    def progress_for_resource(resource):
        def on_progress(current: int, total: int, start_time: float):
            current_time = time.time()
            elapsed_time = current_time - start_time
            speed = current / elapsed_time
            remaining_time = (total - current) / speed
            progress = current / total * 100
            resource['status'] = 'processing'
            resource['progress'] = progress
            resource['remainingTime'] = remaining_time
            resource['speed'] = speed
            report_status()

        return on_progress

    had_error = False
    for resource in resources:
        try:
            civitai.load_resource(resource, progress_for_resource(resource))
            resource['status'] = 'success'
        except Exception as e:
            civitai.log(e)
            resource['status'] = 'error'
            resource['error'] = 'Failed to download resource'
            had_error = True
        report_status(True)


    payload['status'] = 'success' if not had_error else 'error'
    if had_error:
        payload['error'] = 'Failed to download some resources'

    report_status(True)

def on_resources_remove(payload: CommandResourcesRemove):
    resources = payload['resources']

    had_error = False
    for resource in resources:
        try:
            civitai.remove_resource(resource)
            resource['status'] = 'success'
        except Exception as e:
            civitai.log(e)
            resource['status'] = 'error'
            resource['error'] = 'Failed to remove resource'
            had_error = True

    sio.emit('commandStatus', { 'id': payload['id'], 'type': payload['type'], 'resources': resources, 'status': 'success' if not had_error else 'error' })
#endregion

#region SocketIO Events
try:
    socketio_url = shared.cmd_opts.civitai_link_endpoint
except:
    socketio_url = 'https://link.civitai.com'

sio = socketio.Client()

@sio.event
def connect():
    civitai.log('Connected to Civitai Link')
    sio.emit('iam', {"type": "sd"})

@sio.on('command')
def on_command(payload: Command):
    command = payload['type']
    civitai.log(f"command: {payload['type']}")
    if command == 'resources:list': return on_resources_list(payload)
    elif command == 'resources:add': return on_resources_add(payload)
    elif command == 'resources:remove': return on_resources_remove(payload)


@sio.on('linkStatus')
def on_link_status(payload: bool):
    civitai.connected = payload
    civitai.log("Civitai Link ready")

@sio.on('upgradeKey')
def on_upgrade_key(payload: UpgradeKeyPayload):
    civitai.log("Link Key upgraded")
    shared.opts.data['civitai_link_key'] = payload['key']

@sio.on('error')
def on_error(payload: ErrorPayload):
    civitai.log(f"Error: {payload['msg']}")

@sio.on('joined')
def on_joined(payload: JoinedPayload):
    if payload['type'] != 'client': return
    civitai.log("Client joined")
#endregion

#region SocketIO Connection Management
def socketio_connect():
    sio.connect(socketio_url, socketio_path='/api/socketio')

def join_room(key):
    def on_join(payload):
        civitai.log(f"Joined room {key}")
    sio.emit('join', key, callback=on_join)

def connect_to_civitai(demo: gr.Blocks, app):
    key = shared.opts.data.get("civitai_link_key", None)
    if key is None: return

    socketio_connect()
    join_room(key)

def on_civitai_link_key_changed():
    if not sio.connected: socketio_connect()
    key = shared.opts.data.get("civitai_link_key", None)
    join_room(key)
#endregion

def on_ui_settings():
    section = ('civitai_link', "Civitai Link")
    shared.opts.add_option("civitai_link_key", shared.OptionInfo("", "Your Civitai Link Key", section=section, onchange=on_civitai_link_key_changed))


# Automatically pull model with corresponding hash from Civitai
def on_infotext_pasted(infotext, params):
    if ("Model hash" not in params or shared.opts.disable_weights_auto_swap): return

    model_hash = params["Model hash"]
    model = civitai.get_model_by_hash(model_hash)
    if (model is None):
        civitai.fetch_model_by_hash(model_hash)

script_callbacks.on_infotext_pasted(on_infotext_pasted)
script_callbacks.on_ui_settings(on_ui_settings)
script_callbacks.on_app_started(connect_to_civitai)