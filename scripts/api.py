# api endpoints
import gradio as gr
from fastapi import FastAPI

from modules import script_callbacks as script_callbacks

import extensions.sd_civitai_extension.civitai.lib as civitai
from extensions.sd_civitai_extension.civitai.models import GenerateImageRequest, ResourceRequest

def civitaiAPI(demo: gr.Blocks, app: FastAPI):
    @app.get('/civitai/v1/link-status')
    def link_status():
        return { "connected": civitai.connected }

script_callbacks.on_app_started(civitaiAPI)
civitai.log("API loaded")
