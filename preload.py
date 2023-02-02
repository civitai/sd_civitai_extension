# loaded before parsing commandline args
import argparse

def preload(parser: argparse.ArgumentParser):
    parser.add_argument("--civitai-endpoint", type=str, help="Endpoint for interacting with a Civitai instance", default="https://civitai.com/api/v1")
    parser.add_argument("--civitai-link-endpoint", type=str, help="Endpoint for interacting with a Civitai Link server", default="https://link.civitai.com/api/socketio")