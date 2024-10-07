from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from math import exp
from torch import cuda, device


devicex = device("cuda:0" if cuda.is_available() else "cpu")

def tensor2device(tensor, print_dev=False):
    tensor = tensor.to(devicex)
    if print_dev:
        print(devicex)
    return tensor

modelname = 'jerteh/jerteh-355'
unmasker = pipeline('fill-mask', model=modelname) 
model, tokenizer = tensor2device(AutoModelForCausalLM.from_pretrained(modelname)),AutoTokenizer.from_pretrained(modelname)


def fill_mask(text):
    if "<mask>" in text:
        return unmasker(text)
    return "нема маске у тексту"


def visualize(text, step=4, change=True):
    perp = round(perplexity(text), 3)
    vals, tokens = inspect(text, step, change)
    return perp, vals, tokens


def perplexity(text):
    tokens = text2tokentensors(tokenizer, text)
    if tokens.size()[1] > 1024:
        tokens = tokens.narrow(1, 0, 1024)
    outputs = model(tokens, labels=tokens)
    loss = outputs[0]
    perp = exp(loss)
    return perp


def inspect(text, step, change=True):
    tokens = text.split(" ")
    tl = len(tokens)

    if tl < step + 2:
        ini = perplexity(" ".join(tokens))
        vals = [ini for x in tokens]
        return vals, tokens

    togo = tokens[0:step]
    resto = tokens[step:tl]
    inp = " ".join(togo)
    ini = perplexity(inp)
    vals = [ini for x in togo]

    for i, r in enumerate(resto):

        vals.append(0)
        togo.pop(0)
        togo.append(r)
        inp = "".join(togo)
        ini = perplexity(inp)
        n = [ini for x in togo]

        for x in range(step):
            vals[x+i+1] += n[x]

    for i, v in enumerate(vals):
        if i < step:
            ddd = step - i
        elif i == step:
            ddd = 1
        else:
            ddd = step - tl + i + 1
        if ddd < 1:
            ddd = 1
        co = 1+step-ddd

        vals[i] = vals[i]/co

    return vals, tokens



def text2tokentensors(tokenizer, text):
    tokens_tensor = tokenizer.encode(text, add_special_tokens=False, return_tensors="pt")
    tokens_tensor = tensor2device(tokens_tensor)
    return tokens_tensor

    
