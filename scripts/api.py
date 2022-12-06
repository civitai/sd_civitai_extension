# api endpoints
import asyncio
import gradio as gr
from fastapi import FastAPI

from modules import shared, script_callbacks as script_callbacks

from civitai.api import get_model_version, download

def civitaiAPI(demo: gr.Blocks, app: FastAPI):
    @app.get("/install/{id}")
    async def install(id: str):
        to_install = get_model_version(id)
        print("Civitai Installing: " + to_install['name'])
        url = to_install['downloadUrl']
        type = to_install['type']
        task = asyncio.create_task(download(url, type))
        return {"status": "success"}

try:
    api_enabled = shared.cmd_options.civitai_api
except:
    api_enabled = False

if api_enabled:
    script_callbacks.on_app_started(civitaiAPI)
    print("Civitai API loaded")