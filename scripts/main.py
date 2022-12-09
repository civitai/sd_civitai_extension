# main ui
import gradio as gr

import extensions.sd_civitai_extension.civitai.api as civitai

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
            civitai_page = gr.Number(visible=False, value=1)
            civitai_page_size = gr.Number(visible=False, default=20)
        # Model list
        with gr.Row():
            model_output = gr.HTML()
        # Pagination
        with gr.Row():
            civitai_button_prev = gr.Button(label="Previous")
            civitai_current_page = gr.HTML("<h3>Page 1 of 1</h3>")
            civitai_button_next = gr.Button(label="Next")

        # Dummy Elements
        download_model_version_id = gr.Number(visible=False, value=0, elem_id="download_model_version_id")
        download_model_button = gr.Button(label="Download", visible=False, elem_id="download_model_button")

    # Handle button clicks
    civitai_button_search.click(fn=search_models, inputs=[civitai_query, civitai_sort, civitai_sort_period, civitai_tag, civitai_creator, civitai_page, civitai_page_size], outputs=[model_output, civitai_current_page])
    civitai_button_prev.click(fn=prev_page, inputs=[civitai_page], outputs=[civitai_page])
    civitai_button_next.click(fn=next_page, inputs=[civitai_page], outputs=[civitai_page])

    # Handle dropdown changes
    civitai_tag.change(fn=search_models, inputs=[civitai_query, civitai_sort, civitai_sort_period, civitai_tag, civitai_creator, civitai_page, civitai_page_size], outputs=[model_output, civitai_current_page])
    civitai_sort.change(fn=search_models, inputs=[civitai_query, civitai_sort, civitai_sort_period, civitai_tag, civitai_creator, civitai_page, civitai_page_size], outputs=[model_output, civitai_current_page])
    civitai_sort_period.change(fn=search_models, inputs=[civitai_query, civitai_sort, civitai_sort_period, civitai_tag, civitai_creator, civitai_page, civitai_page_size], outputs=[model_output, civitai_current_page])
    civitai_creator.change(fn=search_models, inputs=[civitai_query, civitai_sort, civitai_sort_period, civitai_tag, civitai_creator, civitai_page, civitai_page_size], outputs=[model_output, civitai_current_page])
    civitai_page.change(fn=search_models, inputs=[civitai_query, civitai_sort, civitai_sort_period, civitai_tag, civitai_creator, civitai_page, civitai_page_size], outputs=[model_output, civitai_current_page])
    civitai_page_size.change(fn=search_models, inputs=[civitai_query, civitai_sort, civitai_sort_period, civitai_tag, civitai_creator, civitai_page, civitai_page_size], outputs=[model_output, civitai_current_page])


script_callbacks.on_ui_tabs(on_ui_tabs)