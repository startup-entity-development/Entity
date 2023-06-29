
import datetime
import json
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

from models.model_request_log import ModelRequestLog


def create_file(requestLog: ModelRequestLog, client_folder_path:str) -> None:
    created:datetime = datetime.fromtimestamp(int(requestLog.created))
    delivery:datetime = datetime.fromtimestamp(int(requestLog.time_delivery))

    final_state: str = ""
    if (requestLog.final_state == "finished"):
        final_state = "Finalizado"
    if (requestLog.final_state == "canceled"):
        final_state = "Cancelado"

    with open(f'{client_folder_path}/{created.strftime("%d-%m-%y__%H:%M:%S")}.txt', 'w') as f:
        f.write(f'             --------{requestLog.unique_id}--------\n')
        f.write(f'Creador del trabajo:        {requestLog.account_creator_name} - {requestLog.account_creator_dni}\n')
        f.write(f'Trabajador asignado:        {requestLog.account_receiver_name} - {requestLog.account_receiver_dni}\n')
        f.write(f'Cliente:                    {requestLog.client_name} - {requestLog.client_phone}\n')
        f.write(f'Fecha de creación:          {created.strftime("%d/%m/%y %H:%M")}\n')
        f.write(f'Fecha de arribo:            {delivery.strftime("%d/%m/%y %H:%M")}\n')
        f.write(f'Detalle:                    {requestLog.detail}\n')
        f.write(f'Dirección:                  {requestLog.direction}\n')
        f.write(f'Precio final:               ${requestLog.final_price}\n')
        f.write(f'Estado final:               {final_state}\n')
        f.write(f'\n')
        f.write(f'\n')
        f.write(f'                ### PRODUCTOS ###\n')
        if(len(requestLog.products_log) == 0):
            f.write(f'Sin productos.\n')
        else:
            for p in requestLog.products_log:
                f.write(f'------------------------------------------------\n')
                f.write(f'Nombre:                     {p.product_name}\n')
                f.write(f'Cantidad                    {p.amount_product}\n')
                f.write(f'Precio producto:            ${p.product_price}\n')
        f.write(f'\n')
        f.write(f'\n')
        f.write(f'                ### SERVICIOS ###\n')
        if(len(requestLog.service_log) == 0):
            f.write(f'Sin servicios.\n')
        else:
            for s in requestLog.service_log:
                f.write(f'------------------------------------------------\n')
                f.write(f'Nombre:                     {s.service_name}\n')
                f.write(f'Cantidad                    {p.amount_service}\n')
                f.write(f'Precio servicio:            ${p.service_price}\n')


def delete_all_files_on_folder(folder_path:str) -> None:
    '''
        Deletes all the folder, images, and text files
        in the backups_folder folder.
    '''
    for root, dirs, files in os.walk(folder_path):
        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))

def delete_previous_zip_backup() -> None:
    if (os.path.exists('/app/backups_folder/backups_folder.zip')):
        os.unlink('/app/backups_folder/backups_folder.zip')

def create_client_folder(client:ModelClient) -> str:
    path_client_folder:str = f'backups_folder/requests_backups/{client.phone_number}_{client.name}'
    os.mkdir(path_client_folder)
    return path_client_folder

def create_request_folder(client_folder_path:str, epoch_creation_time) -> str:
    created:datetime = datetime.fromtimestamp(epoch_creation_time)
    path_request_folder = client_folder_path + f'/{created.strftime("%d-%m-%y__%H:%M")}'
    os.mkdir(path_request_folder)
    return path_request_folder


def create_zip_file() -> None:

    archived = shutil.make_archive( base_name='backups_folder', 
                                    format='zip', 
                                    root_dir='/app/backups_folder/', 
                                    base_dir='/app/backups_folder/requests_backups')
    shutil.move('/app/backups_folder.zip', '/app/backups_folder')


def move_images_to_client_folder(associated_images:str, client_request_path_folder:str):
    if (associated_images != ''):
        images = json.loads(associated_images)
        for image in images:
            image_path:str = '/app/' + image[image.rfind('/images_folder/'):]
            if (os.path.exists(image_path)): 
                shutil.move(image_path, client_request_path_folder)

