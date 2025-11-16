from fastapi import FastAPI, Request
from transformers import pipeline
import torch
import sys
import os
sys.path.append(os.path.abspath("C:/Users/A200348545/Escritorio 2/Personal-Projects/IOG"))
sys.path.append(os.path.abspath("C:/Users/A200348545/Escritorio 2/Personal-Projects/IOG/pyfuncs"))
from credentials import Credentials
from summarizer import *
credentials = Credentials()
os.environ["http_proxy"] = credentials.http_proxy
os.environ["https_proxy"] = credentials.https_proxy

app = FastAPI()


# Load model on GPU if available
tokenizer, model = load_tokenizer_and_model()
device = torch.device("cuda")
model = model.to(device)

# Setting summparams
summparams = SummParams(
    text = "",
    tokenizer = tokenizer,
    model = model,
    num_beans = 6,
    max_input_length = 1024,
    min_output_length = 20,
    max_output_length= 200,
    device = device
)

@app.post("/summarizer/summarize")
async def generate(request: Request):
    data = await request.json()
    prompt = data.get("text", "")
    summparams.text = prompt
    result = summarize_text(summparams)
    return {"summary": result}
