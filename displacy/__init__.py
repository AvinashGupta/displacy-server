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

from flask import Flask, Response, request, jsonify, redirect
import sqlitedict

from .handlers import handle_parse, handle_manual


app = Flask(__name__, static_url_path='/displacy', static_folder='../static')
app.config['DEBUG'] = os.environ.get('DEBUG', 'True') != 'False'
app = newrelic.agent.WSGIApplicationWrapper(app)


db = sqlitedict.SqliteDict('tmp.db', autocommit=True)


def set_headers(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/api/displacy/parse/', methods=['POST'])
def parse_endpoint():
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
    db[key] = parse
    resp = Response(str(key), mimetype='text/plain')
    return set_headers(resp)


@app.route('/api/displacy/load/<key>')
def load_endpoint(key='0'):
    parse = json.loads(db.get(int(key), '{}'))
    resp = jsonify(parse)
    return set_headers(resp)


@app.route('/health')
def health():
    if not handle_parse({'text': 'test'}):
        abort(503)
    if not handle_manual({'text': 'test'}):
        abort(503)
    return jsonify({
        'status': 'ok'
    })


@app.route('/')
@app.route('/displacy/')
@app.route('/displacy')
def root_endpoint():
    return redirect('/displacy/index.html?' + urlencode(request.args))
