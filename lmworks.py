from torch import tensor, no_grad, softmax
from helper import cfg, group_into_sentences, lat2cyr, find_most_similar_word
from os import path as px
import sys
from torch import cuda, topk, stack, cat, long as tlong

sys.path.append(str(px.dirname(__file__)))
from bin.transformers_o import AutoModelForCausalLM, RobertaTokenizerFast


modelname = cfg["model"]
batch_size = cfg["batch_size"]
reasonable_doubt = cfg["reasonable_doubt_index"]
max_perplexity = cfg["max_perplexity"]
top_k = cfg["top_k"]
min_conf_ocr = cfg["min_conf_ocr"]
min_conf_combined = cfg["min_conf_combined"]
prefix = [".", "-"]
cuda = cuda.is_available() and cfg["cuda"]
print("cuda:", cuda)

tokenizer = RobertaTokenizerFast.from_pretrained(modelname, add_prefix_space=True, max_len=512, pad_token="<pad>", unk_token="<unk>", mask_token="<mask>", pad_to_max_length=True)
if cuda:
    model = AutoModelForCausalLM.from_pretrained(modelname).to(0)
else:
    model = AutoModelForCausalLM.from_pretrained(modelname)
model.eval()

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
    bathces = [tokenizer.convert_tokens_to_ids(x) for x in grouped_tokens]
    return bathces, token_word


def lm_inspect(words, pre_confs=None, conf_threshold=min_conf_ocr, max_perplexity=max_perplexity):
    if isinstance(words, str):
        words = words.rstrip().replace("\n", " ")
        words = words.split()
    if not words:
        return [], []
    perplexities = []
    words_conf = []
    bathces, token_word = prepare_batches(words)

    if pre_confs:
        candidates = [i for i, x in enumerate(pre_confs) if x < conf_threshold]
    else:
        candidates = [i for i, x in enumerate(words)]

    for_masking = [[i] for i, y in enumerate(token_word) if y in candidates]
    input_ids_list, masked_tokens = create_batches_to_fix(bathces, for_masking)

    for i in range(0, len(input_ids_list), batch_size):
        if cuda:
            batch_input_ids = pad_and_stack_batches(input_ids_list[i:i + batch_size]).to(0)
        else:
            batch_input_ids = pad_and_stack_batches(input_ids_list[i:i + batch_size])
        with no_grad():
            outputs = model(batch_input_ids)

        for j in range(batch_input_ids.size(0)):
            masked_index = (batch_input_ids[j] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
            masked_logits = outputs.logits[j, masked_index, :]
            original_token_prob = softmax(masked_logits, dim=0)[masked_tokens[i+j]].item()
            perplexities.append(1/original_token_prob)

    inspection_perplexities = {x[0] : y for x, y in zip(for_masking, perplexities)}

    for i, word in enumerate(words):
        token_idxs = [j for j, x in enumerate(token_word) if x==i]
        wv = [inspection_perplexities[x] if x in inspection_perplexities else pre_confs[i] for x in token_idxs]
        words_conf.append(sum(wv)/len(wv))

    words_conf = [1-x/max_perplexity if x<max_perplexity else 0 for x in words_conf]
    return words_conf, words


def confidence_rework(ocr_confs, lm_confs, rdi=1-reasonable_doubt):
    return [(y*rdi)**(1-x) if x<min_conf_ocr else x for x, y in zip(ocr_confs, lm_confs)]


def lm_fix_words(words, confs):
    token_batches, token_word = prepare_batches(words)
    to_fix = [i for i, x in enumerate(confs) if x < min_conf_combined]
    for_masking = [[i for i, y in enumerate(token_word) if y==x] for x in to_fix]
    input_ids_list, _ = create_batches_to_fix(token_batches, for_masking)
    all_predictions= []
    results = []

    for i in range(0, len(input_ids_list), batch_size):
        if cuda:
            batch_input_ids = pad_and_stack_batches(input_ids_list[i:i + batch_size]).to(0)
        else:
            batch_input_ids = pad_and_stack_batches(input_ids_list[i:i + batch_size])
        with no_grad():
            outputs = model(batch_input_ids)

        for j in range(batch_input_ids.size(0)):
            masked_index = (batch_input_ids[j] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
            masked_logits = outputs.logits[j, masked_index, :]
            top_k_indices = topk(masked_logits, top_k, dim=0).indices.tolist()
            top_k_tokens = [tokenizer.decode([token_id]) for token_id in top_k_indices]
            all_predictions.append(top_k_tokens)

    print(len(to_fix), len(all_predictions)) 
 
    inspection_prediction = {x : y for x, y in zip(to_fix, all_predictions)}
    for i, word in enumerate(words):
        if i not in inspection_prediction.keys():
            results.append(word)
        elif word in inspection_prediction[i]:
            results.append(word)
        else:
            predictions = [lat2cyr(x.strip()) for x in inspection_prediction[i]]
            results.append(find_most_similar_word(word, predictions))
    return results


def pad_and_stack_batches(input_ids_list):
    max_length = max(len(batch) for batch in input_ids_list)
    padded_batches = [cat([batch, tensor([tokenizer.pad_token_id] * (max_length - len(batch)), dtype=tlong)]) for batch in input_ids_list]
    return stack(padded_batches)


def create_batches_to_fix(token_batches, for_masking):
    masked_contexts = []
    masked_tokens = []
    batch_min = 0
    batch_max = 0

    for i, batch in enumerate(token_batches):
        batch_max += len(batch)

        for to_mask in for_masking:
            mask_avg = sum(to_mask)/len(to_mask)
            if batch_max > mask_avg and mask_avg >= batch_min:
                to_mask = [x-batch_min for x in to_mask]
                masked_context = batch.copy()
                masked_tokens.append(masked_context[to_mask[0]:to_mask[-1]+1])
                masked_context[to_mask[0]:to_mask[-1]+1] = [tokenizer.mask_token_id]
                masked_context = tokenizer.convert_tokens_to_ids(prefix) + masked_context
                masked_contexts.append(tensor(masked_context, dtype=tlong))


        batch_min = batch_max

    return masked_contexts, masked_tokens