# main ui
from datetime import datetime, timezone
import time
from typing import List
import gradio as gr
import socketio
import os

import extensions.sd_civitai_extension.civitai.lib as civitai
from extensions.sd_civitai_extension.civitai.models import Command, CommandActivitiesList, CommandResourcesAdd, CommandActivitiesCancel, CommandResourcesList, CommandResourcesRemove, ErrorPayload, JoinedPayload, RoomPresence, UpgradeKeyPayload

from modules import shared, sd_models, script_callbacks, hashes

#region Civitai Link Command Handlers
def on_resources_list(payload: CommandResourcesList):
    types = payload['types'] if 'types' in payload else []
    payload['resources'] = civitai.load_resource_list(types)
    payload['status'] = 'success'
    command_response(payload)

def on_activities_list(payload: CommandActivitiesList):
    payload['activities'] = civitai.activities
    payload['status'] = 'success'
    command_response(payload)

def on_activities_clear(payload: CommandActivitiesList):
    civitai.activities = []
    payload['activities'] = civitai.activities
    payload['status'] = 'success'
    command_response(payload)

report_interval = 1
processing_activites: List[str] = []
should_cancel_activity: List[str] = []
def on_resources_add(payload: CommandResourcesAdd):
    resource = payload['resource']
    payload['status'] = 'processing'

    last_report = time.time()
    def report_status(force=False):
        nonlocal last_report
        current_time = time.time()
        if force or current_time - last_report > report_interval:
            command_response(payload, history=True)
            last_report = current_time

    def on_progress(current: int, total: int, start_time: float):
        if payload['id'] in should_cancel_activity:
            should_cancel_activity.remove(payload['id'])
            payload['status'] = 'canceled'
            return True

        current_time = time.time()
        elapsed_time = current_time - start_time
        speed = current / elapsed_time
        remaining_time = (total - current) / speed
        progress = current / total * 100
        payload['status'] = 'processing'
        payload['progress'] = progress
        payload['remainingTime'] = remaining_time
        payload['speed'] = speed
        report_status()

    try:
        processing_activites.append(payload['id'])
        civitai.load_resource(resource, on_progress)
        if payload['status'] != 'canceled':
            payload['status'] = 'success'
    except Exception as e:
        civitai.log(e)
        if payload['status'] != 'canceled':
            payload['status'] = 'error'
            payload['error'] = 'Failed to download resource'

    processing_activites.remove(payload['id'])
    report_status(True)

def on_activities_cancel(payload: CommandActivitiesCancel):
    activity_id = payload['activityId']
    if activity_id not in processing_activites:
        payload['status'] = 'error'
        payload['error'] = 'Activity not found or already completed'
    else:
        should_cancel_activity.append(activity_id)
        payload['status'] = 'success'

    command_response(payload)

def on_resources_remove(payload: CommandResourcesRemove):
    try:
        civitai.remove_resource(payload['resource'])
        payload['status'] = 'success'
    except Exception as e:
        civitai.log(e)
        payload['status'] = 'error'
        payload['error'] = 'Failed to remove resource'

    command_response(payload, history=True)
#endregion

#region SocketIO Events
try:
    socketio_url = shared.cmd_opts.civitai_link_endpoint
except:
    socketio_url = 'https://link.civitai.com'

sio = socketio.Client()
should_reconnect = False

@sio.event
def connect():
    global should_reconnect

    civitai.log('Connected to Civitai Link Server')
    sio.emit('iam', {"type": "sd"})
    if should_reconnect:
        key = shared.opts.data.get("civitai_link_key", None)
        if key is None: return
        join_room(key)
        should_reconnect = False

@sio.event
def disconnect():
    global should_reconnect

    civitai.log('Disconnected from Civitai Link Server')
    should_reconnect = True

@sio.on('command')
def on_command(payload: Command):
    command = payload['type']
    civitai.log(f"command: {payload['type']}")
    civitai.add_activity(payload)

    if command == 'activities:list': return on_activities_list(payload)
    elif command == 'activities:clear': return on_activities_clear(payload)
    elif command == 'activities:cancel': return on_activities_cancel(payload)
    elif command == 'resources:list': return on_resources_list(payload)
    elif command == 'resources:add': return on_resources_add(payload)
    elif command == 'resources:remove': return on_resources_remove(payload)


@sio.on('roomPresence')
def on_link_status(payload: RoomPresence):
    civitai.log(f"Presence update: SD: {payload['sd']}, Clients: {payload['client']}")
    civitai.connected = payload['sd'] > 0 and payload['client'] > 0

@sio.on('upgradeKey')
def on_upgrade_key(payload: UpgradeKeyPayload):
    civitai.log("Link Key upgraded")
    shared.opts.data['civitai_link_key'] = payload['key']

@sio.on('error')
def on_error(payload: ErrorPayload):
    civitai.log(f"Error: {payload['msg']}")

def command_response(payload, history=False):
    payload['updatedAt'] = datetime.now(timezone.utc).isoformat()
    if history: civitai.add_activity(payload)
    sio.emit('commandStatus', payload)
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