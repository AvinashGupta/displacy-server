from __future__ import unicode_literals, print_function
import os
import json
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import newrelic.agent
newrelic.agent.initialize('newrelic.ini',
    os.environ.get('ENVIRONMENT', 'development'))

from flask import Flask, Response, request, jsonify, current_app, abort, render_template, send_from_directory
from flask_limiter import Limiter
from werkzeug.routing import BaseConverter
from flask.ext.cors import CORS

from .handlers import handle_parse, handle_manual
from .key import Key
from .log import Log
from . import util


class Server(Flask):
    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)

        util.set_config(self, 'ENVIRONMENT', 'development')
        util.set_config(self, 'DEBUG', True)
        util.set_config(self, 'API_URL', '/')

        util.set_config(self, 'AWS_ACCESS_KEY_ID', False)
        util.set_config(self, 'AWS_SECRET_ACCESS_KEY', False)
        util.set_config(self, 'AWS_REGION', 'eu-central-1')

        if self.config['ENVIRONMENT'] in ['production']:
            util.set_config(self, 'KEYS_TABLE', 'displacy-keys')
            util.set_config(self, 'LOGS_TABLE', 'displacy-logs')
        else:
            util.set_config(self, 'KEYS_TABLE', 'displacy-keys-dev')
            util.set_config(self, 'LOGS_TABLE', 'displacy-logs-dev')

        if self.config['AWS_ACCESS_KEY_ID']:
            self.keys = Key(
                access_key_id=self.config['AWS_ACCESS_KEY_ID'],
                secret_access_key=self.config['AWS_SECRET_ACCESS_KEY'],
                region=self.config['AWS_REGION'],
                table=self.config['KEYS_TABLE'])

            self.logs = Log(
                access_key_id=self.config['AWS_ACCESS_KEY_ID'],
                secret_access_key=self.config['AWS_SECRET_ACCESS_KEY'],
                region=self.config['AWS_REGION'],
                table=self.config['LOGS_TABLE'])
        else:
            self.keys = {}
            self.logs = []


app = newrelic.agent.WSGIApplicationWrapper(Server(
    __name__, static_url_path='/static', static_folder='../static',
    template_folder='../static'))
limiter = Limiter(app, headers_enabled=True, strategy='moving-window')
CORS(app)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter
def serve_dir(path, filename):
    return send_from_directory(os.path.join(app.static_folder, path), filename)


@app.route('/parse', methods=['POST'])
@limiter.limit('200/day')
def parse_endpoint():
    current_app.logs.append(request)
    model = handle_parse(request.json)
    return jsonify(model.to_json())


@app.route('/manual', methods=['POST'])
def manual_endpoint():
    model = handle_manual(request.json)
    return jsonify(model.to_json())


@app.route('/save', methods=['POST'])
def save_endpoint():
    if not request.json:
        abort(400)
    parse = json.dumps(request.json)
    key = str(abs(hash(parse)))
    current_app.keys[int(key)] = parse
    return jsonify({'key': key})


@app.route('/load/<key>', methods=['GET'])
def load_endpoint(key):
    if not key:
        abort(400)
    parse = current_app.keys.get(int(key))
    if not parse:
        abort(404)
    return jsonify(json.loads(parse) or {})


@app.route('/health')
def health():
    if not handle_parse({'text': 'test'}):
        abort(503)
    if not handle_manual({'text': 'test'}):
        abort(503)
    if not current_app.keys.status():
        abort(503)  # key service not available
    if not current_app.logs.status():
        abort(503)  # log service not available
    return jsonify({
        'status': 'ok'
    })


@app.route('/css/<path:path>')
def handle_css(path):
    return serve_dir('css', path)


@app.route('/fonts/<path:path>')
def handle_fonts(path):
    return serve_dir('fonts', path)


@app.route('/img/<path:path>')
def handle_img(path):
    return serve_dir('img', path)


@app.route('/js/<path:path>')
def handle_js(path):
    return serve_dir('js', path)


@app.route('/sounds/<path:path>')
def handle_sounds(path):
    return serve_dir('sounds', path)


@app.route('/')
def handle_root():
    return render_template('index.html', api_url='/')
