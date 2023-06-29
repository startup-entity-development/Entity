import datetime
import json
from general_functions.backup_functions import *
from models.model_account import ModelAccount
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (mutation_header_jwt_required, get_jwt_claims)
import os
from general_functions.log_implementation import logger
import time
from datetime import datetime
from models import base as b
import shutil
from models.model_client import ModelClient
from models.model_product_request import ModelProductRequest

from models.model_request_log import ModelRequestLog
from models.model_service_request import ModelServiceRequest


class CreateBackUpAttribute:
    create_backup = graphene.Boolean(description="If true, create a backup of the database")

class CreateBackUpInput(graphene.InputObjectType, CreateBackUpAttribute):
    pass

class CreateBackUp(graphene.Mutation):
    """ 
        - Mutation for creating a backUp.
        Process is documented in a private folder.
    """
    backup_ok = graphene.Boolean(description="if true means that the zip file was created")

    class Arguments:
        input = CreateBackUpInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        # # Who is trying to create the backup?
        # id_account_token = int(get_jwt_claims()['id'])
        # account = db_session.query(ModelAccount).get(id_account_token)
        
        # # We check for this perm cause only admins have it.
        # # Actually we should create a custom perm for this (no need for the moment)
        # perms = ['product.add']
        # utils.evaluate_permissions(perms, account)
        # data:dict = utils.input_to_dictionary(input)
        # create_backup:str = data.get('create_backup')  # type: ignore

        # if (create_backup == True):
        #     today = datetime.datetime.today()
        #     backup_name:str = "nordeste_backup_" + today.strftime('%d_%m_%Y')
        #     logger.info(f"Name of backup file {backup_name}!")
            
        #     """
        #      IMPORTANT: 
        #            - Consider that the file dump_db.sh should be reachable for the pipe! 
        #            - We do not pass .sql in this context cause the dump_db.sh does this for us. 
        #     """
            
        #     # Create the command that will be passed to the pipe.assert
        #     # In theory, the pipe context is the host_container_pipe folder (host) OR "/" OR /home/ (host)".
        #     command:str = f'echo "./dump_db.sh {backup_name}" > host_gateway_pipe'
        #     logger.info(command)
        #     logger.info(f"About to pass the command to the pipe!!")
        #     os.system(command) 
        #     logger.info(f"Backup comand passed to the pipe!!")
        #     time.sleep(1)
            
        #     # Check if the backup is already created
        #     i = 0
        #     path = './backups_folder/' + backup_name + ".sql"
        #     logger.info(f"Path where to look: {path}")
        #     while i < 10:
        #         logger.info(f"Waiting for {i} seconds")
        #         i = i + 1
        #         backup_created = os.path.exists(path)
        #         if backup_created:
        #             logger.info("Backup founded!")
        #             return CreateBackUp(name_backup=backup_name + ".sql")
        #         time.sleep(1)
        clients: list[ModelClient] = b.db_session.query(ModelClient).all()
        delete_all_files_on_folder('backups_folder/requests_backups/')
        delete_previous_zip_backup()
        for c in clients:
            request_logs:list[ModelRequestLog] = b.db_session.query(ModelRequestLog).filter_by(client_phone=c.phone_number).all()
            if len(request_logs) == 0:
                pass
            else:
                client_folder_path:str = create_client_folder(c)
                for r in request_logs:
                    request_path:str = create_request_folder(client_folder_path, r.created)
                    move_images_to_client_folder(r.associated_images, request_path)
                    create_file(r, request_path)
        create_zip_file()
        delete_all_files_on_folder('backups_folder/requests_backups/')

        if os.path.exists('/app/backups_folder/backups_folder.zip'):
            return CreateBackUp(backup_ok=True)
        else:
            return CreateBackUp(backup_ok=False)



class ConfirmationBackUpAttribute:
    confirmation = graphene.Boolean(description="If true, means that the backup zip file have been downloaded")

class ConfirmationBackUpInput(graphene.InputObjectType, ConfirmationBackUpAttribute):
    pass

class ConfirmationBackUp(graphene.Mutation):
    """ 
        - Mutation to know when we can delete everything on the LOGS of the database.
    """
    confirmation = graphene.Boolean(description="if true menad that all the data was deleted on backend", required=True)

    class Arguments:
        input = ConfirmationBackUpInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        everything_ok: bool = False
        if (input['confirmation']) == True:
            delete_previous_zip_backup()
            b.db_session.query(ModelProductRequest).delete()
            b.db_session.query(ModelServiceRequest).delete()
            b.db_session.query(ModelRequestLog).delete()
            b.db_session.commit()
            delete_all_files_on_folder('images_folder/')
            everything_ok = True
        return ConfirmationBackUp(confirmation=everything_ok)
