class Model(object):
    def to_json(self):
        return {name: _as_json(value) for name, value in self.__dict__.items()
                if not name.startswith('_')}


class Parse(Model):
    def __init__(self, doc, states, actions, client_state):
        word_edits = client_state.get('words', {})
        tag_edits = client_state.get('tags', {})
        self.actions = actions
        self.words = [Word(w, w.i in word_edits, w.i in tag_edits) for w in doc]
        self.states = states
        self.client_state = client_state


class Word(Model):
    def __init__(self, token, is_w_edit=False, is_t_edit=False):
        self.word = token.orth_
        self.tag = token.pos_ if not token.ent_type_ else token.ent_type_
        self.is_entity = token.ent_iob in (1, 3)
        self.is_w_edit = is_w_edit
        self.is_t_edit = is_t_edit
        self.prob = token.prob


class State(Model):
    def __init__(self, heads, deps, stack, queue):
        Model.__init__(self)

        queue = [w for w in queue if w >= 0]
        self.focus = min(queue) if queue else -1
        self.is_final = bool(not stack and not queue)
        self.stack = set(stack)
        self.arrows = self._get_arrows(heads, deps)

    def _get_arrows(self, heads, deps):
        arcs = defaultdict(dict)
        for i, (head, dep) in enumerate(zip(heads, deps)):
            if i < head:
                arcs[head - i][i] = Arrow(i, head, dep)
            elif i > head:
                arcs[i - head][head] = Arrow(i, head, dep)
        output = []
        for level in range(1, len(heads)):
            level_arcs = []
            for i in range(len(heads) - level):
                level_arcs.append(arcs[level].get(i))
            output.append(level_arcs)
        while output and all(arc is None for arc in output[-1]):
            output.pop()
        return output


class Arrow(Model):
    def __init__(self, word, head, label):
        self.dir = 'left' if head > word else 'right'
        self.label = label


def _as_json(value):
    if hasattr(value, 'to_json'):
        return value.to_json()
    elif isinstance(value, list):
        return [_as_json(v) for v in value]
    elif isinstance(value, set):
        return {key: True for key in value}
    else:
        return value
