(function() {
    var baseurl = hostname || '';

    var $ = new displaCy({
        api: api
    });

    document.addEventListener('DOMContentLoaded', function() {
        _get('input').focus();
        addUIListeners();

        var share = getQueryVar('share');
        var modal = getQueryVar('modal');
        var oldVersion = checkBackwardsComp(getQueryVar('full'), getQueryVar('steps'), getQueryVar('manual'));

        if(modal) showModal(modal);

        if(share) {
            loadFromShareLink(share, function(response) {
                if(response.mode == 'manual') annotate(response);
                else parse(response);
            });
        }

        else if(oldVersion) oldVersion();
        else parse();

    }, false);

    function parse(options) {
        $.run(options || {
            text: _get('input').value || $.defaults.text
        }, onStart, onSuccess, onFinal, onErrors);
    }

    function annotate(options) {
        $.run(options || {
            mode: 'manual',
            text: _get('input').value || $.defaults.text
        }, onStart, onSuccess, function() {
            onFinal();
            playSound('bing.wav');
            displayToast('Your sentence is ready!');
        }, onErrors);
    }

    function getQueryVar(variable) {
       var query = window.location.search.substring(1);
       var vars = query.split('&');

       for(var i = 0; i < vars.length; i++) {
            var pair = vars[i].split('=');
            if(pair[0] == variable) return pair[1];
       }
       return false;
    }

    function checkBackwardsComp(full, steps, manual) {
        if(full || steps || manual) {
            return function() {
                if(full) parse({ text: decodeURIComponent(full) });
                else if(steps) annotate({ text: decodeURIComponent(steps), mode: 'manual' });
                else if(manual) annotate({ text: decodeURIComponent(manual), mode: 'manual' });
                else return false;
            }
        }

        else return false;
    }

    function getShareLink(callback) {
        var xhr = new XMLHttpRequest();
        xhr.open('POST', $.api + 'save', true);
        xhr.setRequestHeader('Content-type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                callback(baseurl + '/?share=' + JSON.parse(xhr.responseText).key);
            }
        }

        xhr.send(JSON.stringify({
            mode: $.request.mode,
            text: $.request.text,
            history: $.request.history,
            edits: $.getEdits()
        }));
    }

    function loadFromShareLink(token, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', $.api + 'load/' + token, true);
        xhr.onload = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                callback(JSON.parse(xhr.responseText));
            }
        }

        xhr.send(null);
    }

    function addUIListeners() {
        _get('button-parse').addEventListener('click', function() { parse(); });
        _get('button-manual').addEventListener('click', function() { annotate(); });
        //_get('button-note').addEventListener('click', function() { $.displayNote(); });
        _get('button-help').addEventListener('click', function() { showModal('help'); });
        _get('button-share').addEventListener('click', displayShareLink);
        _get('nav-icon').addEventListener('click', toggleSidenav);
        _get('displacy').addEventListener('mousedown', hideSidenav);
        _get('easteregg').addEventListener('click', easteregg);

        _get('theme_light').onchange = function() {
            if(this.checked) document.body.className = 'theme-light';
            else document.body.className = 'theme-dark';
        }

        _get('input').onkeydown = function(event) {
            if(event.keyCode == 13) {
                parse();
                this.blur();
            }
        }

        Array.from(document.querySelectorAll('.close')).forEach(function(button) {
            button.addEventListener('click', function() {
                hideModal(this.parentElement.parentElement.id)
            });
        });

        window.addEventListener('popstate', rewriteHistory);
    }

    function loading(status) {
        if(status) _get('loading').classList.add('active');
        else _get('loading').classList.remove('active');
    }

    function onStart() {
        loading(true);
        if($.request.text != $.defaults.text) _get('input').value = $.request.text;
    }

    function onSuccess() {
        loading(false);
        displayVersionString($.versionString);
        history.pushState({ request: $.request }, null, '');
    }

    function onFinal() {
        document.documentElement.scrollLeft = document.body.scrollLeft = 0;
    }

    function onErrors() {
        loading(false);
        showModal('error');
    }

    function rewriteHistory(event) {
        if(event.state && event.state.request) {
            if(event.state.request.mode == 'manual') annotate(event.state.request);
            else parse(event.state.request);

            _get('input').value = event.state.request.text || '';
        }
    }

    function displayToast(text) {
        var toast = _create('div', 'toast', 0, 0, text);

        setTimeout(function() {
            if(toast) toast.remove();
        }, 4000);

        document.body.appendChild(toast);
    }

    function displayShareLink() {
        loading(true);

        getShareLink(function(link) {
            loading(false);
            _get('share-link').value = link;
            showModal('share');
        });
    }

    function displayVersionString(version) {
        var container = _get('version-string');

        if(container && version) {
            container.innerHTML = 'spaCy v' + version;
        }
    }

    function playSound(sound) {
        var file = new Audio('/demos/displacy/sounds/' + sound);
        file.play();
    }

    function easteregg() {
        $.run({
            text: 'Never gonna give you up, never gonna let you down. Never gonna run around and desert you. Never gonna make you cry, never gonna say goodbye. Never gonna tell a lie and hurt you.'
        }, onStart, function() {
            onSuccess();
            hideSidenav();
            playSound('rickroll.m4a');
            document.body.className = 'theme-easteregg';
            document.body.appendChild(_create('button', 'panic-button', 0, 0, 'Make it stop!', function() {
                window.location.reload()
            }));
        }, onFinal, onErrors);
    }

    function showModal(id) {
        var modal = _get(id);
        if(modal && !modal.classList.contains('active')) {
            _animate(modal, 'intro');
            modal.classList.add('active');
        }
        else return false;
    }

    function hideModal(id) {
        var modal = _get(id);
        _animate(modal, 'exit');
        modal.classList.remove('active');
    }

    function showSidenav() {
        if(!_get('sidenav').classList.contains('active')) {
            _animate(_get('sidenav'), 'intro');
            _get('sidenav').classList.add('active');
            _get('nav-icon').classList.add('active');
        }
    }

    function hideSidenav() {
        if(_get('sidenav').classList.contains('active')) {
            _animate(_get('sidenav'), 'exit');
            _get('sidenav').classList.remove('active');
            _get('nav-icon').classList.remove('active');
        }
    }

    function toggleSidenav() {
        if(_get('sidenav').classList.contains('active')) hideSidenav();
        else if(!_get('sidenav').classList.contains('active')) showSidenav();
    }

    function _create(tag, classname, id, attributes, content, onclick) {
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

        if(content) element.appendChild(document.createTextNode(content));
        if(onclick) element.onclick = onclick;
        return element;
    }

    function _get(id) {
        return document.getElementById(id);
    }

    function _animate(element, type) {
        element.classList.add(type);

        setTimeout(function() {
            element.classList.remove(type);
        }, 250);
    }
})();
