import gradio as gr

import civitai.link as link

from modules import shared, script_callbacks

def connect_to_civitai(demo: gr.Blocks, app):
    key = shared.opts.data.get("civitai_link_key", None)
    # If key is empty or not set, don't connect to Civitai Link
    if not key: return

    link.log('Connecting to Civitai Link Server')
    link.socketio_connect()
    link.join_room(key)
def get_link_status()-> bool:
    return link.is_connected()

def reconnect_to_civitai() -> str:
    key = shared.opts.data.get("civitai_link_key", None)
    # If key is empty or not set, don't connect to Civitai Link
    if not key: 
        msg = 'Civitai Link Key is empty'
        link.log(msg)
        return msg
   
    link.log('Reconnecting to Civitai Link Server')
    link.socketio_connect()
    link.rejoin_room(key)
    if link.is_connected():
        msg = 'Civitai Link active'
        link.log(msg)
        return msg
    else:
        return 'Civitai Link not connected'

script_callbacks.on_app_started(connect_to_civitai)

