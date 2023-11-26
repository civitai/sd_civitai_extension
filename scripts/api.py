# api endpoints
import gradio as gr
from fastapi import FastAPI
from scripts.link import reconnect_to_civitai,get_link_status
from modules import script_callbacks as script_callbacks

import civitai.lib as civitai
from civitai.models import GenerateImageRequest, ResourceRequest

def civitaiAPI(_: gr.Blocks, app: FastAPI):
    @app.get('/civitai/v1/link-status')
    def link_status():
        return { "connected": civitai.connected }
    @app.get('/civitai/v1/reconnect-link')
    def reconnect_link():
        msg = reconnect_to_civitai()
        return { "message": msg }
    @app.get('/civitai/v1/alpha-link-status')
    def alpha_link_status():
        return { "connected": get_link_status() }
script_callbacks.on_app_started(civitaiAPI)
civitai.log("API loaded")
