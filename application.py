#!/usr/bin/env python
from __future__ import unicode_literals, print_function
import sys
import sqlitedict
import mimetypes
import json
import os
import io

import newrelic.agent
newrelic.agent.initialize('newrelic.ini',
    os.environ.get('ENVIRONMENT', 'development'))

import falcon

from displacy.handlers import handle_parse, handle_manual


try:
  unicode
except NameError:
  unicode = str


class Endpoint(object):
    def __init__(self, make_model):
        self.make_model = make_model

    def set_header(self, resp):
        resp.content_type = b'text/string'
        resp.append_header(b'Access-Control-Allow-Origin', b"*")
        resp.status = falcon.HTTP_200

    def set_body(self, resp, parse):
        if hasattr(parse, 'to_json'):
            resp.body = json.dumps(parse.to_json(), indent=4)
        else:
            resp.body = json.dumps(parse)

    def on_get(self, req, resp, text="", actions=""):
        if not isinstance(text, unicode):
            text = text.decode('utf8')
        self.set_body(resp, self.make_model({"text": text, "actions": actions}))
        self.set_header(resp)

    def on_post(self, req, resp, text="", actions=""):
        body_bytes = req.stream.read()
        json_data = json.loads(body_bytes.decode('utf8'))
        self.set_body(resp, self.make_model(json_data))
        self.set_header(resp)


class ServeLoad(object):
    def on_get(self, req, resp, key='0'):
        global db
        parse = db.get(int(key), {})
        resp.body = json.dumps(parse, indent=4)
        resp.content_type = b'text/string'
        resp.append_header(b'Access-Control-Allow-Origin', b"*")
        resp.status = falcon.HTTP_200


def handle_save(parse):
    string = json.dumps(parse)
    key = abs(hash(string))
    db[key] = parse
    return key


db = sqlitedict.SqliteDict('tmp.db', autocommit=True)
application = falcon.API()

application.add_route('/api/displacy/parse/', Endpoint(handle_parse))
application.add_route('/api/displacy/manual/', Endpoint(handle_manual))
application.add_route('/api/displacy/save/', Endpoint(handle_save))
application.add_route('/api/displacy/load/{key}', ServeLoad())


# FIXME: falcon isn't good at serving static content
class StaticFile(object):
    def on_get(self, req, resp, filename='index.html', directory=''):
        full_path = os.path.join(os.path.dirname(__file__),
                                 'frontend', directory, filename)

        content_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'
        resp.content_type = content_type.encode('ascii')
        resp.body = io.open(full_path, 'rb').read()


class Root(object):
    def on_get(self, req, resp):
        query = ''
        if req.params:
            query = '?' + urlencode(req.params)
        url = '/displacy/index.html' + query
        resp.append_header(b'Location', url.encode('ascii'))
        resp.status = falcon.HTTP_301


application.add_route('/displacy/{directory}/{filename}', StaticFile())
application.add_route('/displacy/index.html', StaticFile())

# redirects
application.add_route('/displacy', Root())  # includes /displacy/
application.add_route('/', Root())


if __name__ == '__main__':
    from wsgiref import simple_server
    httpd = simple_server.make_server('127.0.0.1', 8000, application)
    httpd.serve_forever()
else:
    application = newrelic.agent.WSGIApplicationWrapper(application)
