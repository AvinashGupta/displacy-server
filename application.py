#!/usr/bin/env python
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

from displacy.handlers import handle_parse, handle_manual


application = Flask(__name__, static_url_path='/displacy')


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


@app.route('/')
@app.route('/displacy/')
@app.route('/displacy')
def root_endpoint():
    return redirect('/displacy/index.html?' + urlencode(request.args))


application.run(debug=os.environ.get('DEBUG', 'True') != 'False')


# code below needs to be converted to flask
# import sqlitedict

# class ServeLoad(object):
#     def on_get(self, req, resp, key='0'):
#         global db
#         parse = db.get(int(key), {})
#         resp.body = json.dumps(parse, indent=4)
#         resp.content_type = b'text/string'
#         resp.append_header(b'Access-Control-Allow-Origin', b"*")
#         resp.status = falcon.HTTP_200

# def handle_save(parse):
#     string = json.dumps(parse)
#     key = abs(hash(string))
#     db[key] = parse
#     return key

# db = sqlitedict.SqliteDict('tmp.db', autocommit=True)

# application.add_route('/api/displacy/save/', Endpoint(handle_save))
# application.add_route('/api/displacy/load/{key}', ServeLoad())
