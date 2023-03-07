# api endpoints
import gradio as gr
from fastapi import FastAPI

from modules import script_callbacks as script_callbacks

import civitai.lib as civitai
from civitai.models import GenerateImageRequest, ResourceRequest

def civitaiAPI(_: gr.Blocks, app: FastAPI):
    @app.get('/civitai/v1/link-status')
    def link_status():
        return { "connected": civitai.connected }

script_callbacks.on_app_started(civitaiAPI)
civitai.log("API loaded")
