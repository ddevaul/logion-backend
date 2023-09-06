# -*- coding: utf-8 -*-
from transformers import BertTokenizer, BertForMaskedLM
import torch
tokenizer = BertTokenizer.from_pretrained("cabrooks/LOGION-50k_wordpiece")
model = BertForMaskedLM.from_pretrained("cabrooks/LOGION-50k_wordpiece")
sm = torch.nn.Softmax(dim=1) # In order to construct word probabilities, we will employ softmax.
torch.set_grad_enabled(False) # Since we are not training, we disable gradient calculation.
import re

# Get top k suggestions for each masked position:
def argkmax(array, k, prefix='', dim=0): # Return indices of the 1st through kth largest values of an array, given prefix
  indices = []
  new_prefixes = []
  added = 0
  ind = 1
  while added < k:
    if ind > len(array[0]):
      break
    val = torch.kthvalue(-array, ind, dim=dim).indices.cpu().numpy().tolist()
    if prefix != '':
      cur_tok = tokenizer.convert_ids_to_tokens(val[0]).replace('##', '')
      trunc_prefix = prefix[:min(len(prefix), len(cur_tok))]
      if not cur_tok.startswith(trunc_prefix):
        ind += 1
        continue
    else:
      cur_tok = ''
    indices.append(val)
    if len(cur_tok) >= len(prefix):
      new_prefixes.append('')
    else:
      new_prefixes.append(prefix[len(cur_tok):])
    ind += 1
    added += 1
  return torch.tensor(indices), new_prefixes

# gets n predictions / probabilities for a single masked token , by default, the first masked token
def get_n_preds(token_ids, n, prefix, masked_ind, fill_inds, cur_prob=1):
  mask_positions = (token_ids.squeeze() == tokenizer.mask_token_id).nonzero().flatten().tolist()
  for i in range(len(fill_inds)):
    token_ids.squeeze()[mask_positions[i]] = fill_inds[i]

  #print(len(mask_positions), len(fill_inds))
  # model_id = min(len(mask_positions) - len(fill_inds) - 1, 4)
  logits = model(token_ids).logits.squeeze(0)
  mask_logits = logits[[[masked_ind]]]
  probabilities = sm(mask_logits)
  arg1, prefixes = argkmax(probabilities, n, prefix, dim=1)
  suggestion_ids = arg1.squeeze().tolist()
  n_probs = probabilities.squeeze()[suggestion_ids]
  n_probs = torch.mul(n_probs, cur_prob).tolist()
  new_fill_inds = [fill_inds + [i] for i in suggestion_ids]
  return tuple(zip(new_fill_inds, n_probs, prefixes)) 

def beam_search(token_ids, beam_size, prefix='', breadth=100):
  mask_positions = (token_ids.detach().clone().squeeze() == tokenizer.mask_token_id).nonzero().flatten().tolist()
  #print(len(mask_positions))
  num_masked = len(mask_positions)
  cur_preds = get_n_preds(token_ids.detach().clone(), beam_size, prefix, mask_positions[0], [])
  #for c in range(len(cur_preds)):
    #print(tokenizer.convert_ids_to_tokens(cur_preds[c][0][0]))

  for i in range(num_masked - 1):
    #print(i)
    candidates = []
    for j in range(len(cur_preds)):
      candidates += get_n_preds(token_ids.detach().clone(), breadth, cur_preds[j][2], mask_positions[i + 1], cur_preds[j][0], cur_preds[j][1])
    candidates.sort(key=lambda k:k[1],reverse=True)
    if i != num_masked - 2:
      cur_preds = candidates[:beam_size]
    else:
      cur_preds = candidates[:breadth]
  return cur_preds
# Get top 5 suggestions for each masked position:
def argkmax_right(array, k, suffix='', dim=0): # Return indices of the 1st through kth largest values of an array
  indices = []
  new_suffixes = []
  added = 0
  ind = 1
  while added < k:
    if ind > len(array[0]):
      break
    val = torch.kthvalue(-array, ind, dim=dim).indices.cpu().numpy().tolist()
    if suffix != '':
      cur_tok = tokenizer.convert_ids_to_tokens(val[0]).replace('##', '')
      trunc_suffix = suffix[len(suffix) - min(len(suffix), len(cur_tok)):]
      if not cur_tok.endswith(trunc_suffix):
        ind += 1
        continue
    else:
      cur_tok = ''
    indices.append(val)
    if len(cur_tok) >= len(suffix):
      new_suffixes.append('')
    else:
      new_suffixes.append(suffix[:len(suffix) - len(cur_tok)])
    ind += 1
    added += 1
  return torch.tensor(indices), new_suffixes

# gets n predictions / probabilities for a single masked token , by default, the first masked token
def get_n_preds_right(token_ids, n, suffix, masked_ind, fill_inds, cur_prob=1):
  mask_positions = (token_ids.squeeze() == tokenizer.mask_token_id).nonzero().flatten().tolist()
  # fill in the current guessed tokens
  for i in range(len(fill_inds)):
    token_ids.squeeze()[mask_positions[len(mask_positions) - i - 1]] = fill_inds[i]
  #print(len(mask_positions), len(fill_inds))
  # model_id = min(len(mask_positions) - len(fill_inds) - 1, 4)
  model_id = 0
  #print(model_id)
  # model = models[model_id]
  logits = model(token_ids).logits.squeeze(0)
  mask_logits = logits[[[masked_ind]]]
  probabilities = sm(mask_logits)
  arg1, suffixes = argkmax_right(probabilities, n, suffix, dim=1)
  suggestion_ids = arg1.squeeze().tolist()
  n_probs = probabilities.squeeze()[suggestion_ids]
  n_probs = torch.mul(n_probs, cur_prob).tolist()
  new_fill_inds = [fill_inds + [i] for i in suggestion_ids]
  return tuple(zip(new_fill_inds, n_probs, suffixes)) 

def beam_search_right(token_ids, beam_size, suffix='', breadth=100):
  mask_positions = (token_ids.detach().clone().squeeze() == tokenizer.mask_token_id).nonzero().flatten().tolist()
  num_masked = len(mask_positions)
  cur_preds = get_n_preds_right(token_ids.detach().clone(), beam_size, suffix, mask_positions[-1], [])
  #for c in range(len(cur_preds)):
    #print(tokenizer.convert_ids_to_tokens(cur_preds[c][0][0]))
  for i in range(num_masked - 1, 0, -1):
    #print('here: ' + str(i))
    candidates = []
    for j in range(len(cur_preds)):
      candidates += get_n_preds_right(token_ids.detach().clone(), breadth, cur_preds[j][2], mask_positions[i - 1], cur_preds[j][0], cur_preds[j][1])
    candidates.sort(key=lambda k:k[1],reverse=True)
    if i != 1:
      cur_preds = candidates[:beam_size]
    else:
      cur_preds = candidates[:breadth]
  for tokens, probability, _ in cur_preds:
    tokens.reverse()
  return cur_preds

def display_word(toks):
  s = ''
  first_tok = True
  for tok in toks:
    is_suffix = tok.startswith('##')
    if is_suffix: tok = '·' + tok[2:]  # remove suffix hashtags
    elif not first_tok: s += ' '
    
    s += tok
    
    first_tok = False
  return s


# text_test = 'ἐπείπερ ἐν τῷ γένει'
# toks = tokenizer.encode(text_test, return_tensors='pt')
# print(tokenizer.convert_ids_to_tokens(toks[0]))





def get_strings(text, num_toks):
  text = re.sub('[****]', tokenizer.mask_token, text)
  # print(text)
  tokens = tokenizer.encode(text, return_tensors='pt')
  sugs = beam_search(tokens, num_toks, '')
  strings = []
  for s in sugs:
    first_tok = tokenizer.convert_ids_to_tokens(s[0])[0]
    # if not first_tok.startswith('συν'):
      # continue
    converted = tokenizer.convert_ids_to_tokens(s[0])
    converted.reverse()
    # print(converted)
    # print(tokenizer.convert_ids_to_tokens(s[0]))
    # print(s[1])
    strings.append(s)
  strings = display_word(strings)
  return strings


def clean_text(text):

  # lunate sigmas at the end of the word
  text = re.sub(r'c(?!\w)', 'ς', text)
  # all remaining lunate sigmas
  text = re.sub(r'ϲ', 'σ', text)
  text = re.sub(r'Ϲ', 'Σ', text)

  # remove titles should I do this?

  # remove dots under letters
  text = re.sub("\u0323", "", text)

  # remove  ͜
  text = re.sub("͜", "", text)

  # replace ⸏word or ⸐word with [UNK]
  text = re.sub("[⸏⸐][\u0370-\u03ff\u1f00-\u1fff\[\]']*", " [UNK] ", text)

  # remove meter suggestions e.g. <–⏑⏑–⏓>
  text = re.sub("<[–⏔⏕⏓⏑]*>[\u0370-\u03ff\u1f00-\u1fff\']*", " [UNK] ", text)

  # remove meter suggestions not in arrows
  text = re.sub('[–⏔⏓⏑⏕]', "", text)
  
  # replace words with internal ellipses
  text = re.sub(f'[\u0370-\u03ff\u1f00-\u1fff\']+[\.]+((\[[" "\.]*\])|[\u0370-\u03ff\u1f00-\u1fff\'\.\[])+', " [UNK] ", text)

  # replace ellipses all by themselves with[UNK]
  text = re.sub('" "\.{2,}" "', " [UNK] ", text)

  # remove words starting and ending with [ ]
  text = re.sub(f'[" "]\[[" ".]*\][\u0370-\u03ff\u1f00-\u1fff.\']*\[[" ".]*\]', " [UNK] ", text)

  # remove words starting with [ ]
  text = re.sub(f'\[[" ".]*\][\u0370-\u03ff\u1f00-\u1fff\.\'\[\]]*', " [UNK] ", text)

  # remove words ending with [ ]
  text = re.sub(f'[\u0370-\u03ff\u1f00-\u1fff.\']*\[[" ".]*\]', " [UNK] ", text)

  # replace words with internal [ ]
  text = re.sub('[\u0370-\u03ff\u1f00-\u1fff\.\[\]\']+(\[[" "\.]*\])+((\[[" "\.]*\])|[\u0370-\u03ff\u1f00-\u1fff\'\.\[\]])*', " [UNK] ", text)

  # remove words ending with [
  text = re.sub(f'[\u0370-\u03ff\u1f00-\u1fff\.\']+\[\s', "[UNK]", text)

  # remove elipses beginning words e.g. .word
  text = re.sub('[\.]+[\u0370-\u03ff\u1f00-\u1fff.\'\[\]]', " [UNK] ", text)

  # remove daggers of desparation
  # text = re.sub('†.*†', " [UNK] ", text)

  # remove any remaining angle brackets < >
  text = re.sub(f'[<>]', "", text)

  # remove any remaining square brackets []
  text = re.sub(f'[\[\]]', "", text)

  # add back on the parentheses here
  text = re.sub('(UNK)', '[UNK]', text)

  # remove dashes that represent unfinished words
  # e.g. word-? 
  text = re.sub('[\u0370-\u03ff\u1f00-\u1fff\']+-\?', " [UNK] ", text)

  # unsplit words across lines
  text = re.sub('-\n[\s]*', "", text)

  # remove (= #)
  text = re.sub(f'[\([=" "1-9]*\)]', "", text)

  # remove parentheses around words
  text = re.sub(f'[\(\)]', "", text)

  # remove weird characters:
  text = re.sub("(([1-9]+,)|([1-9]+-)|(—\s—)|[†|>⸖※<0-9⌞⌟⊗⟦⟧»*\\\{\}])", "", text)
  random_character_list = ['†', '|', '>', '⸖', '※', '<', '1', '2', '0', '7', '5', '4', '8', '3', '⌞', '⌟' , '9', '6', '⊗', '⟦', '⟧', '»', '*', '{', '}']
  
  return text

def all_possibilities(text1, text2, num_tokens, right=False):
  fix = ''
  strings = []
  output = ''
  token_masks = ''
  # text1 = ''
  # text2 = f'πρώτης σελίδος χορὸν ἐξ Ἑλικῶνος ἐλθεῖν εἰς ἐμὸν ἦτορ ἐπεύχομαι εἵνεκ᾿ ἀοιδῆς, ἣν νέον ἐν δέλτοισιν ἐμοῖς ἐπὶ γούνασι θῆκα, δῆριν ἀπειρεσίην, πολεμόκλονον ἔργον Ἄρηος, εὐχόμενος μερόπεσσιν ἐς οὔατα πᾶσι βαλέσθαι, πῶς μύες ἐν βατράχοισιν ἀριστεύσαντες ἔβησαν, γηγενέων ἀνδρῶν μιμούμενοι ἔργα Γιγάντων, ὡς λόγος ἐν θνητοῖσιν ἔην· τοίην δ᾿ ἔχεν ἀρχήν. μῦς ποτε διψαλέος, γαλέης κίνδυνον ἀλύξας πλησίον, ἐν λίμνηι λίχνον προσέθηκε γένειον, ὕδατι τερπόμενος μελιηδέϊ· τὸν δὲ κατεῖδεν λιμνόχαρις πολύφημος, ἔπος δ᾿ ἐφθέγξατο τοῖον· “ξεῖνε, τίς εἶ; πόθεν ἦλθες ἐπ᾿ ἠιόνα; τίς δέ σ᾿ ὁ φύσας; πάντα δ᾿ ἀλήθευσον, μὴ ψευδόμενόν σε νοήσω. εἰ γάρ σε γνοίην φίλον ἄξιον, ἐς δόμον ἄξω, δῶρα δέ τοι δώσω ξεινήϊα πολλὰ καὶ ἐσθλά. εἶμι δ᾿ ἐγὼ βασιλεὺς Φυσίγναθος, ὃς κατὰ λίμνην τιμῶμαι βατράχων ἡγούμενος ἤματα πάντα· καί με πατὴρ Πηλεὺς ἀνεθρέψατο, Ὑδρομεδούσηι μιχθεὶς ἐν φιλότητι παρ᾿ ὄχθας Ἠριδανοῖο. καὶ σὲ δ᾿ ὁρῶ καλόν τε καὶ ἄλκιμον ἔξοχον ἄλλων.”'

  text1 = clean_text(text1)
  text2 = clean_text(text2)
  for i in range(num_tokens):
    token_masks += f' {tokenizer.mask_token} ' 
  text = text1 + " " + token_masks + " " + text2
  tokens = tokenizer.encode(text, return_tensors='pt')
  if right:
    sugs = beam_search_right(tokens, 20, fix)
  else: 
    sugs = beam_search(tokens, 20, fix)
  for s in sugs:
    first_tok = tokenizer.convert_ids_to_tokens(s[0])[0]
    # if not first_tok.startswith('συν'):
      # continue
    converted = tokenizer.convert_ids_to_tokens(s[0])
    converted.reverse()
    # print(converted)
    tok_arr = tokenizer.convert_ids_to_tokens(s[0])
    toks = len(tok_arr)
    st = ''
    for t in tok_arr:
      t = re.sub('[#]+', '', t)
      st += t
    strings.append(st + " probability: " + str(s[1]))

  return strings