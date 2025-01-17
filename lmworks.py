from torch import tensor, no_grad, softmax
from helper import cfg
from os import path as px
import sys
from torch import cuda

sys.path.append(str(px.dirname(__file__)))
from bin.transformers_o import pipeline, AutoModelForCausalLM, RobertaTokenizerFast


modelname = cfg["model"]
devicex = 0 if cuda.is_available() else -1

model = AutoModelForCausalLM.from_pretrained(modelname).to(devicex)
unmasker = pipeline('fill-mask', model=modelname, top_k=11, device=devicex) 
tokenizer = RobertaTokenizerFast.from_pretrained(modelname)
#tokenizer =  RobertaTokenizerFast(tokenizer_file=modelname+"/tokenizer.json", add_prefix_space=True, max_len=514, pad_token="<pad>", unk_token="<unk>", mask_token="<mask>", pad_to_max_length=True)                              


def fill_mask(text):
    if "<mask>" in text:
        return unmasker(text)
    return []


def visualize(text):
    vals, tokens = inspect(text)
    return vals, tokens


def inspect(text, mp=800):
    text = text.rstrip().replace("\n", " ")
    words = [" " + x if i>0 else x for i, x in enumerate(text.split())]
    tokens = []
    token_word = []
    for i, word in enumerate(words):
        toks = tokenizer.tokenize(word)
        tokens+=toks
        for t in toks:
            token_word.append(i)
    token_ids = tokenizer.convert_tokens_to_ids(tokens)
    vals = []

    for i, token_id in enumerate(token_ids):
        input_ids =  tensor(token_ids).unsqueeze(0).to(devicex)
        labels = input_ids.clone()
        input_ids[0, i] = tokenizer.mask_token_id 

        with no_grad():
            outputs = model(input_ids, labels=labels)
            logits = outputs.logits

        probs = softmax(logits[0, i], dim=-1)
        token_prob = probs[token_id].item()
        vals.append(1/token_prob)
    
    if len(words)<len(tokens):
        word_vals = []
        for i, word in enumerate(words):
            wv = [vals[j] for j, x in enumerate(token_word) if x==i]
            word_vals.append(sum(wv)/len(wv))

        vals = [100*x/mp if x<mp else 100 for x in word_vals]

    return vals, words

