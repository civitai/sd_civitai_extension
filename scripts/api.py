# api endpoints
import asyncio
import gradio as gr
from fastapi import FastAPI

from modules import shared, script_callbacks as script_callbacks
from modules.hypernetworks import hypernetwork
from modules.api.api import encode_pil_to_base64, validate_sampler_name
from modules.api.models import StableDiffusionTxt2ImgProcessingAPI, TextToImageResponse
from modules.processing import StableDiffusionProcessingTxt2Img, process_images
from modules.sd_models import checkpoints_list
from modules.call_queue import queue_lock
from typing import List

import extensions.sd_civitai_extension.civitai.lib as civitai
from extensions.sd_civitai_extension.civitai.models import GenerateImageRequest, ResourceRequest

def civitaiAPI(demo: gr.Blocks, app: FastAPI):
    # To detect if the API is loaded
    @app.get("/civitai/v1")
    async def index():
        return {"status": "success"}

    # To get a list of resources available
    @app.get("/civitai/v1/resources")
    async def get_resources():
        models = [{"name":x.model_name, "hash":x.sha256, "type":"Checkpoint"} for x in checkpoints_list.values()]
        hypernetworks = [civitai.parse_hypernetwork(name) for name in shared.hypernetworks]
        return models + hypernetworks

    # To activate a list of resources
    @app.post("/civitai/v1/resources")
    async def set_resources(resources: List[ResourceRequest]):
        for resource in resources:
            await asyncio.create_task(civitai.load_resource(resource))

        return {"status": "success"}


    # To download and select a model
    # @app.post("/civitai/v1/run/{id}")
    # async def run(id: str):
    #     to_run = civitai.get_model_version(id)
    #     to_run_name = f'{to_run["model"]["name"]} {to_run["name"]}'
    #     civitai.log(f'Running: {to_run_name}')
    #     primary_file = [x for x in to_run['files'] if x['primary'] == True][0]
    #     name = primary_file['name']
    #     hash = primary_file['hashes']['AutoV1']
    #     url = to_run['downloadUrl']
    #     type = to_run['model']['type']
    #     if type == 'Checkpoint':
    #         try:
    #             config_file = [x for x in to_run['files'] if x['type'] == "Config"][0]
    #             await asyncio.create_task(civitai.load_config(config_file['name'], config_file['downloadUrl']))
    #         except IndexError: config_file = None
    #         await asyncio.create_task(civitai.load_model(name, url))
    #     elif type == 'TextualInversion': await asyncio.create_task(civitai.download_textual_inversion(name, url))
    #     elif type == 'AestheticGradient': await asyncio.create_task(civitai.download_aesthetic_gradient(name, url))
    #     elif type == 'Hypernetwork': await asyncio.create_task(civitai.load_hypernetwork(name, url))

    #     civitai.log(f'Loaded: {to_run_name}')
    #     return {"status": "success"}

    def txt2img(txt2imgreq: StableDiffusionTxt2ImgProcessingAPI):
        populate = txt2imgreq.copy(update={ # Override __init__ params
            "sampler_name": validate_sampler_name(txt2imgreq.sampler_name or txt2imgreq.sampler_index),
            "do_not_save_samples": True,
            "do_not_save_grid": True
            }
        )
        if populate.sampler_name:
            populate.sampler_index = None  # prevent a warning later on

        args = vars(populate)
        args.pop('script_name', None)

        with queue_lock:
            p = StableDiffusionProcessingTxt2Img(sd_model=shared.sd_model, **args)

            shared.state.begin()
            processed = process_images(p)
            shared.state.end()

        b64images = list(map(encode_pil_to_base64, processed.images))

        return TextToImageResponse(images=b64images, parameters=vars(txt2imgreq), info=processed.js())

    @app.post("/civitai/v1/generate/image", response_model=TextToImageResponse)
    async def generate_image(req: GenerateImageRequest):
        if (req.vae is None): civitai.clear_vae()
        if (req.hypernetwork is None): civitai.clear_hypernetwork()

        if (req.model is not None): await asyncio.create_task(civitai.load_model(req.model))
        if (req.hypernetwork is not None):
            await asyncio.create_task(civitai.load_hypernetwork(req.hypernetwork))
            hypernetwork.apply_strength(req.params.hypernetworkStrength)
        if (req.vae is not None): await asyncio.create_task(civitai.load_vae(req.vae))

        return txt2img(
            StableDiffusionTxt2ImgProcessingAPI(
                prompt=req.params.prompt,
                negative_prompt=req.params.negativePrompt,
                seed=req.params.seed,
                steps=req.params.steps,
                width=req.params.width,
                height=req.params.height,
                cfg_scale=req.params.cfgScale,
                n_iter=req.quantity,
                batch_size=req.batchSize,
            )
        )

script_callbacks.on_app_started(civitaiAPI)
civitai.log("API loaded")
