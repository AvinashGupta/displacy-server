import os

from displacy import app as application


if __name__ == '__main__':
    application.run()


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
