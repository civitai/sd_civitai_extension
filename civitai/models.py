from pydantic import BaseModel, Field

class ImageParams(BaseModel):
    prompt: str = Field(default="", title="Prompt", description="The prompt to use when generating the image.")
    negativePrompt: str = Field(default="", title="Negative Prompt", description="The negative prompt to use when generating the image.")
    sampler: str = Field(default="Euler a", title="Sampler", description="The sampler to use when generating the image.")
    seed: int = Field(default=-1, title="Seed", description="The seed to use when generating the image.")
    steps: int = Field(default=30, title="Steps", description="The number of steps to use when generating the image.")
    width: int = Field(default=512, title="Width", description="The width of the image to generate.")
    height: int = Field(default=512, title="Height", description="The height of the image to generate.")
    cfgScale: float = Field(default=7.5, title="Scale", description="The guidance scale for image generation.")
    hypernetworkStrength: float = Field(default=None, title="Hypernetwork Strength", description="The strength of the hypernetwork for image generation.")


class GenerateImageRequest(BaseModel):
    quantity: int = Field(default=1, title="Quantity", description="The number of images to generate.")
    batchSize: int = Field(default=1, title="Batch Size", description="The number of images to generate in each batch.")
    model: str = Field(default=None, title="Model", description="The hash of the model to use when generating the images.")
    vae: str = Field(default=None, title="VAE", description="The hash of the VAE to use when generating the images.")
    hypernetwork: str = Field(default=None, title="Hypernetwork", description="The hash of the hypernetwork to use when generating the images.")
    params: ImageParams = Field(default=ImageParams(), title="Parameters", description="The parameters to use when generating the images.")