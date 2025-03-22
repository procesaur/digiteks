from torch import tensor, no_grad, softmax
from helper import cfg, group_into_sentences, usual_suspects
from stringworks import textsplit, isnumber, map_visual_similarity, calculate_similarities, harmonize_array, roman
from torch import cuda, stack, clamp, cat, long as tlong, nn
from transformers import AutoTokenizer, RobertaForMaskedLM, ModernBertForMaskedLM
from numpy import array as nparray, clip, newaxis, arange


class RobertaForMaskedLM2(RobertaForMaskedLM):
    _supports_param_buffer_assignment = False

class ModernBertForMaskedLM2(ModernBertForMaskedLM):
    _supports_param_buffer_assignment = False

cuda = cuda.is_available() and cfg["cuda"]
print("cuda:", cuda)

if cfg["modern"]:
    modellclass = ModernBertForMaskedLM2
else:
    modellclass = RobertaForMaskedLM2

if cfg["model"]:
    tokenizer = AutoTokenizer.from_pretrained(cfg["model"], add_prefix_space=True, max_len=512, pad_token="<pad>", unk_token="<unk>", mask_token="<mask>", pad_to_max_length=True)
    special_token_indices = tokenizer.all_special_ids

    encodes = [tokenizer.decode([i]) for i in range(len(tokenizer))]
    mapped_encodes = [map_visual_similarity(x) for x in encodes]
    encodes_length = nparray([len(x) for x in encodes])
    length_similarities = []
    for i in range(cfg["max_len_similarity"] + 1):
        t = abs(encodes_length-i)/clip(encodes_length, a_min=i, a_max=None)
        length_similarities.append(1-t)
    
    suspect_weights = {}
    for x in usual_suspects["strong"]:
        suspect_weights[x] = nparray([1+3*cfg["usual_suspects_boost"] if e.strip() in usual_suspects["strong"][x] else 1 for e in encodes])
    for x in usual_suspects["normal"]:
        suspect_weights[x] = nparray([1+cfg["usual_suspects_boost"] if e.strip() in usual_suspects["normal"][x] else 1 for e in encodes])

    if cuda:
        model = modellclass.from_pretrained(cfg["model"]).to(0)
    else:
        model = modellclass.from_pretrained(cfg["model"])
    model.eval()

    max_length=tokenizer.model_max_length - len(cfg["prefix"]) - len(cfg["suffix"]) - 2
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
            toks = tokenizer.tokenize(word)
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


def should_merge(x, y, c):
    if not cfg["model"]:
        return False
    c = len(tokenizer.tokenize(c))
    if c == 1:
        return True
    x = len(tokenizer.tokenize(x))
    y = len(tokenizer.tokenize(y))
    if c < x+y:
        return True
    return False


def lm_inspect(words, pre_confs=None, conf_threshold=cfg["min_conf_ocr"], max_perplexity=cfg["max_perplexity"]):
    if not cfg["model"]:
        print("No language model loaded!")
        return pre_confs, words
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

    for i in range(0, len(input_ids_list), cfg["batch_size"]):
        batch_input_ids, attention_masks = pad_and_stack_batches(input_ids_list[i:i + cfg["batch_size"]])
        with no_grad():
            outputs = model(batch_input_ids, attention_mask=attention_masks)

        for j in range(batch_input_ids.size(0)):

            masked_index = (batch_input_ids[j] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
            masked_logits = outputs.logits[j, masked_index, :]
            original_token_prob = softmax(masked_logits, dim=0)[masked_tokens[i+j]].item()
            perplexities.append(1/original_token_prob)

    inspection_perplexities = {x[0] : y for x, y in zip(for_masking, perplexities)}

    for i in range(len(words)):
        token_idxs = [j for j, x in enumerate(token_word) if x==i]
        wv = [inspection_perplexities[x] if x in inspection_perplexities else pre_confs[i] for x in token_idxs]
        if len(wv) != 0:
            words_conf.append(sum(wv)/len(wv))
        else:
            words_conf.append(0)

    words_conf = [1-x/max_perplexity if x<max_perplexity else 0 for x in words_conf]
    return words_conf, words


def confidence_rework(ocr_confs, lm_confs, rdi=cfg["reasonable_doubt_index"]):
    lm_confs = clip(nparray(lm_confs), a_min=rdi, a_max=1-rdi)
    lm_confs = lm_confs**(cfg["min_conf_ocr"]+rdi/2-nparray(ocr_confs))
    return list(lm_confs)


def lm_fix_words(words, confs, ocr_confs):
    if not cfg["model"]:
        print("No language model loaded!")
        return words
    if not words:
        return []
    token_batches, token_word = prepare_batches(words)
    to_fix = [i for i, x in enumerate(confs) if x < cfg["min_conf_combined"] and not isnumber(words[i])]
    if not to_fix:
        return words
    words_to_fix_orig = [words[x] for x in to_fix]

    words_to_fix = [x.lower() for x in words_to_fix_orig]
    mapped_to_fix = [map_visual_similarity(x) for x in words_to_fix]
    for_masking = [[i for i, y in enumerate(token_word) if y==x] for x in to_fix]
    input_ids_list, _ = create_batches_to_fix(token_batches, for_masking)

    similarities = calculate_similarities(words_to_fix, encodes) * cfg["sim_weight"]
    mapped_similarities = calculate_similarities(mapped_to_fix, mapped_encodes) * cfg["mapped_sim_weight"]
    len_similarities = nparray([length_similarities[min(len(word), cfg["max_len_similarity"])] for word in words_to_fix]) * cfg["len_sim_weight"]
    ocr_confs_to_fix = nparray([ocr_confs[i] for i in to_fix])[:, newaxis]
    combined_similarities = (similarities + mapped_similarities + len_similarities) * ocr_confs_to_fix

    all_probabilities = []
    outputs = []
    for i in range(0, len(input_ids_list), cfg["batch_size"]):
        batch_input_ids, attention_masks = pad_and_stack_batches(input_ids_list[i:i + cfg["batch_size"]])
        with no_grad():
            outputs = model(batch_input_ids, attention_mask=attention_masks)

        for j in range(batch_input_ids.size(0)):
            masked_index = (batch_input_ids[j] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0].item()
            masked_logits = outputs.logits[j, masked_index, :]
            probabilities = nn.functional.softmax(masked_logits, dim=0)
            probabilities[probabilities == 0] = 1e-10
            probabilities = clamp(1/probabilities/cfg["max_perplexity"], min=0, max=1)
            all_probabilities.append(probabilities.cpu().numpy())

    combined_similarities += (1-nparray(all_probabilities)) * (1-ocr_confs_to_fix) * cfg["lm_influence"]
    combined_similarities[:, special_token_indices] = 0

    for i, w in enumerate(words_to_fix_orig):
        if w.strip() in suspect_weights:
            combined_similarities[i] *= suspect_weights[w.strip()]

    guesses = combined_similarities.argmax(axis=1)
    sims = combined_similarities[arange(combined_similarities.shape[0]), guesses]
    guesses = harmonize_array([encodes[x] for x in guesses], words_to_fix_orig)
    inspection_prediction = {x : (y, z) for x, y, z in zip(to_fix, guesses, sims)}
    results = [inspection_prediction[i][0] if i in inspection_prediction.keys() and inspection_prediction[i][1] > cfg["lm_fix_over"] else word for i, word in enumerate(words)]
    return results


def pad_and_stack_batches(input_ids_list):
    padded_batches = []
    attention_masks = []
    for batch in input_ids_list:
        padding_length = max_length - len(batch)
        padded_batch = cat([batch, tensor([tokenizer.pad_token_id] * padding_length, dtype=tlong)])
        attention_mask = (padded_batch != tokenizer.pad_token_id).long()
        padded_batches.append(padded_batch)
        attention_masks.append(attention_mask)
    if cuda:
        padded_batches = stack(padded_batches).to(0)
        attention_masks = stack(attention_masks).to(0)
    else:
        padded_batches = stack(padded_batches)
        attention_masks = stack(attention_masks)
    return padded_batches, attention_masks


def create_batches_to_fix(token_batches, for_masking):
    masked_contexts = []
    masked_tokens = []
    batch_min = 0
    batch_max = 0

    for batch in token_batches:
        batch_max += len(batch)

        for to_mask in for_masking:
            mask_avg = sum(to_mask)/len(to_mask)
            if batch_max > mask_avg and mask_avg >= batch_min:
                to_mask = [x-batch_min for x in to_mask]
                masked_context = batch.copy()
                masked_tokens.append(masked_context[to_mask[0]:to_mask[-1]+1])
                masked_context[to_mask[0]:to_mask[-1]+1] = [tokenizer.mask_token_id]
                masked_context = tokenizer.convert_tokens_to_ids(cfg["prefix"]) + masked_context + tokenizer.convert_tokens_to_ids(cfg["suffix"])
                masked_contexts.append(tensor(masked_context, dtype=tlong))

        batch_min = batch_max
    return masked_contexts, masked_tokens


def fix_text(text):
    if not cfg["model"]:
        return "No language model loaded! Check config!"
    words = textsplit(text)
    probs = [cfg["min_conf_ocr"]-0.1 for x in words]
    results = lm_fix_words(words, probs)
    return " ".join(f"<b>{x}</b>" if x and x!=y else y for x, y in zip(results, words))
     