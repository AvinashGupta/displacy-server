from __future__ import unicode_literals, print_function
import os
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

import newrelic.agent
newrelic.agent.initialize('newrelic.ini',
    os.environ.get('ENVIRONMENT', 'development'))

from flask import Flask, request, jsonify, redirect

from .handlers import handle_parse, handle_manual


app = Flask(__name__, static_url_path='/displacy', static_folder='../static')
app.config['DEBUG'] = os.environ.get('DEBUG', 'True') != 'False'
app = newrelic.agent.WSGIApplicationWrapper(app)


def endpoint(make_model):
    if request.method == 'POST':
        model = make_model(request.json)
    else:
        model = make_model({'text': request.args.get('text', ''),
                            'actions': request.args.get('actions', '')})

    resp = jsonify(model.to_json())
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/api/displacy/parse/', methods=['GET', 'POST'])
def parse_endpoint():
    return endpoint(handle_parse)


@app.route('/api/displacy/manual/', methods=['GET', 'POST'])
def manual_endpoint():
    return endpoint(handle_manual)


@app.route('/health')
def health():
    if not handle_parse({'text': 'test'}):
        abort(503)  # index service not available
    if not handle_manual({'text': 'test'}):
        abort(503)  # action service not available
    return jsonify({
        'status': 'ok'
    })


@app.route('/')
@app.route('/displacy/')
@app.route('/displacy')
def root_endpoint():
    return redirect('/displacy/index.html?' + urlencode(request.args))
