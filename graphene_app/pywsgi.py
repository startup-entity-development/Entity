from gevent import monkey
monkey.patch_all()
from geventwebsocket.handler import WebSocketHandler
from gevent.pywsgi import WSGIServer
from nordeste_app import app
import os


server = WSGIServer(
    ('0.0.0.0', int(os.environ['PORT_APP'])), app, handler_class=WebSocketHandler,)
server.serve_forever()
 
