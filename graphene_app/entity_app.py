import os
import datetime
from graphql_ws.gevent import GeventSubscriptionServer
from models.base import db_session
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename
from flask_cors import CORS
from graphql_auth import (
    GraphQLAuth,
)
from flask_sockets import Sockets
from flask_graphql import GraphQLView
from schemas.schema import schema
from general_functions.log_implementation import logger
import pathlib

app = Flask(__name__)
CORS(app)

UPLOAD_IMAGES = './images_folder'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'sql', 'sh', 'jpeg'}
URL_SERVER = 'http://192.168.100.200'

# Auth stuff
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_IMAGES'] = UPLOAD_IMAGES
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config["JWT_SECRET_KEY"] = os.environ['JWT_SECRET_KEY']
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(weeks=5215)
auth = GraphQLAuth(app)

app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))
app.app_protocol = lambda environ_path_info: 'graphql-ws'  # type: ignore

subscription_server = GeventSubscriptionServer(schema)
sockets = Sockets(app)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@sockets.route('/subscriptions')
def echo_socket(ws):
    #print(dict(request.headers))
    #subscription_server.keep_alive = True
    subscription_server.handle(ws)
    return []


@app.route('/uploaded_files', methods=['POST'])
def upload_file():
    '''
        All files are uploaded to the same endponit. 
        This funciton decides where to put the files according to its extension
        
        The folder where the files are located are exposed through nginx so clients can acces to it!
    '''

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            raise Exception("No files in request!")
        file = request.files['file']  # type: ignore
        if file.filename == '':
            raise Exception("Files can not have empty names")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            # Save the upload in the shared volume
            logger.info(f"Saving uploaded file for {file.filename}")


            # Get file extension
            file_extension = pathlib.Path(file.filename).suffix
            if (file_extension == '.sql'):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                logger.info(f"{file.filename} saved!")
                # Restore the backup
                logger.info(f"Passing restore instruction to pipe!")
                command:str = f'echo "./restore_db.sh {file.filename}" > host_gateway_pipe'
                os.system(command)
                return {'ok' : True} 
            else: 
                file.save(os.path.join(app.config['UPLOAD_IMAGES'] , filename))
                logger.info(f"{file.filename} saved!")
    return {'ok' : True} 

