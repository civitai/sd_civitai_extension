from enum import Enum
from typing import List
from pydantic import BaseModel, Field

class ResourceTypes(str, Enum):
    Checkpoint = "Checkpoint"
    CheckpointConfig = "CheckpointConfig"
    TextualInversion = "TextualInversion"
    AestheticGradient = "AestheticGradient"
    Hypernetwork = "Hypernetwork"
    LORA = "LORA"
    VAE = "VAE"

class CommandTypes(str, Enum):
    ActivitiesList = "activities:list"
    ActivitiesCancel = "activities:cancel"
    ResourcesList = "resources:list"
    ResourcesAdd = "resources:add"
    ResourcesRemove = "resources:remove"

class ImageParams(BaseModel):
    prompt: str = Field(default="", title="Prompt", description="The prompt to use when generating the image.")
    negativePrompt: str = Field(default="", title="Negative Prompt", description="The negative prompt to use when generating the image.")
    sampler: str = Field(default="Euler a", title="Sampler", description="The sampler to use when generating the image.")
    seed: int = Field(default=-1, title="Seed", description="The seed to use when generating the image.")
    steps: int = Field(default=30, title="Steps", description="The number of steps to use when generating the image.")
    width: int = Field(default=512, title="Width", description="The width of the image to generate.")
    height: int = Field(default=512, title="Height", description="The height of the image to generate.")
    cfgScale: float = Field(default=7.5, title="Scale", description="The guidance scale for image generation.")


class GenerateImageRequest(BaseModel):
    quantity: int = Field(default=1, title="Quantity", description="The number of images to generate.")
    batchSize: int = Field(default=1, title="Batch Size", description="The number of images to generate in each batch.")
    model: str = Field(default=None, title="Model", description="The hash of the model to use when generating the images.")
    vae: str = Field(default=None, title="VAE", description="The hash of the VAE to use when generating the images.")
    params: ImageParams = Field(default=ImageParams(), title="Parameters", description="The parameters to use when generating the images.")

class ResourceRequest(BaseModel):
    name: str = Field(default=None, title="Name", description="The name of the resource to download.")
    type: ResourceTypes = Field(default=None, title="Type", description="The type of the resource to download.")
    hash: str = Field(default=None, title="Hash", description="The SHA256 hash of the resource to download.")
    url: str = Field(default=None, title="URL", description="The URL of the resource to download.", required=False)
    previewImage: str = Field(default=None, title="Preview Image", description="The URL of the preview image.", required=False)

class RoomPresence(BaseModel):
    client: int = Field(default=None, title="Clients", description="The number of clients in the room")
    sd: int = Field(default=None, title="Stable Diffusion Clients", description="The number of Stable Diffusion Clients in the room")

class Command(BaseModel):
    id: str = Field(default=None, title="ID", description="The ID of the command.")
    type: CommandTypes = Field(default=None, title="Type", description="The type of command to execute.")

class CommandActivitiesList(Command):
    type: CommandTypes = Field(default=CommandTypes.ActivitiesList, title="Type", description="The type of command to execute.")

class CommandResourcesList(Command):
    type: CommandTypes = Field(default=CommandTypes.ResourcesList, title="Type", description="The type of command to execute.")
    types: List[ResourceTypes] = Field(default=[], title="Types", description="The types of resources to list.")

class CommandResourcesAdd(Command):
    type: CommandTypes = Field(default=CommandTypes.ResourcesAdd, title="Type", description="The type of command to execute.")
    resource: ResourceRequest = Field(default=[], title="Resource", description="The resources to add.")

class ResourceCancelRequest(BaseModel):
    type: ResourceTypes = Field(default=None, title="Type", description="The type of the resource to remove.")
    hash: str = Field(default=None, title="Hash", description="The SHA256 hash of the resource to remove.")

class CommandActivitiesCancel(Command):
    type: CommandTypes = Field(default=CommandTypes.ActivitiesCancel, title="Type", description="The type of command to execute.")

class ResourceRemoveRequest(BaseModel):
    type: ResourceTypes = Field(default=None, title="Type", description="The type of the resource to remove.")
    hash: str = Field(default=None, title="Hash", description="The SHA256 hash of the resource to remove.")

class CommandResourcesRemove(Command):
    type: CommandTypes = Field(default=CommandTypes.ResourcesRemove, title="Type", description="The type of command to execute.")
    resource: ResourceRemoveRequest = Field(default=[], title="Resource", description="The resources to remove.")

class CommandImageTxt2Img(Command):
    quantity: int = Field(default=1, title="Quantity", description="The number of images to generate.")
    batchSize: int = Field(default=1, title="Batch Size", description="The number of images to generate in each batch.")
    model: str = Field(default=None, title="Model", description="The hash of the model to use when generating the images.")
    vae: str = Field(default=None, title="VAE", description="The hash of the VAE to use when generating the images.")
    params: ImageParams = Field(default=ImageParams(), title="Parameters", description="The parameters to use when generating the images.")

class UpgradeKeyPayload(BaseModel):
    key: str = Field(default=None, title="Key", description="The upgraded key.")

class ErrorPayload(BaseModel):
    msg: str = Field(default=None, title="Message", description="The error message.")

class JoinedPayload(BaseModel):
    type: str = Field(default=None, title="Type", description="The type of the client that joined.")