import copy
import random
import time
from typing import Dict, List
from graphql_relay.node.node import from_global_id
import re

from sqlalchemy import Enum
from general_functions.payload_request import PayloadRequest
from models.model_account import ModelAccount
from models.model_client import ModelClient
from models.model_product import ModelProduct
from models.model_product_request import ModelProductRequest

from models.model_request import ModelRequest
from models.model_request_log import ModelProductDetailLog, ModelRequestLog, ModelServiceDetailLog
from models.base import db_session
from models.model_service import ModelService
from models.model_service_request import ModelServiceRequest
from models.model_state_request import EnumState, ModelRequestState
from schemas.schema_request import Request

keys_names = ['id', 'id_contact', 'account_id',
              'id_entity', 'id_area', 'tickets_id', 'id_member',
              'id_client', 'id_account_receiver', 'id_product',
              'id_products', 'id_services', 'category_id', 'brand_id', 'news_list']
'''
def input_to_dictionary(input):
    """Method to convert Graphene inputs into dictionary"""
    dictionary = {}
    for key in input:
        # Convert GraphQL global id to database id
        if key[-2:] == 'id':
            input[key] = from_global_id(input[key])[1]
        dictionary[key] = input[key]
    return dictionary
'''


def input_to_dictionary(input):
    """Method to convert Graphene inputs into dictionary."""
    print("input: ", input)
    dictionary = input
    for key in input:
        # Convert GraphQL global id to models id
        if key in keys_names:
            
            if input[key] is not None:
                
                if isinstance(input[key], list):
                    decoded_list = []
                    for item in input[key]:
                        decoded_list.append(from_global_id(item)[1])
                    input[key] = decoded_list
                else:
                    dictionary[key] = (from_global_id(input[key])[1])

    print("dictionary:", dictionary)
    return dictionary


def input_to_dict_prod_serv(input):
    ''' Method to decode lists of products and services'''
    if len(input) == 0:
        return {}
    dictionary = copy.copy(input)
    for key in input:
        if input[key] is not None:
            dictionary[int(from_global_id(key)[1])] = dictionary[key]
            dictionary.pop(key)
    return dictionary


def evaluate_permissions(permissions, account: ModelAccount):
    '''
        Evaluates if the account exists and a list of permissions.
        Will give you an Exception if the Account lacks of some of
        the permissions passed.
    '''

    if account is None:
        raise Exception('Account does not exist. Check the token.')
    if not isinstance(permissions, list):
        raise Exception(
            'Function evaluate_permissions only accepts LIST as permissions parameter.')
    for p in permissions:
        account.has_perm(p)


def object_in_list(obj, list_obj):
    ''' Checks if an instance of product or service is inside the list
        of produts of a request instance.

        Returns index of product if it is inside or False if it isn't.
    '''
    if len(list_obj) != 0:
        if hasattr(list_obj[0], 'id_product'):
            for item in list_obj:
                if item.id_product == obj.id:
                    return list_obj.index(item)

        if hasattr(list_obj[0], 'id_service'):
            for item in list_obj:
                if item.id_service == obj.id:
                    return list_obj.index(item)
    return False


def requests_to_dict(requests: List[ModelRequest], is_admin: bool):
    '''
      Convert the request to a dict that can be emited in ws.
      Used only in the creation of the request


    '''
    list_requests: List[ModelRequest] = []

    # Pretty sure this is not the best way to do this.
    for request in requests:
        list_products: List[ModelProduct] = []
        list_services: List[ModelRequest] = []
        print(request)
        r = request.to_dict()
        r['state'] = request.state.to_dict()

        r['account_creator'] = request.account_creator.to_dict()
        if 'Role' in r['account_creator']:
            r['account_creator'].pop('Role')

        r['account_receiver'] = request.account_receiver.to_dict()
        if 'Role' in r['account_receiver']:
            r['account_receiver'].pop('Role')

        r['client'] = request.Client.to_dict()
        print(r['client'])
        if 'request' in r['state']:
            r['state'].pop('request')

        if isinstance(r['state'], dict):
            if 'state' in r['state']:
                if isinstance(r['state']['state'], EnumState):
                    r['state']['state'] = r['state']['state'].name

                elif isinstance(r['state']['state'], str):
                    print(f"state: {r['state']}")
                    r['state']['state'] = r['state']['state']
                else:
                    print(f"type: {type(r['state']['state'])}")

        for p in request.products:
            p_dict = p.to_dict()
            prod = (db_session.query(ModelProduct).filter_by(
                id=p_dict['id_product']).first()).to_dict()
            prod['amount'] = p_dict['amount']
            list_products.append(prod)

        for s in request.services:
            s_dict = s.to_dict()
            serv = (db_session.query(ModelService).filter_by(
                id=s_dict['id_service']).first()).to_dict()
            serv['amount'] = s_dict['amount']
            list_services.append(serv)

        r['products'] = list_products
        r['services'] = list_services
        list_requests.append(r)

    return list_requests

# def requests_to_dict_create_request(requests: list, is_admin: bool):
#     '''
#         Get requests from database and convert them into a dictionary.
#         Just take the ones BEFORE the last_edited parameter.
#     '''
#     list_requests: list = []
#     list_products: list = []
#     list_services: list = []

#     # Pretty sure this is not the best way to do this.
#     if is_admin:
#         for request in requests:
#             r = request.to_dict()
#             r['state'] = request.state.to_dict()
#             if 'request' in r['state']:
#                 r['state'].pop('request')
#             #if 'state' in r['state']:
#                 #r['state']['state'] = r['state']['state'].name
#                 #r['state'].pop('state')

#             for p in request.products:
#                 p_dict = p.to_dict()
#                 if 'product_ref' in p_dict:
#                     p_dict.pop('product_ref')
#                 list_products.append(p_dict)

#             for s in request.services:
#                 s_dict = s.to_dict()
#                 if 'service_ref' in s_dict:
#                     s_dict.pop('service_ref')
#                 list_services.append(s_dict)
#             r['products'] = list_products
#             r['services'] = list_services
#             list_requests.append(r)
#     else:
#         for request in requests:
#             if request.state.state.name == 'pending':
#                 r = request.to_dict()
#                 r['state'] = request.state.to_dict()
#                 if 'request' in r['state']:
#                     r['state'].pop('request')
#                 #if 'state' in r['state']:
#                 #    r['state']['state'] = r['state']['state'].name

#                 for p in request.products:
#                     p_dict = p.to_dict()
#                     if 'product_ref' in p_dict:
#                         p_dict.pop('product_ref')
#                     list_products.append(p_dict)

#                 for s in request.services:
#                     s_dict = s.to_dict()
#                     if 'service_ref' in s_dict:
#                         s_dict.pop('service_ref')
#                     list_services.append(s_dict)
#                 r['products'] = list_products
#                 r['services'] = list_services
#             list_requests.append(r)

#     return list_requests


def create_log(request_id: str, state: str, payload: str) -> None:
    '''
        This function creates the log for any request that was canceled
        or finished. That way the request in the table Request can be deleted.
    '''

    original_request = db_session.query(
        ModelRequest).filter_by(id=request_id).first()
    original_client = db_session.query(
        ModelClient).filter_by(id=original_request.id_client).first()
    original_account_creator = db_session.query(
        ModelAccount).filter_by(id=original_request.id_account_creator).first()
    original_account_receiver = db_session.query(
        ModelAccount).filter_by(id=original_request.id_account_receiver).first()
    original_detail_request = db_session.query(
        ModelRequestState).filter_by(id_request=original_request.id).first()
    original_detail_prod_request = db_session.query(
        ModelProductRequest).filter_by(id_request=original_request.id)
    original_detail_service_request = db_session.query(
        ModelServiceRequest).filter_by(id_request=original_request.id)
    request_log = ModelRequestLog()

    request_log.client_name = original_client.name
    request_log.client_phone = original_client.phone_number
    request_log.account_creator_name = original_account_creator.name
    request_log.account_creator_dni = original_account_creator.dni
    request_log.account_receiver_name = original_account_receiver.name
    request_log.account_receiver_dni = original_account_receiver.dni
    request_log.final_state = state
    request_log.detail = original_detail_request.detail
    request_log.final_price = original_request.final_price
    request_log.created = int(time.time())
    request_log.time_delivery = original_request.time_delivery
    request_log.direction = original_request.direction
    request_log.unique_id = original_request.unique_id

    if payload != None:
        request_log.associated_images = payload

    # Add detail to request_log
    for original_prod_detail in original_detail_prod_request:
        prod_log_detail = ModelProductDetailLog()
        product = db_session.query(
            ModelProduct).filter_by(id=original_prod_detail.id_product).first()
        prod_log_detail.product_name = product.name
        prod_log_detail.product_price = product.price
        prod_log_detail.amount_product = original_prod_detail.amount
        request_log.products_log.append(prod_log_detail)

    # Add detail to request_log
    for original_serv_detail in original_detail_service_request:
        serv_log_detail = ModelServiceDetailLog()
        service = db_session.query(
            ModelService).filter_by(id=original_serv_detail.id_service).first()
        serv_log_detail.service_name = service.name
        serv_log_detail.service_price = service.price
        serv_log_detail.amount_service = original_serv_detail.amount
        request_log.service_log.append(serv_log_detail)

    # Use the same session of the caller of the function so we dont need to commit here
    db_session.add(request_log)


def random_code_request() -> str:
    random_code = ''
    for _ in range(3):
        random_integer = random.randint(97, 97 + 26 - 1)
        flip_bit = random.randint(0, 1)
        random_integer = random_integer - 32 if flip_bit == 1 else random_integer
        random_code += (chr(random_integer))
    random_code += str(random.randint(100, 999))
    return random_code.upper()


def delete_finished_canceled_req(request: ModelRequest) -> None:
    '''
        This function is for a dirty operation of mine.
        It deletes the detail of a request and the request.
        A better solution is to read de docs and declare the models in another
        way so it uses the DELETE ON CASCADE functionality.
    '''
    prod_detail = db_session.query(
        ModelProductRequest).filter_by(id_request=request.id)

    serv_detail = db_session.query(
        ModelServiceRequest).filter_by(id_request=request.id)

    state_detail = db_session.query(
        ModelRequestState).filter_by(id_request=request.id)

    for p in prod_detail:
        db_session.delete(p)
    for s in serv_detail:
        db_session.delete(s)
    for d in state_detail:
        db_session.delete(d)
    db_session.delete(request)


def update_final_price_requests(id_prod_serv: str, insumo: str) -> None:
    '''
        This function does whats the name indicate it does.
        Don't excpect every comment to be redundant.
    '''
    involved_requests: ModelRequest = []

    if insumo == 'product':
        detail_prod_request = db_session.query(
            ModelProductRequest).filter_by(id_product=id_prod_serv)
        # Get all request ids that use the product / service
        for d in detail_prod_request:
            if d.id_request not in involved_requests:
                involved_requests.append(d.id_request)
    else:
        detail_serv_request = db_session.query(
            ModelServiceRequest).filter_by(id_service=id_prod_serv)
        # Get all request ids that use the product / service
        for d in detail_serv_request:
            if d.id_request not in involved_requests:
                involved_requests.append(d.id_request)

    for r in involved_requests:
        new_final_price: float = 0
        request = db_session.query(ModelRequest).filter_by(id=r).first()
        detail_prod_request = db_session.query(
            ModelProductRequest).filter_by(id_request=r)
        detail_serv_request = db_session.query(
            ModelServiceRequest).filter_by(id_request=r)

        for p in detail_prod_request:
            new_final_price += db_session.query(
                ModelProduct).filter_by(id=p.id_product).first().price * p.amount

        for s in detail_serv_request:
            new_final_price += db_session.query(
                ModelService).filter_by(id=s.id_service).first().price * s.amount

        # Update the prices on the requests
        request = db_session.query(
            ModelRequest).filter_by(id=r)
        request.update({'final_price': new_final_price})
        db_session.commit()


def create_dict_to_ws_emision(request_copy: dict, request: ModelRequest, state) -> dict:
    request_copy.pop('_sa_instance_state')
    requests_prods_copy = request.products.__dict__.copy()
    requests_servs_copy = request.services.__dict__.copy()
    requests_state_copy = request.state.__dict__.copy()

    request_copy['show_notification'] = True
    request_copy['products'] = []
    request_copy['services'] = []

    requests_state_copy.pop('_sa_instance_state')
    request_copy['state'] = {
        "detail": requests_state_copy['detail'],
        "state": state,
        "id_request": requests_state_copy['id_request'],
        "id": requests_state_copy['id']
        }

    '''
    for prod in requests_prods_copy['_sa_adapter'].data:
        del prod.__dict__['_sa_instance_state']
        request_copy['products'].append(prod.__dict__)

    for serv in requests_servs_copy['_sa_adapter'].data:
        del serv.__dict__['_sa_instance_state']
        request_copy['services'].append(serv.__dict__)
    '''
    for p in request.products:
        p_dict = p.to_dict()
        prod = (db_session.query(ModelProduct).filter_by(
            id=p_dict['id_product']).first()).to_dict()
        prod['amount'] = p_dict['amount']
        request_copy['products'].append(prod)

    for s in request.services:
        s_dict = s.to_dict()
        serv = (db_session.query(ModelService).filter_by(
            id=s_dict['id_service']).first()).to_dict()
        serv['amount'] = s_dict['amount']
        request_copy['services'].append(serv)

    return request_copy


class InputCheck():
    ''' Contains common checks in the input of the mutations '''

    def name_ok(self, name):
        ''' Checks for name lenght and if it only contains character (not number or spaces)'''

        if len(name) < 3 or not (name.isalpha()):
            return False
        return True

    def account_input_ok(self, data, editing: bool):
        ''' Checks for the input fields of Account '''

        if 'dni' in data:
            if len(data['dni']) < 8 or not (data['dni'].isdigit()):
                raise Exception(
                    f"|$AC1001 - Invalid dni. Should only contain numbers and be less or equal to 8 digits")
        if 'password' in data and not editing:
            if len(data['password']) < 7:
                raise Exception(
                    '|$AC1002 - The minimum required password length is 7')
        if 'name' in data:
            if len(data['name']) < 3 or not (all(chr.isalpha() or chr.isspace() for chr in data['name'])):
                raise Exception(
                    f"|$AC1003 - Invalid name. Should only contain letters and be greater than 3 characters")
        if 'phone_number' in data and data['phone_number'] != '':
            if data['phone_number'] != None and not data['phone_number'].isdigit():
                 raise Exception(
                    f"|$AC1010 - Invalid phone number. Should only contain numbers")
        if 'email' in data and data['email'] != None and data['email'] != '':
            regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
            if not (re.fullmatch(regex, data['email'])):
                 raise Exception(f"|$AC1011 - Invalid email. Is not a valid email")
        
         

    def product_service_input_ok(self, data):
        ''' Checks for the input fields of Product '''

        if 'name' in data:
            if len(data['name']) < 3 or data['name'] == None:
                raise Exception(
                    f"|$PRSE1003 - Invalid name. Should be greater than 3 characters")
        if 'price' in data:
            if data['price'] <= 0 or data['price'] == None:
                raise Exception(
                    f"|$PRSE1004 - Invalid price. Should be grater than 1 and can not be empty")

    def client_input_ok(self, data):
        ''' Checks for the input fields of Client '''

        if 'name' in data:
            if (len(data['name']) < 3) or not (bool(re.match('[a-zA-Z\s]+$', data['name']))):
                raise Exception(
                    f"|$CL1001 - Invalid name. Should only contain letters and be greater than 3 characters")
        if 'phone_number' in data:
            if len(data['phone_number']) <= 5 or not (data['phone_number'].isdigit()):
                raise Exception(
                    f"|$CL1002 - Invalid Phone Number. Should only contain numbers and be greater than 5 characters")

    def request_input_ok(self, data):
        ''' Checks for the basic input fields of Request '''

        if 'direction' in data:
            if len(data['direction']) <= 0:
                raise Exception(f" Direction can not be empty")

    def request_state_input_ok(self, data):
        '''
            Checks for the state on a Request
        '''
        possible_states = ['pending', 'finished', 'canceled', 'initiated']
        if data is not None:
            if data not in possible_states:
                raise Exception(
                    f" Request's state can only be pending, finished or canceled.")

    def request_list_prod_serv(self, prods: list, servs: list):
        '''
            Checks for the products and services listed on a Request 
        '''

        if prods is not None:
            for p in prods:
                if int(prods[p]) <= 0:
                    raise Exception(
                        f" The ammount requested for a product can not be cero")

        if servs is not None:
            for s in servs:
                if int(servs[s]) <= 0:
                    raise Exception(
                        f" The ammount requested for a service can not be cero")


def notify_change_of_request(request):
    '''
        This function marks the request as "finished" for the prior
        "owner" of the request so that request disappear from its device.
    '''
    request_copy = request.__dict__.copy()
    requests_state_copy = request.state.__dict__.copy()
    request_copy_to_emmit = create_dict_to_ws_emision(  request_copy, 
                                                        request, 
                                                        'finished')
    PayloadRequest.received_data([request_copy_to_emmit])

