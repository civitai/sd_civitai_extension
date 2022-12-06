# main ui
import gradio as gr

import civitai.api as civitai

from modules import shared, sd_models, script_callbacks

def on_ui_tabs():
    with gr.Blocks() as civitai_interface:
        # Nav row with Civitai logo, search bar, sort, sort period, tag select, and creator select
        with gr.Row():
            gr.HTML("<h3>Civitai</h3>")
            with gr.Group():
                civitai_query = gr.Textbox(label="Search", default="")
                civitai_button_search = gr.Button(label="🔎");
            civitai_sort = gr.Dropdown(label="Sort", value="Most Downloaded", options=["Most Downloaded", "Most Recent", "Most Liked", "Most Viewed"])
            civitai_sort_period = gr.Dropdown(label="Sort Period", value="All Time", options=["All Time", "Last 30 Days", "Last 7 Days", "Last 24 Hours"])
            civitai_tag = gr.Dropdown(label="Tag", choices=["All", "Anime", "Cartoon", "Comic", "Game", "Movie", "Music", "Other", "Realistic", "TV"])
            civitai_creator = gr.Dropdown(label="Creator", choices=["All", "Anime", "Cartoon", "Comic", "Game", "Movie", "Music", "Other", "Realistic", "TV"])
        # Model list
        with gr.Row():
            gr.Gallery()
        # Pagination
        with gr.Row():
            civitai_button_prev = gr.Button(label="Previous")
            civitai_current_page = gr.HTML("<h3>Page 1 of 1</h3>")
            civitai_button_next = gr.Button(label="Next")

        # Handle button clicks
        # Handle dropdown changes


script_callbacks.on_ui_tabs(on_ui_tabs)