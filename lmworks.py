from torch import tensor, no_grad, softmax
from helper import cfg, group_into_sentences
from os import path as px
import sys
from torch import cuda

sys.path.append(str(px.dirname(__file__)))
from bin.transformers_o import pipeline, AutoModelForCausalLM, RobertaTokenizerFast


modelname = cfg["model"]
cuda = cuda.is_available()
if cuda:
    model = AutoModelForCausalLM.from_pretrained(modelname).to(0)
    unmasker = pipeline('fill-mask', model=modelname, top_k=11, device=0)
else:
    model = AutoModelForCausalLM.from_pretrained(modelname)
    unmasker = pipeline('fill-mask', model=modelname, top_k=11)
tokenizer = RobertaTokenizerFast.from_pretrained(modelname, add_prefix_space=True, max_len=256, pad_token="<pad>", unk_token="<unk>", mask_token="<mask>", pad_to_max_length=True)
#tokenizer =  RobertaTokenizerFast(tokenizer_file=modelname+"/tokenizer.json", add_prefix_space=True, max_len=514, pad_token="<pad>", unk_token="<unk>", mask_token="<mask>", pad_to_max_length=True)                              
max_length=tokenizer.model_max_length

def fill_mask(text):
    if "<mask>" in text:
        return unmasker(text)
    return []


def visualize(text):
    vals, tokens = inspect(text)
    return vals, tokens


def prepare_batches(words):
    sentences = group_into_sentences(words)
    token_word = []
    grouped_tokens = []
    current_tokens = []
    current_length = 0

    i=0
    for sentence in sentences:
        for word in sentence:
            toks = tokenizer.tokenize(word)
            for t in toks:
                token_word.append(i)
            if current_length + len(toks) > max_length:
                grouped_tokens.append(current_tokens)
                current_tokens = toks
                current_length = len(toks)
            else:
                current_tokens.extend(toks)
                current_length += len(toks)
            i+=1

    if current_tokens:
        grouped_tokens.append(current_tokens)

    bathces = [tokenizer.convert_tokens_to_ids(x) for x in grouped_tokens]

    return bathces, token_word


def inspect(words, prior_probs=None, prior_influence=0.5, mp=800):
    if isinstance(words, str):
        words = words.rstrip().replace("\n", " ")
        words = [" " + x if i>0 else x for i, x in enumerate(words.split())]

    bathces, token_word = prepare_batches(words)

    vals = []

    for token_ids in bathces:
        print(len(token_ids))
        for i, token_id in enumerate(token_ids):
            input_ids = tensor(token_ids).unsqueeze(0)
            if cuda:
                input_ids = input_ids.to(0)
            labels = input_ids.clone()
            input_ids[0, i] = tokenizer.mask_token_id 

            with no_grad():
                outputs = model(input_ids, labels=labels)
                logits = outputs.logits

            probs = softmax(logits[0, i], dim=-1)
            token_prob = probs[token_id].item()
            vals.append(1/token_prob)
    
    word_vals = []
    for i, word in enumerate(words):
        wv = [vals[j] for j, x in enumerate(token_word) if x==i]
        word_vals.append(sum(wv)/len(wv))

    vals = [100*x/mp if x<mp else 100 for x in word_vals]
    if prior_probs:
        vals = vals
    return vals, words


