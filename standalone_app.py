import gradio as gr
import os
import json
import random
import re
import sys
import os

# Set proxy settings
os.environ['http_proxy'] = 'http://127.0.0.1:2334'
os.environ['https_proxy'] = 'http://127.0.0.1:2334'
os.environ['no_proxy'] = 'localhost,127.0.0.1'
# Import translation modules
try:
    from transerver import Translator, baidu, freebd, llmTranslate, llm
except ImportError:
    transerver_path = os.path.join(os.path.dirname(__file__), "transerver")
    sys.path.append(transerver_path)
    from scripts.transerver import Translator, baidu, freebd, llmTranslate, llm 

# Setup paths
current_script = os.path.realpath(__file__)
current_folder = os.path.dirname(current_script)
work_basedir = current_folder
path1 = os.path.join(work_basedir, "json")
path2 = os.path.join(work_basedir, "yours")

transObj = {}

def load_tags_file():
    dic = {}
    load_json_files(path1, dic)
    load_json_files(path2, dic)
    return dic

def load_json_files(path, dic):
    files = os.listdir(path)
    for item in files:
        if item.endswith(".json"):
            filepath = os.path.join(path, item)
            filename = os.path.splitext(os.path.basename(filepath))[0]
            with open(filepath, "r", encoding="utf-8-sig") as f:
                res = json.load(f)
                dic[filename] = res

def contains_chinese(s):
    pattern = re.compile(r'[\u4e00-\u9fff]+')
    return bool(pattern.search(s))

def translate(text):
    if transObj['server'] == 'free':
        trans_server = freebd.FreeBDTranslator()
        return Translator.translate_text(trans_server, text)
    elif transObj['server'] == 'llm':
        trans_server = llmTranslate.LLMTranslator()
        return Translator.translate_text(trans_server, text, transObj)
    elif transObj['server'] == 'baidu':
        trans_server = baidu.BaiduTranslator()
        return Translator.translate_text(trans_server, transObj['appid'], transObj['secret'], text)

def extract_tags(text):
    pattern = r'#\[(.*?)\]'
    matches = re.findall(pattern, text)
    for i in matches:
        newarr = i.split(',')
        random.seed(random.random())
        rdindex = random.randint(0, len(newarr)-1)
        rdtext = newarr[rdindex]
        text = re.sub(pattern, rdtext, text, count=1)
    return text

def process_prompt(prompt, negative_prompt):
    prompt = extract_tags(prompt)
    negative_prompt = extract_tags(negative_prompt)
    
    if contains_chinese(prompt):
        prompt = translate(prompt)
    if contains_chinese(negative_prompt):
        negative_prompt = translate(negative_prompt)
    
    return prompt, negative_prompt

def generate_image(prompt, negative_prompt):
    processed_prompt, processed_negative_prompt = process_prompt(prompt, negative_prompt)
    return f"Processed prompt: {processed_prompt}\nProcessed negative prompt: {processed_negative_prompt}"

def set_translation_server(server, appid="", secret="", llm_name=""):
    global transObj
    transObj = {
        'server': server,
        'appid': appid,
        'secret': secret,
        'llmName': llm_name
    }
    return "Translation server settings updated."

def test_translation():
    trans_text = translate('苹果')
    return 'Translation working' if trans_text.lower() == 'apple' else 'Translation failed'

def imagine_prompt(prompt):
    return llm.chat_imagine(prompt, transObj)

def search_prompts(search_term, prompts_dict):
    results = []
    for category, subcategories in prompts_dict.items():
        for subcategory, prompts in subcategories.items():
            for prompt, translation in prompts.items():
                if search_term.lower() in prompt.lower() or search_term.lower() in translation.lower():
                    results.append(f"{category} - {subcategory}: {prompt} ({translation})")
    return "\n".join(results)

def random_prompt(prompts_dict):
    category = random.choice(list(prompts_dict.keys()))
    subcategory = random.choice(list(prompts_dict[category].keys()))
    prompt = random.choice(list(prompts_dict[category][subcategory].keys()))
    return f"{category} - {subcategory}: {prompt} ({prompts_dict[category][subcategory][prompt]})"

def truncate_text(text, max_length=20):
    return text if len(text) <= max_length else text[:max_length-3] + "..."

css = """
.gr-box {
    border: none !important;
    background-color: transparent !important;
    margin-bottom: 1em;
}
.gr-button {
    margin: 0.2em;
    min-width: 0;
    max-width: 100%;
    height: auto;
    padding: 0.2em 0.4em;
    font-size: 0.9em;
    background-color: #3a3b3c;
    color: white;
    border: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.gr-button:hover {
    background-color: #4a4b4c;
}
.gr-markdown {
    margin-bottom: 0.5em;
}
.prompt-grid-wrapper {
    display: grid;
    grid-template-columns: repeat(8, minmax(0, 1fr));
    gap: 0.5em;
    max-width: 1200px; /* Adjust this value as needed */
    width: 100%;
    margin: 0 auto;
}
"""

# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="blue"), css=css) as app:
    gr.Markdown("# Old Six Prompt Generator")
    
    prompts_dict = load_tags_file()
    
    with gr.Row():
        with gr.Column(scale=2):
            prompt_input = gr.Textbox(label="Positive Prompt", lines=5)
            negative_prompt_input = gr.Textbox(label="Negative Prompt", lines=5)
        with gr.Column(scale=1):
            generate_btn = gr.Button("Generate")
            output = gr.Textbox(label="Output", lines=5)
    
    with gr.Tabs() as tabs:
        for category, subcategories in prompts_dict.items():
            with gr.Tab(category):
                for subcategory, prompts in subcategories.items():
                    gr.Markdown(f"### {subcategory}")
                    with gr.Row(elem_classes=["prompt-grid-wrapper"]):
                        for prompt, translation in prompts.items():
                            truncated_prompt = truncate_text(prompt)
                            truncated_translation = truncate_text(translation)
                            gr.Button(f"{truncated_prompt} ({truncated_translation})", size="sm")
    
    with gr.Row():
        search_input = gr.Textbox(label="Search Prompts")
        search_output = gr.Textbox(label="Search Results", lines=5)
        search_btn = gr.Button("Search")
    
    with gr.Row():
        random_btn = gr.Button("Random Prompt")
        random_output = gr.Textbox(label="Random Prompt")
    
    with gr.Accordion("Settings"):
        server_dropdown = gr.Dropdown(["free", "llm", "baidu"], label="Translation Server")
        appid_input = gr.Textbox(label="App ID (for Baidu)")
        secret_input = gr.Textbox(label="Secret (for Baidu)")
        llm_name_input = gr.Textbox(label="LLM Name (for LLM)")
        set_server_btn = gr.Button("Set Translation Server")
        server_output = gr.Textbox(label="Server Status")
    
    generate_btn.click(generate_image, inputs=[prompt_input, negative_prompt_input], outputs=output)
    set_server_btn.click(set_translation_server, 
                         inputs=[server_dropdown, appid_input, secret_input, llm_name_input], 
                         outputs=server_output)
    search_btn.click(search_prompts, inputs=[search_input, gr.State(prompts_dict)], outputs=search_output)
    random_btn.click(random_prompt, inputs=[gr.State(prompts_dict)], outputs=random_output)

if __name__ == "__main__":
    app.launch()