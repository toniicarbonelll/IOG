from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os
import numpy as np
import re
from dataclasses import dataclass
import time
import torch


def load_tokenizer_and_model():
    tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
    model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")
    return tokenizer, model


@dataclass
class SummParams:
    text: str
    tokenizer: AutoTokenizer
    model: AutoModelForSeq2SeqLM
    num_beans: int = 6
    max_input_length: int = 1024
    min_output_length: int = 20
    max_output_length: int = 200
    device: torch.device = torch.device("cuda")


def summarize_text(summparams: SummParams) -> str:
    """Summarizes text

    Args:
        summparams (SummParams): Parameters for text summarization (dataclass)

    Returns:
        str: Summarized text
    """
    inputs = summparams.tokenizer([summparams.text], max_length=summparams.max_input_length, return_tensors='pt').to(summparams.device)
    summary_ids = summparams.model.generate(inputs['input_ids'], num_beams=summparams.num_beans, min_length=summparams.min_output_length, max_length=summparams.max_output_length, early_stopping=True)
    return (summparams.tokenizer.decode(summary_ids[0], skip_special_tokens=True, truncation=True))