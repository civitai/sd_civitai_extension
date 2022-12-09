# api endpoints
import asyncio
import gradio as gr
from fastapi import FastAPI

from modules import shared, script_callbacks as script_callbacks

import extensions.sd_civitai_extension.civitai.api as civitai

def civitaiAPI(demo: gr.Blocks, app: FastAPI):
    @app.get("/install/{id}")
    async def install(id: str):
        to_install = civitai.get_model_version(id)
        print("Civitai Installing: " + to_install['name'])
        url = to_install['downloadUrl']
        type = to_install['type']
        task = asyncio.create_task(civitai.download(url, type))
        return {"status": "success"}

try:
    api_enabled = shared.cmd_options.civitai_api
except:
    api_enabled = False

if api_enabled:
    script_callbacks.on_app_started(civitaiAPI)
    print("Civitai API loaded")