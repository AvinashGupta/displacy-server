from __future__ import unicode_literals
from __future__ import print_function

import spacy.en
from spacy.attrs import ORTH, SPACY, TAG, POS, ENT_IOB, ENT_TYPE
from spacy.parts_of_speech import NAMES as UNIV_POS_NAMES


from . import models


try:
  unicode
except NameError:
  unicode = str


print("Loading models...")
NLU = spacy.en.English()
print("Ready.")


def merge_entities(doc):
    ents = [(e[0].idx, e[len(e)-1].idx + len(e[len(e)-1]), e.label_, e.lemma_)
            for e in doc.ents if len(e) >= 2]
    for start, end, label, lemma in ents:
        merged = doc.merge(start, end, label, lemma, label)
        assert merged != None


def merge_nps(doc):
    nps = [(np[0].idx, np[-1].idx + len(np[-1]), np.root.tag_, np.lemma_)
            for np in doc.noun_chunks if len(np) >= 2]
    
    for start, end, ent_type, lemma in nps:
        doc.merge(start, end, u'NP', lemma, ent_type)


def merge_punct(tokens):
    # Merge punctuation onto its head
    collect = False
    start = None
    merges = []

    for word in tokens:
        if word.whitespace_:
            if collect:
                span = tokens[start:word.i+1]
                if len(span) >= 2:
                    merges.append((
                        span[0].idx,
                        span[-1].idx + len(span[-1]),
                        span.root.tag_,
                        span.root.lemma_,
                        span.root.ent_type_))
                collect = False
                start = None
        elif not collect:
            collect = True
            start = word.i
    if collect:
        span = tokens[start:len(tokens)]
        merges.append((span[0].idx, span[-1].idx + len(span[-1]),
                       span.root.tag_, span.root.lemma_, span.root.ent_type_))
    for merge in merges:
         tokens.merge(*merge)


def get_actions(parse_state, history_length):
    actions = []
    queue = list(sorted(parse_state.queue))
    stack = list(sorted(parse_state.stack))
    stack = []
    actions.append({'label': 'shift', 'key': 'S', 'binding': 38,
                    'is_valid': NLU.parser.moves.is_valid(parse_state, 'S')})
    actions.append({'label': 'left', 'key': 'L', 'binding': 37,
                    'is_valid': NLU.parser.moves.is_valid(parse_state, 'L-det')})
    actions.append({'label': 'predict', 'key': '_', 'binding': 32,
                    'is_valid': bool(queue or len(stack) > 1)})
    actions.append({'label': 'right', 'key': 'R', 'binding': 39,
                    'is_valid': NLU.parser.moves.is_valid(parse_state, 'R-dobj')})
    actions.append({'label': 'undo', 'key': '-', 'binding': 8,
                    'is_valid': history_length != 0})
    actions.append({'label': 'reduce', 'key': 'D', 'binding': 40,
                    'is_valid': NLU.parser.moves.is_valid(parse_state, 'D')})
    return actions


def _parse_history(history):
    if history and history.endswith(','):
        history = history[:-1]
    history = history.strip().split(',') if history else tuple()
    new_hist = []
    history_length = len(history)
    for action in history:
        if action == '-':
            if new_hist:
                new_hist.pop()
        else:
            new_hist.append(action)
    return new_hist, history_length


def handle_parse(json_data):
    text = json_data.get("text", "")
    history = json_data.get("history", "")
    client_state = json_data.get("client_state", {})
    print('Parse=', repr(json_data))
    tokens = NLU(text)
    merge_entities(tokens)
    merge_nps(tokens)
    merge_punct(tokens)
    state = models.State(
                [w.head.i for w in tokens],
                [w.dep_ for w in tokens],
                [],
                [],
                {}
            )
    return models.Model(tokens, [state], [], client_state, {}, {})


#def handle_steps(json_data):
#    text = json_data.get("text", "")
#    history = json_data.get("history", "")
#    client_state = json_data.get("client_state", {})
#    print('Steps=', repr(text))
#    tokens = NLU.tokenizer(text)
#    NLU.tagger(tokens)
#    NLU.matcher(tokens)
#
#    with NLU.parser.step_through(tokens) as state:
#        states = []
#        while not state.is_final:
#            action = state.predict()
#            state.transition(action)
#            states.append(models.State(state.heads, state.deps, state.stack, state.queue))
#    actions = [
#        {'label': 'prev', 'key': 'P', 'binding': 37, 'is_valid': True},
#        {'label': 'next', 'key': 'N', 'binding': 39, 'is_valid': True}
#    ]
#    return models.Model(state.doc, states, actions, client_state)


def handle_manual(json_data):
    text = json_data.get("text", "")
    history = json_data.get("history", "")
    client_state = json_data.get("client_state", {})
    print('Manual=', repr(json_data))

    if not isinstance(text, unicode):
        text = text.decode('utf8')
    text = text.replace('-SLASH-', '/')
    history, history_length = _parse_history(history)

    tokens = NLU.tokenizer(text)
    NLU.tagger(tokens)
    NLU.matcher(tokens)

    prev_deps = []
    prev_heads = []
    prev_top = None
    with NLU.parser.step_through(tokens) as state:
        for action in history:
            prev_deps = list(state.deps)
            prev_heads = list(state.heads)
            prev_top = max(state.stack) if state.stack else None
            state.transition(action)

    diffs = _diff_deps(prev_deps, prev_heads, state.deps, state.heads)
    
    NLU.entity(tokens)
    actions = get_actions(state.stcls, len(history))
    pushed = {}
    popped = {}
    if prev_top not in state.stack:
        popped = {prev_top: True}
    if state.stack and max(state.stack) > prev_top:
        pushed = {max(state.stack): True}
    return models.Model(tokens, [models.State(state.heads, state.deps,
                                 state.stack, state.queue, diffs)],
                        actions, client_state, pushed, popped)


def _diff_deps(prev_deps, prev_heads, deps, heads):
    diff = {}
    for i, head in enumerate(heads):
        if deps[i] != '' and prev_deps[i] == '':
            diff[i] = {'dep': deps[i], 'head': head}
    return diff
