from datetime import datetime, timezone
import time
from typing import List
import socketio

import civitai.lib as civitai
import civitai.generation as generation
from civitai.models import Command, CommandActivitiesList, CommandImageTxt2Img, CommandResourcesAdd, CommandActivitiesCancel, CommandResourcesList, CommandResourcesRemove, ErrorPayload, JoinedPayload, RoomPresence, UpgradeKeyPayload

from modules import shared, sd_models, script_callbacks, hashes

#region Civitai Link Utils
def log(message: str):
    if not shared.opts.data.get('civitai_link_logging', True): return
    print(f'Civitai Link: {message}')
#endregion

#region Civitai Link Command Handlers
def send_resources(types: List[str] = []):
    command_response({'type': 'resources:list', 'resources': civitai.load_resource_list(types)})

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
processing_activities: List[str] = []
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

    notified_of_download = False
    def on_progress(current: int, total: int, start_time: float):
        nonlocal notified_of_download
        if not notified_of_download:
            send_resources()
            notified_of_download = True

        if payload['id'] in should_cancel_activity:
            should_cancel_activity.remove(payload['id'])
            dl_resources = [r for r in civitai.resources if r['hash'] == resource['hash'] and r['downloading'] == True]
            if len(dl_resources) > 0:
                civitai.resources.remove(dl_resources[0])
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
        processing_activities.append(payload['id'])
        civitai.load_resource(resource, on_progress)
        if payload['status'] != 'canceled':
            payload['status'] = 'success'
    except Exception as e:
        log(e)
        if payload['status'] != 'canceled':
            payload['status'] = 'error'
            payload['error'] = 'Failed to download resource'

    processing_activities.remove(payload['id'])
    report_status(True)
    send_resources()

def on_activities_cancel(payload: CommandActivitiesCancel):
    activity_id = payload['activityId']
    if activity_id not in processing_activities:
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
        log(e)
        payload['status'] = 'error'
        payload['error'] = 'Failed to remove resource'

    command_response(payload, history=True)
    send_resources()

def on_image_txt2img(payload: CommandImageTxt2Img):
    try:
        result = generation.txt2img(payload)
        payload['status'] = 'success'
        payload['images'] = result.images
    except Exception as e:
        log(e)
        payload['status'] = 'error'
        payload['error'] = 'Failed to generate image: ' + e

    command_response(payload)
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

    log('Connected to Civitai Link Server')
    sio.emit('iam', {"type": "sd"})
    if should_reconnect:
        key = shared.opts.data.get("civitai_link_key", None)
        if key is None: return
        join_room(key)
        should_reconnect = False

@sio.event
def connect_error(data):
    log('Error connecting to Civitai Link Server')

@sio.event
def disconnect():
    global should_reconnect
    global current_key
    current_key = None

    log('Disconnected from Civitai Link Server')
    should_reconnect = True

@sio.on('command')
def on_command(payload: Command):
    command = payload['type']
    log(f"Incoming Command: {payload['type']}")
    civitai.add_activity(payload)

    if command == 'activities:list': return on_activities_list(payload)
    elif command == 'activities:clear': return on_activities_clear(payload)
    elif command == 'activities:cancel': return on_activities_cancel(payload)
    elif command == 'resources:list': return on_resources_list(payload)
    elif command == 'resources:add': return on_resources_add(payload)
    elif command == 'resources:remove': return on_resources_remove(payload)
    elif command == 'image:txt2img': return on_image_txt2img(payload)

@sio.on('kicked')
def on_kicked():
    log(f"Kicked from instance. Clearing key.")
    shared.opts.data['civitai_link_key'] = None

@sio.on('roomPresence')
def on_room_presence(payload: RoomPresence):
    log(f"Presence update: SD: {payload['sd']}, Clients: {payload['client']}")
    connected = payload['sd'] > 0 and payload['client'] > 0
    if civitai.connected != connected:
        civitai.connected = connected
        if connected: log("Connected to Civitai Instance")
        else: log("Disconnected from Civitai Instance")

upgraded_key = None
@sio.on('upgradeKey')
def on_upgrade_key(payload: UpgradeKeyPayload):
    global upgraded_key

    log("Link Key upgraded")
    shared.opts.data['civitai_link_key'] = payload['key']
    upgraded_key = payload['key']

@sio.on('error')
def on_error(payload: ErrorPayload):
    log(f"Error: {payload['msg']}")

def command_response(payload, history=False):
    payload['updatedAt'] = datetime.now(timezone.utc).isoformat()
    if history: civitai.add_activity(payload)
    sio.emit('commandStatus', payload)
#endregion

#region SocketIO Connection Management
def socketio_connect():
    if (sio.connected): return
    sio.connect(socketio_url, socketio_path='/api/socketio')

current_key = None
def join_room(key):
    if (current_key == key): return
    def on_join(payload):
        log(f"Joined room {key}")
    sio.emit('join', key, callback=on_join)

old_short_key = None
def on_civitai_link_key_changed():
    global old_short_key

    if not sio.connected: socketio_connect()

    # If the key is upgraded, don't change it back to the short key
    if old_short_key is not None and old_short_key == shared.opts.data.get("civitai_link_key", None):
        shared.opts.data['civitai_link_key'] = upgraded_key
        return

    key = shared.opts.data.get("civitai_link_key", None)
    if len(key) < 10: old_short_key = key
    join_room(key)
#endregion