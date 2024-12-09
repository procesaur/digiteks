
from torch import tensor, no_grad, softmax
from helper import cfg
from os import path as px
import sys

path_root = px.dirname(__file__)
sys.path.append(str(path_root))
from bin.transformers_o import pipeline, AutoModelForCausalLM, RobertaTokenizerFast


devicex = cfg["device"]
modelname = cfg["model"]

def tensor2device(tensor, print_dev=False):
    tensor = tensor.to(devicex)
    if print_dev:
        print(devicex)
    return tensor


unmasker = pipeline('fill-mask', model=modelname, top_k=11, device=devicex ) 
model = tensor2device(AutoModelForCausalLM.from_pretrained(modelname))
tokenizer = RobertaTokenizerFast.from_pretrained(modelname)
#tokenizer =  RobertaTokenizerFast(tokenizer_file=modelname+"/tokenizer.json", add_prefix_space=True, max_len=514, pad_token="<pad>", unk_token="<unk>", mask_token="<mask>", pad_to_max_length=True)                              


def fill_mask(text):
    if "<mask>" in text:
        return unmasker(text)
    return []


def visualize(text):
    vals, tokens = inspect(text)
    return vals, tokens


def inspect(text):
    tokens = tokenizer.tokenize(text)
    words = [" " + x for x in text.split()]
    token_ids = tokenizer.convert_tokens_to_ids(tokens)
    vals = []

    for i, token_id in enumerate(token_ids):
        input_ids =  tensor2device(tensor(token_ids).unsqueeze(0))
        labels = input_ids.clone()
        input_ids[0, i] = tokenizer.mask_token_id 

        with no_grad():
            outputs = model(input_ids, labels=labels)
            logits = outputs.logits

        probs = softmax(logits[0, i], dim=-1)
        token_prob = probs[token_id].item()
        vals.append(1/token_prob)

    return vals, tokens


def text2tokentensors(tokenizer, text):
    tokens_tensor = tokenizer.encode(text, add_special_tokens=True, return_tensors="pt")
    tokens_tensor = tensor2device(tokens_tensor)
    return tokens_tensor

