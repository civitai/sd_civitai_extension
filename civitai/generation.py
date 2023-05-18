# api endpoints
from modules import shared
from modules.api.api import encode_pil_to_base64, validate_sampler_name
from modules.api.models import StableDiffusionTxt2ImgProcessingAPI, TextToImageResponse
from modules.processing import StableDiffusionProcessingTxt2Img, process_images
from modules.call_queue import queue_lock

from civitai.models import CommandImageTxt2Img
import civitai.lib as lib

def internal_txt2img(txt2imgreq: StableDiffusionTxt2ImgProcessingAPI):
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
    args.pop('script_args', None) # will refeed them to the pipeline directly after initializing them
    args.pop('alwayson_scripts', None)

    send_images = args.pop('send_images', True)
    args.pop('save_images', None)

    with queue_lock:
        p = StableDiffusionProcessingTxt2Img(sd_model=shared.sd_model, **args)

        shared.state.begin()
        processed = process_images(p)
        shared.state.end()

    b64images = list(map(encode_pil_to_base64, processed.images)) if send_images else []

    return TextToImageResponse(images=b64images, parameters=vars(txt2imgreq), info=processed.js())

def txt2img(command: CommandImageTxt2Img):
    # TODO: Add support for VAEs
    # if (command['vae'] is None): lib.clear_vae()

    if (command['model'] is not None): lib.select_model({ 'hash': command['model'] })
    # if (command['vae'] is not None): lib.select_vae(command['vae'])

    return internal_txt2img(
        StableDiffusionTxt2ImgProcessingAPI(
            prompt=command['params']['prompt'],
            negative_prompt=command['params']['negativePrompt'],
            seed=command['params']['seed'],
            steps=command['params']['steps'],
            width=command['params']['width'],
            height=command['params']['height'],
            cfg_scale=command['params']['cfgScale'],
            clip_skip=command['params']['clipSkip'],
            n_iter=command['quantity'],
            batch_size=command['batchSize'],
        )
    )