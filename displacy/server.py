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

from flask import Flask, Response, request, jsonify, redirect, current_app, abort

from .handlers import handle_parse, handle_manual
from .key import Key
from .log import Log
from . import util


class Server(Flask):
    def __init__(self, *args, **kwargs):
        super(Server, self).__init__(*args, **kwargs)

        util.set_config(self, 'ENVIRONMENT', 'development')
        util.set_config(self, 'DEBUG', True)

        util.set_config(self, 'AWS_ACCESS_KEY_ID')
        util.set_config(self, 'AWS_SECRET_ACCESS_KEY')
        util.set_config(self, 'AWS_REGION', 'eu-central-1')

        if self.config['ENVIRONMENT'] in ['production']:
            util.set_config(self, 'KEYS_TABLE', 'displacy-keys')
            util.set_config(self, 'LOGS_TABLE', 'displacy-logs')
        else:
            util.set_config(self, 'KEYS_TABLE', 'displacy-keys-dev')
            util.set_config(self, 'LOGS_TABLE', 'displacy-logs-dev')

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


app = newrelic.agent.WSGIApplicationWrapper(Server(
    __name__, static_url_path='/displacy', static_folder='../static'))


def set_headers(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/api/displacy/parse/', methods=['POST'])
def parse_endpoint():
    current_app.logs.create('parse', request)
    model = handle_parse(request.json)
    resp = jsonify(model.to_json())
    return set_headers(resp)


@app.route('/api/displacy/manual/', methods=['POST'])
def manual_endpoint():
    model = handle_manual(request.json)
    resp = jsonify(model.to_json())
    return set_headers(resp)


@app.route('/api/displacy/save/', methods=['POST'])
def save_endpoint():
    parse = json.dumps(request.json)
    key = abs(hash(parse))
    current_app.keys.put(key, parse)
    resp = Response(str(key), mimetype='text/plain')
    return set_headers(resp)


@app.route('/api/displacy/load/<key>')
def load_endpoint(key='0'):
    parse = current_app.keys.get(key)
    if not parse:
        abort(404)
    resp = jsonify(json.loads(parse))  # ensure it's json?
    return set_headers(resp)


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


@app.route('/')
@app.route('/displacy/')
@app.route('/displacy')
def root_endpoint():
    return redirect('/displacy/index.html?' + urlencode(request.args))