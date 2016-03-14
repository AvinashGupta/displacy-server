var displaCy = displaCy || {};

function displaCy(options) {
    this.api = options.api;
    this.defaults = DEFAULTS;
    this.container = document.getElementById(this.defaults.containerId);
}

displaCy.prototype = {
    run: function(options, onStart, onSuccess, onFinal, onErrors) {
        var options = options || {};

        this.request = {
            mode: (options.mode) ? options.mode : this.defaults.mode,
            text: options.text || this.defaults.text,
            history: options.history || '',
            edits: options.edits || this.defaults.edits
        }

        if(onStart && typeof onStart === 'function') onStart();
        window.addEventListener('keyup', abortRequest); 

        var xhr = new XMLHttpRequest();
        xhr.open('POST', this.api + this.request.mode, true);
        xhr.setRequestHeader('Content-type', 'application/json');
        xhr.onreadystatechange = function() {
            if(xhr.readyState === 4 && xhr.status === 200) {

                var state = this.parseResult(JSON.parse(xhr.responseText));

                if(this.request.mode == 'manual') this.displayAnnotation(state, function(key) {
                    this.run({
                        mode: 'manual',
                        text: this.request.text,
                        history: this.request.history + key + ',',
                        edits: this.getEdits()
                    }, onStart, onSuccess, onFinal, onErrors);
                });

                else this.displayParse(state);

                if(onSuccess && typeof onSuccess === 'function') onSuccess();
                if(state.is_final && onFinal && typeof onFinal === 'function') onFinal();
                window.removeEventListener('keyup', abortRequest); 

                return state;
            }

        }.bind(this);

        xhr.onerror = function() {
            xhr.abort();
            if(onErrors && typeof onErrors === 'function') onErrors();
        }

        xhr.send(JSON.stringify({
            text: this.request.text,
            history: this.request.history,
            edits: this.request.edits
        }));

        function abortRequest(event) {
            if(event.keyCode == 27) {
                xhr.abort();
                if(onErrors && typeof onErrors === 'function') onErrors();
                window.removeEventListener('keyup', abortRequest);
            }
        }
    },

    parseResult: function(result) {
        this.versionString = result.version;

        return {
            words: result.parse.words,
            arrows: result.parse.arrows,
            stack: result.parse.stack,
            focus: result.parse.focus,
            is_final: result.parse.is_final,
            actions: result.actions || {},
            notes: result.edits.notes || [],
            edits: {
                words: result.edits.words,
                tags: result.edits.tags,
                labels: result.edits.labels
            }
        }
    },

    displayParse: function(state) {
        this.clear(this.container);
        this.displayCss(state.arrows, state.words);
        this.displayWords(state.words, state.stack, state.edits);
        this.displayArrows(state.arrows, state.words, state.edits);
        this.displayNotes(state.notes);
        this.displayFocus(state.focus, state.arrows, state.words, state.stack);
        this.resizeAllFields(this.getElements('.field'));

        if(!state.arrows.length) document.documentElement.scrollLeft = document.body.scrollLeft = 0;
    },

    displayAnnotation: function(state, runNext) {
        this.displayParse(state);
        this.displayActionButtons(this.getActionButtons.call(this, state.actions, runNext));
    },

    displayCss: function(arrows, words) {
        var stylesheet = this.create('style', 0, 0, { 'scoped': 'true' });
        var arrowSizes = this.getArrowSizes(arrows.length);
        var unit = this.defaults.unit;

        var style = [
            '#displacy *, #displacy *:before ,#displacy *:after { box-sizing:border-box }',
            '#displacy { width: ' + words.length * arrowSizes.width + unit + '; min-width: 100vw; overflow: visible; padding: 0; margin: 0; -webkit-user-select: none; -ms-user-select: none; -moz-user-select: none; user-select: none; min-height: 100vh; height: 100vh}',
            '#displacy .words { display: flex; display: -webkit-flex; display: -ms-flexbox; display: -webkit-box; flex-flow: row nowrap; overflow: hidden; text-align: center; position: absolute; bottom: 25px; left: 0; min-width: ' + arrowSizes.width * words.length + unit + ' }',
            '#displacy .words .token { display: inline-block; width: ' + arrowSizes.width + unit + ' }',
            '#displacy .words .token .tag, #displacy .words .token .word { display: inline } ',
            '#displacy .arrows { width: 100%; position: absolute; bottom: 125px; left: 0; text-align: center }',
            '#displacy .level { position: absolute; bottom: 0; width: 100% }',
            '#displacy .arrows { height: ' + arrowSizes.height + unit + ' }',
            '#displacy .level { left: ' + arrowSizes.width/2 + unit + ' }',

            '#displacy .arrow { height: 100%; position: absolute; overflow: hidden }',
            '#displacy .arrow:before { content: ""; display: block; height: 200%; border-radius: 50%; border: ' + arrowSizes.arc + unit + ' solid; margin: 0 auto }',
            '#displacy .arrow:after { content: ""; width: 0; height: 0; position: absolute; bottom: -1px; border-top: ' + arrowSizes.head + unit + ' solid; border-left: ' + (arrowSizes.head/2) + unit + ' solid transparent; border-right: ' + (arrowSizes.head/2) + unit + ' solid transparent }',
            '#displacy .arrow.null { display: none }',
            '#displacy .arrow .label { position: absolute; top: 0; z-index: 90 }',
            '#displacy .focus { position: absolute; top: 0; height: 100%; z-index: -1 }',
            '#displacy .words .in-focus { position: relative; z-index: 100 }',
            '#displacy .divider { display: block }',
            '#displacy .note { visibility: visible; position: absolute; width: ' + this.defaults.notes.width + unit + '; height: ' + this.defaults.notes.height + unit + '; margin: 0; padding: 0; z-index: 100 !important; }',
            '#displacy .note header { cursor: move }',
        ];

        for(var i = 1; i <= arrows.length; i++) {
            var level = '.level' + i;
            style.push(
                '#displacy ' + level + ' { height: ' + (100/arrows.length * i) + '% }',
                '#displacy ' + level + ' .arrow { width: ' + (arrowSizes.width * i) + unit + ' }',
                '#displacy ' + level + ' .arrow:before { width: calc(100% - ' + (arrowSizes.spacing * (arrows.length + 1 - i)) + unit + ') }',
                '#displacy ' + level + ' .arrow.left:after { left: ' + arrowSizes.spacing * (arrows.length - i)/2 + unit + ' }',
                '#displacy ' + level + ' .arrow.right:after { right: ' + arrowSizes.spacing * (arrows.length - i)/2 + unit + ' }'
            );
        }

        for(i = 1; i < words.length; i++) {
            style.push('#displacy .level .arrow:nth-child(' + i + ') { left: ' + arrowSizes.width * (i - 1) + unit + '}');
        }

        stylesheet.appendChild(this.textNode(style.join(' ')));
        this.container.appendChild(stylesheet);
    },

    displayWords: function(words, stack, edits) {

        function createWord(i, word_edited, tag_edited) {
            var self = this;
            var token = this.create('div', 'token ' + this.defaults.tags[(tag_edited) ? edits.tags[i] : words[i].tag]);
            if(i === focus) token.classList.add(this.defaults.classes['in_focus']);
            if(stack[i]) token.classList.add(this.defaults.classes['on_stack']);
            if(words[i].is_pushed) token.classList.add(this.defaults.classes['is_pushed']);
            if(words[i].is_popped) token.classList.add(this.defaults.classes['is_popped']);

            var word = this.create('input', 'word field', 'word-' + i, { 'data-initial': words[i].word }, 0, function() {
                this.select(this);
            });

            if(word_edited) {
                word.value = edits.words[i];
                word.classList.add('edited');
            }

            else word.value = words[i].word;

            word.onkeydown = function(event) {
                var editKeys = { 9: true, 37: true, 39: true, 16: true }

                if(event.keyCode == 27) {
                    this.value = words[i].word;
                    if(this.classList.contains('edited')) this.classList.remove('edited');
                    self.resizeField(this);
                    this.blur();
                }

                else if(event.keyCode == 13) this.blur();
                else if(!editKeys[event.keyCode]) this.classList.add('edited');
            }

            token.appendChild(word);
            return token;
        }

        function createTag(i, tag_edited) {
            var selected = {
                current: (tag_edited) ? edits.tags[i] : words[i].tag,
                initial: words[i].tag
            }

            return this.displaySelect(selected, 'tag', this.defaults.tags, tag_edited);
        }

        var container = this.create('div', 'words');

        for(var i = 0; i < words.length; i++) {
            var word_edited = edits.words && edits.words[i] && (edits.words[i] != words[i].word) || false;
            var tag_edited = edits.tags && edits.tags[i] && (edits.tags[i] != words[i].tag) || false;
            var token = createWord.call(this, i, word_edited, tag_edited);
            var tag = createTag.call(this, i, tag_edited);

            token.appendChild(this.create('span', 'divider'));
            token.appendChild(tag);
            container.appendChild(token);
        }

        this.container.appendChild(container);
    },

    displayArrows: function(arrows, words, edits) {

        function createArrow(i, j, label_edited) {
            var arrow = this.create('span');

            if(arrows[i][j] !== null) {
                arrow.className = 'arrow ' + arrows[i][j].dir + ' ' + this.defaults.labels[(label_edited) ? edits.labels[i][j] : arrows[i][j].label];
                if(label_edited) arrow.classList.add('edited');
                if(arrows[i][j].is_new) arrow.classList.add(this.defaults.classes['is_new']);

                var selected = {
                    current: (label_edited) ? edits.labels[i][j] : arrows[i][j].label,
                    initial: arrows[i][j].label
                }

                arrow.appendChild(this.displaySelect(selected, 'label', this.defaults.labels, label_edited));
            }

            else arrow.className = 'arrow null';
            return arrow;
        }

        var container = this.create('div', 'arrows');

        for(var i = 0; i < arrows.length; i++) {
            var level = this.create('div', 'level level' + (i + 1));

            for(var j = 0; j < arrows[i].length; j++) {
                var label_edited = edits.labels && edits.labels[i] && edits.labels[i][j] && arrows[i] && arrows[i][j] && (edits.labels[i][j] != arrows[i][j].label) || false;
                level.appendChild(createArrow.call(this, i, j, label_edited));
            }

            container.appendChild(level);
        }

        this.container.appendChild(container);
    },

    displaySelect: function(selected, classname, descriptions, is_edited) {
        var self = this;
        var select = this.create('select', classname + ' field');
        if(is_edited) select.classList.add('edited');
        select.add(this.create('option', 0, 0, { 'selected': 'true', 'value' : selected.current }, selected.current));
        select.setAttribute('data-initial', selected.initial);

        var options = '';
        for(var i = 0; i < Object.keys(descriptions).length; i++) {
            var name = Object.keys(descriptions)[i];
            if(name != selected.current) options += '<option value="' + name + '">' + name + '</option>';
        }

        select.innerHTML += options;

        select.onchange = function() {
            this.classList.add('edited');

            for(var i = 0; i < this.parentElement.classList.length; i++) {
                if(this.parentElement.classList[i].substring(0,2) == 'w-' || this.parentElement.classList[i].substring(0,2) == 't-') this.parentElement.classList.remove(this.parentElement.classList[i]);
            }

            this.parentElement.classList.add(descriptions[this.value]);
            self.resizeField(this);
            this.blur();
        }

        return select;
    },

    getActionButtons: function(actions, runNext) {
        var buttons = [];

        actions.forEach(function(action) {
            buttons.push({
                key: action.key,
                code: action.binding,
                label: action.label,
                enabled: action.is_valid,
                action: function() {
                    runNext.call(this, action.key)
                }
            });
        });

        return buttons;
    },

    displayActionButtons: function(buttons) {
        if(this.getById('actions')) this.clear('actions');
        var actions = this.create('div', 'actions active', 'actions');

        for(var i = 0; i < buttons.length; i++) {
            var button = this.create('button', 'action-' + buttons[i].label, 0, 0, buttons[i].label, buttons[i].action.bind(this));
            if(!buttons[i].enabled) button.disabled = true;
            actions.appendChild(button);
        }

        this.container.appendChild(actions);

        document.onkeydown = function(event) {
            if(event.target.nodeName.toLowerCase() != 'input' && event.target.nodeName.toLowerCase() != 'textarea') {
                for(var i = 0; i < Object.keys(buttons).length; i++) {
                    if(event.keyCode == buttons[i].code) {
                        event.preventDefault();
                        buttons[i].action.call(this);
                    }
                }
            }
        }.bind(this);
    },

    displayNotes: function(notes) {
        for(var i = 0; i < notes.length; i++) {
            this.displayNote({ left: notes[i].left, bottom: notes[i].bottom }, notes[i].text, true);
        }
    },

    displayNote: function(position, text, closed) {

        function constructNote() {
            if(text) textarea.value = text;
            header.appendChild(headline);
            header.appendChild(toggle);
            header.appendChild(remove);
            note.appendChild(header);
            note.appendChild(textarea);
        }

        function appendNote() {
            if(this.getById('notes')) this.getById('notes').appendChild(note);

            else {
                var notes = this.create('div', 'notes', 'notes');
                notes.appendChild(note);
                this.container.appendChild(notes);
            }

            if(!closed) textarea.focus();
        }

        var note = this.create('div', 'note');

        if(!closed) note.classList.add('active');
        note.style.left = (position && position.left) ? position.left : ((document.documentElement.scrollLeft || document.body.scrollLeft) + this.defaults.notes.left) + this.defaults.unit;
        note.style.bottom = (position && position.bottom) ? position.bottom : (this.container.clientHeight - this.defaults.notes.top - this.defaults.notes.height) + this.defaults.unit;

        var header = this.create('header');
        var headline = this.create('h4', 'headline', 0, 0, 'Note');
        var textarea = this.create('textarea', 'note-content');

        var toggle = this.create('button', 'toggle-note', 0, 0, 'Toggle', function() {
            note.classList.toggle('active');
        }.bind(this));

        var remove = this.create('button', 'delete-note', 0, { 'data-tooltip' : 'Delete note'}, 'Delete', function() {
            note.remove();
        });

        constructNote();
        appendNote.call(this);

        this.makeDraggable(this.getElements('.note'), this.defaults.notes.height);
    },

    getEdits: function() {

        function compare(current, initial) {
            var differences = {};

            for(var i = 0; i < current.length; i++) {
                if(current[i] != initial[i]) differences[i] = current[i];
            }

            return differences;
        }

        function compareLabels(labels) {
            var differences = {};

            for(var i = 0; i < Object.keys(labels).length; i++) {
                differences[i] = compare(labels[i].current, labels[i].initial);
            }

            return differences;
        }

        var state = this.readDOM();

        return {
            words: compare(state.words.current, state.words.initial),
            tags: compare(state.tags.current, state.tags.initial),
            labels: compareLabels(state.labels),
            notes: state.notes
        }
    },

    readDOM: function() {

        function readWords() {
            var words = this.getElements('.word');
            var result = { current: [], initial: [] };

            words.forEach(function(word) {
                result.current.push(word.value);
                result.initial.push(word.getAttribute('data-initial'));
            });

            return result;
        }

        function readTags() {
            var tags = this.getElements('.tag');
            var result = { current: [], initial: [] };

            tags.forEach(function(tag) {
                result.current.push(tag.options[tag.selectedIndex].value);
                result.initial.push(tag.getAttribute('data-initial'));
            });

            return result;
        }

        function readLabels() {
            var result = {};
            var levels = document.querySelectorAll('.level');

            for(i = 0; i < levels.length; i++) {
                result[i] = { current: [], initial: [] };

                Array.from(levels[i].querySelectorAll('.arrow')).forEach(function(arrow) {
                    if(arrow.classList.contains('null')) {
                        result[i].current.push(null);
                        result[i].initial.push(null);
                    }

                    else {
                        var label = arrow.querySelector('.label');
                        result[i].current.push(label.options[label.selectedIndex].value);
                        result[i].initial.push(label.getAttribute('data-initial'));
                    }
                });
            }

            return result;
        }

        function readNotes() {
            var notes = this.getElements('.note');
            var result = [];

            notes.forEach(function(note) {
                result.push({
                    left: note.style.left,
                    bottom: note.style.bottom,
                    text: note.getElementsByTagName('textarea')[0].value
                });
            });

            return result;
        }

        return {
            words: readWords.call(this),
            tags: readTags.call(this),
            labels: readLabels.call(this),
            notes: readNotes.call(this)
        };
    },

    displayFocus: function(focus, arrows, words, stack) {
        var arrowSizes = this.getArrowSizes(arrows.length);
        var unit = this.defaults.unit;
        var container = this.create('div', 'focus', 'focus', { 'style': 'width: ' + arrowSizes.width + unit + '; left: ' + arrowSizes.width * focus + unit + ';' });
        container.appendChild(this.displayStack(words, stack));

        if(arrowSizes.width * focus - (document.documentElement.scrollLeft || document.body.scrollLeft) > document.body.clientWidth/2) document.documentElement.scrollLeft = document.body.scrollLeft = arrowSizes.width * focus - document.body.clientWidth/2 + arrowSizes.width/2;

        this.container.appendChild(container);
    },

    displayStack: function(words, stack) {
        var container = this.create('div', 'current-stack', 0, { 'title' : 'Stack' });

        for(var i = 0; i < words.length; i++) {
            if(stack[i]) {
                var word = this.create('div', 0, 0, 0, words[i].word);
                container.insertBefore(word, container.childNodes[0]);
            }
        }

        return container;
    },

    getArrowSizes: function(levels) {
        var sizes = {
            height: this.defaults.arrows.height,
            width: this.defaults.arrows.width,
            spacing: this.defaults.arrows.spacing,
            head: this.defaults.arrows.head,
            arc: this.defaults.arrows.arc
        }

        if(levels <= 2) sizes.height /= 2.75;
        else if(levels == 3) sizes.height /= 1.75;

        else if(levels > 12) {
            sizes.width *= 1.15;
            sizes.height *= 1.25;
        }

        else if(levels > 20) {
            sizes.width *= 1.25;
            sizes.height *= 1.5;
        }

        return sizes;
    },

    makeDraggable: function(elements, height) {

        function drag(object) {
            selected = object;
            x = x_pos - selected.offsetLeft;
            y = y_pos - self.container.clientHeight - height - selected.offsetTop;
        }

        function move(event) {
            x_pos = document.all ? window.event.clientX : event.pageX;
            y_pos = document.all ? window.event.clientY : self.container.clientHeight - event.pageY;

            if(selected) {
                selected.style.left = (x_pos - x) + 'px';
                selected.style.bottom = (y_pos - height) + 'px';
                selected.classList.add('selected');
            }
        }

        var x, y, x_pos, y_pos, selected;
        var self = this;

        for(var i = 0; i < elements.length; i++) {
            elements[i].addEventListener('mousedown', function(event) {
                drag(this);
            });

            document.onmousemove = move.bind(this);

            document.onmouseup = function() {
                if(selected) {
                    selected.classList.remove('selected');
                    selected = null;
                }
            }
        }
    },

    resizeField: function(element) {

        /* based on Stretchy by Lea Verou: http://leaverou.github.io/stretchy */
        var offset = 0;

        if(element.nodeName.toLowerCase() == 'input') {
            element.style.width = '0';
            offset = element.offsetWidth;
            element.scrollLeft = 1e+10;

            var width = Math.max(element.scrollLeft + offset, element.scrollWidth - element.clientWidth);
            element.style.width = width + 'px';
        }

        else if(element.nodeName.toLowerCase() == 'select') {
            var option = this.create('_');
            option.textContent = element.options[element.selectedIndex].textContent;
            element.parentNode.insertBefore(option, element.nextSibling);
            option.style.width = '';

            if(!getComputedStyle(option).webkitLogicalWidth) element.style.width = 'calc(' + element.style.width + ' + 2em)';
            else element.style.width = option.offsetWidth + 'px';

            option.parentNode.removeChild(option);
            option = null;
        }
    },

    resizeAllFields: function(elements) {

        function listener(event) {
            this.resizeField(event.target);
        }

        this.container.removeEventListener('input', listener);
        this.container.removeEventListener('change', listener);

        for(var i = 0; i < elements.length; i++) {
            this.resizeField(elements[i]);
        }

        this.container.addEventListener('input', listener.bind(this));
        this.container.addEventListener('change', listener.bind(this));
    },

    getById: function(id) {
        return document.getElementById(id);
    },

    getElements: function(elements) {
        return Array.from(this.container.querySelectorAll(elements));
    },

    clear: function(element) {
        if(typeof element === 'string') element = this.getById(element);

        while (element.lastChild) {
            element.removeChild(element.lastChild);
        }
    },

    create: function(tag, classname, id, attributes, content, onclick) {
        var element = document.createElement(tag);
        if(classname) element.className = classname;
        if(id) element.id = id;

        if(attributes) {
            for(i = 0; i < Object.keys(attributes).length; i++) {
                var attribute = Object.keys(attributes)[i];
                var value = attributes[attribute];
                element.setAttribute(attribute, value);
            }
        }

        if(content) element.appendChild(this.textNode(content));
        if(onclick) element.onclick = onclick;
        return element;
    },

    textNode: function(text) {
        return document.createTextNode(text);
    }
}

var DEFAULTS = {
    mode: "parse",
    containerId: "displacy",
    text: "displaCy uses CSS and JavaScript to show you how computers understand language",
    unit: "px",
    arrows: {
        height: 350,
        width: 175,
        spacing: 10,
        head: 12,
        arc: 2
    },
    notes: {
        height: 150,
        width: 175,
        left: 20,
        top: 100
    },
    edits: {
        words: {},
        tags: {},
        labels: {},
        notes: {}
    },
    tags : {
        "NO_TAG" : "w-notag",
        "ADJ" : "w-adj",
        "ADP" : "w-adp",
        "ADV" : "w-adv",
        "AUX" : "w-aux",
        "CONJ" : "w-conj",
        "DET" : "w-det",
        "INTJ" : "w-intj",
        "NOUN" : "w-noun",
        "NUM" : "w-num",
        "PART" : "w-part",
        "PRON" : "w-pron",
        "PROPN" : "w-propn",
        "PRT" : "w-prt",
        "PUNCT" : "w-punct",
        "SCONJ" : "w-sconj",
        "SYM" : "w-sym",
        "VERB" : "w-verb",
        "X" : "w-x",
        "EOL" : "w-eol",
        "SPACE" : "w-ent-space",
        "PERSON" : "w-ent-pers",
        "NORP" : "w-ent-norp",
        "FACILITY" : "w-ent-facility",
        "ORG" : "w-ent-org",
        "GPE" : "w-ent-gpe",
        "LOC" : "w-ent-loc",
        "PRODUCT" : "w-ent-product",
        "EVENT" : "w-ent-event",
        "WORK_OF_ART" : "w-ent-workofart",
        "LAW" : "w-ent-law",
        "LANGUAGE" : "w-ent-language",
        "DATE" : "w-num-date",
        "TIME" : "w-num-time",
        "PERCENT" : "w-num-percent",
        "MONEY" : "w-num-money",
        "QUANTITY" : "w-num-quantity",
        "ORDINAL" : "w-num-ordinal",
        "CARDINAL" : "w-num-cardinal",
    },
    labels : {
        "acl" : "t-acl",
        "acomp" : "t-acomp",
        "advcl" : "t-advcl",
        "advmod" : "t-advmod",
        "agent" : "t-agent",
        "amod" : "t-amod",
        "appos" : "t-appos",
        "attr" : "t-attr",
        "aux" : "t-aux",
        "case" : "t-case",
        "cc" : "t-cc",
        "ccomp" : "t-ccomp",
        "compound" : "t-compound",
        "conj" : "t-conj",
        "dative" : "t-dative",
        "dep" : "t-dep",
        "det" : "t-det",
        "dobj" : "t-dobj",
        "expl" : "t-expl",
        "iobj" : "t-iobj",
        "intj" : "t-intj",
        "mark" : "t-mark",
        "meta" : "t-meta",
        "neg" : "t-neg",
        "nmod" : "t-nmod",
        "npadvmod" : "t-npadvmod",
        "nummod" : "t-nummod",
        "nsubj" : "t-nsub",
        "oprd" : "t-oprd",
        "parataxis" : "t-parataxis",
        "pmod" : "t-pmod",
        "pcomp" : "t-pcomp",
        "pobj" : "t-pobj",
        "poss" : "t-poss",
        "preconj" : "t-preconj",
        "predet" : "t-predet",
        "prep" : "t-prep",
        "prt" : "t-prt",
        "punct" : "t-punct",
        "quantmod" : "t-quantmod",
        "relcl" : "t-relcl",
        "root" : "t-root",
        "xcomp" : "t-xcomp"
    },
    classes : {
        "on_stack" : "stack",
        "is_entity" : "w-ent",
        "low_prob" : "low-prob",
        "in_focus" : "in-focus",
        "is_new" : 'is-new',
        "is_edit" : "edited",
        "is_w_edit" : "edited-word",
        "is_t_edit" : "edited-tag",
        "is_l_edit" : "edited-label",
        "is_pushed" : "pushed",
        "is_popped" : "popped"
    }
};
