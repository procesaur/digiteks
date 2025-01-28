from torch import tensor, no_grad, softmax
from helper import cfg, group_into_sentences, lat2cyr, find_most_similar_word
from os import path as px
import sys
from torch import cuda, topk, stack

sys.path.append(str(px.dirname(__file__)))
from bin.transformers_o import pipeline, AutoModelForCausalLM, RobertaTokenizerFast


modelname = cfg["model"]
batch_size = cfg["batch_size"]
reasonable_doubt = cfg["reasonable_doubt_index"]
max_perplexity = cfg["max_perplexity"]
top_k = cfg["top_k"]
cuda = cuda.is_available() and cfg["cuda"]

tokenizer = RobertaTokenizerFast.from_pretrained(modelname, add_prefix_space=True, max_len=512, pad_token="<pad>", unk_token="<unk>", mask_token="<mask>", pad_to_max_length=True)
if cuda:
    model = AutoModelForCausalLM.from_pretrained(modelname).to(0)
else:
    model = AutoModelForCausalLM.from_pretrained(modelname)
model.eval()

prefix = [".", "-"]
max_length=tokenizer.model_max_length - len(prefix) - 2
if max_length > cfg["context_size"]:
    max_length = cfg["context_size"]


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
            token_word += [i for x in toks]
            if current_length + len(toks) > max_length-2:
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


def lm_inspect(words, max_perplexity=max_perplexity):
    if isinstance(words, str):
        words = words.rstrip().replace("\n", " ")
        words = words.split()
    
    if not words:
        return [], []

    perplexities = []
    words_conf = []

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

            for j in range(batch_input_ids.size(0)):
                masked_index = (batch_input_ids[j] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
                masked_logits = outputs.logits[j, masked_index, :]
                original_token_prob = softmax(masked_logits, dim=0)[input_ids[i + j]].item()
                perplexities.append(1/original_token_prob)

    for i in range(len(words)):
        wv = [perplexities[j] for j, x in enumerate(token_word) if x==i]
        words_conf.append(sum(wv)/len(wv))

    words_conf = [1-x/max_perplexity if x<max_perplexity else 0 for x in words_conf]
    return words_conf, words


def confidence_rework(ocr_confs, lm_confs, rdi=1-reasonable_doubt):
    return [(y*rdi)**(1-x) for x, y in zip(ocr_confs, lm_confs)]


def lm_fix_words(words, confs):
    token_batches, token_word = prepare_batches(words)
    for_inspection = [i for i, x in enumerate(confs) if x < cfg["min_conf"]]
    input_ids_list = create_batches_to_fix(token_batches, token_word, for_inspection)
    all_predictions= []
    results = []

    for i in range(0, len(input_ids_list), batch_size):
        if cuda:
            batch_input_ids = stack(input_ids_list[i:i + batch_size]).to(0)
        else:
            batch_input_ids = stack(input_ids_list[i:i + batch_size])
        with no_grad():
            outputs = model(batch_input_ids)

        for j in range(batch_input_ids.size(0)):
            masked_index = (batch_input_ids[j] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
            masked_logits = outputs.logits[j, masked_index, :]
            top_k_indices = topk(masked_logits, top_k, dim=0).indices.tolist()
            top_k_tokens = [tokenizer.decode([token_id]) for token_id in top_k_indices]
            all_predictions.append(top_k_tokens)

    inspection_prediction = {x : y for x, y in zip(for_inspection, all_predictions)}
    for i, word in enumerate(words):
        if i not in inspection_prediction.keys():
            results.append(word)
        elif word in inspection_prediction[i]:
            results.append(word)
        else:
            predictions = [lat2cyr(x) for x in inspection_prediction[i]]
            results.append(find_most_similar_word(word, predictions))
    return results


def create_batches_to_fix(token_batches, token_word, for_inspection):
    masked_contexts = []
    tokenized_inputs = [token for batch in token_batches for token in batch]

    for index in for_inspection:
        word_tokens = [idx for idx, word_idx in enumerate(token_word) if word_idx == index]
        
        masked_context = tokenized_inputs[:]
        mask_start = word_tokens[0]
        mask_end = word_tokens[-1] + 1
        masked_context[mask_start:mask_end] = [tokenizer.mask_token_id]

        context_start = max(0, mask_start - (max_length-5) // 2)
        context_end = min(len(masked_context), mask_end + (max_length-5) // 2)
        masked_context = masked_context[context_start:context_end]
        masked_contexts.append(tensor(masked_context))

    return masked_contexts
