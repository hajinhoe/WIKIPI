from gevent.pywsgi import WSGIServer
from app import create_app

print("WIKIPI version 0.1 alpha.")
print("gevent server started.")
http_server = WSGIServer(('0.0.0.0', 3600), create_app())
http_server.serve_forever()