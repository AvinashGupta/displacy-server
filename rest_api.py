#!/usr/bin/env python
from __future__ import unicode_literals
from __future__ import print_function
import sys
import sqlitedict

import falcon
import json
from os import path

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
app = falcon.API()

app.add_route('/api/displacy/parse/', Endpoint(handle_parse))
app.add_route('/api/displacy/manual/', Endpoint(handle_manual))
app.add_route('/api/displacy/save/', Endpoint(handle_save))
app.add_route('/api/displacy/load/{key}', ServeLoad())


if __name__ == '__main__':
    from wsgiref import simple_server
    httpd = simple_server.make_server('0.0.0.0', 8000, app)
    httpd.serve_forever()
