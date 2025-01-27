from torch import tensor, no_grad, softmax
from helper import cfg, group_into_sentences
from os import path as px
import sys
from torch import cuda, topk, stack, cat


sys.path.append(str(px.dirname(__file__)))
from bin.transformers_o import pipeline, AutoModelForCausalLM, RobertaTokenizerFast


modelname = cfg["model"]
cuda = cuda.is_available() and cfg["cuda"]

tokenizer = RobertaTokenizerFast.from_pretrained(modelname, add_prefix_space=True, max_len=512, pad_token="<pad>", unk_token="<unk>", mask_token="<mask>", pad_to_max_length=True)
if cuda:
    model = AutoModelForCausalLM.from_pretrained(modelname).to(0)
    unmasker = pipeline('fill-mask', model=model, top_k=11, device=0, tokenizer=tokenizer)
else:
    model = AutoModelForCausalLM.from_pretrained(modelname)
    unmasker = pipeline('fill-mask', model=model, top_k=11, tokenizer=tokenizer)

prefix = [".", "-"]
max_length=tokenizer.model_max_length - len(prefix) - 2
if max_length > cfg["context"]:
    max_length = cfg["context"]


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
            toks = tokenizer.tokenize(" " + word)
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

    grouped_tokens = [prefix + x for x in grouped_tokens]
    bathces = [tokenizer.convert_tokens_to_ids(x) for x in grouped_tokens]

    return bathces, token_word


def inspect(words, prior_probs=None, prior_influence=0.5, mp=800, top_k=10, batch_size=16):
    vals = []
    #all_predictions = [] 

    if isinstance(words, str):
        words = words.rstrip().replace("\n", " ")
        words = words.split()

    bathces, token_word = prepare_batches(words)

    for input_ids in bathces:
        input_ids_list = []
        

        for i in range(len(input_ids)):
            pl = len(prefix)
            if i >= pl:
                masked_input_ids = input_ids[:]
                masked_input_ids[i-pl] = tokenizer.mask_token_id
                input_ids_list.append(tensor(masked_input_ids))


        for i in range(0, len(input_ids_list), batch_size):
            if cuda:
                batch_input_ids = stack(input_ids_list[i:i + batch_size]).to(0)
            else:
                batch_input_ids = stack(input_ids_list[i:i + batch_size])

            with no_grad():
                outputs = model(batch_input_ids)
            logits = outputs.logits

            for j in range(batch_input_ids.size(0)):
                masked_index = (batch_input_ids[j] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
                masked_logits = logits[j, masked_index, :]  
                #top_k_indices = topk(masked_logits, top_k, dim=0).indices.tolist()
                #top_k_tokens = [tokenizer.decode([token_id]) for token_id in top_k_indices]
                #all_predictions.append((i + j, top_k_tokens))

                original_token_prob = softmax(masked_logits, dim=0)[input_ids[i + j]].item()
                vals.append(1/original_token_prob)

    word_vals = []
    for i, word in enumerate(words):
        wv = [vals[j] for j, x in enumerate(token_word) if x==i]
        word_vals.append(sum(wv)/len(wv))

    vals = [100*x/mp if x<mp else 100 for x in word_vals]
    vals = [x/100 for x in vals]
    if prior_probs:
        vals = vals
    return vals, words


