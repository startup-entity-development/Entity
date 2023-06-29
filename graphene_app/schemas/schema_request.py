import json
import time
from flask import request
from graphene_sqlalchemy import SQLAlchemyObjectType
from mysqlx import IntegrityError
import requests
import sqlalchemy
from graphql_auth.decorators import verify_jwt_in_argument
from rx import Observable

# Models
from models.model_account import ModelAccount
from models.model_client import ModelClient
from models.model_request import ModelRequest
from models.model_product import ModelProduct
from models.model_product_request import ModelProductRequest
from models.model_request_log import ModelProductDetailLog, ModelRequestLog, ModelServiceDetailLog
from models.model_service import ModelService
from models.model_service_request import ModelServiceRequest
from models.model_state_request import ModelRequestState
from models.model_role import ModelRole

from general_functions.payload_request import PayloadRequest

import graphene
from graphene import JSONString
from general_functions import utils
from models.base import db_session
from graphql_auth import (
    mutation_jwt_refresh_token_required, get_jwt_identity,
    create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims
)


def request_redirecter(rq: dict, id_account_token):
    if int(rq['id_account_creator']) == id_account_token:
        return rq
    if int(rq['id_account_receiver']) == id_account_token:
        return rq


class RequestProducts(SQLAlchemyObjectType):
    """RequestProducts node."""

    class Meta:
        model = ModelProductRequest
        interfaces = (graphene.relay.Node,)


class RequestServices(SQLAlchemyObjectType):
    """RequestServices node."""

    class Meta:
        model = ModelServiceRequest
        interfaces = (graphene.relay.Node,)


class RequestState(SQLAlchemyObjectType):
    """RequestState node."""

    class Meta:
        model = ModelRequestState
        interfaces = (graphene.relay.Node,)

class RequestLog(SQLAlchemyObjectType):
    """RequestLog node."""

    class Meta:
        model = ModelRequestLog
        interfaces = (graphene.relay.Node,)

class RequestProductsLog(SQLAlchemyObjectType):
    """RequestProductsLog node."""

    class Meta:
        model = ModelProductDetailLog
        interfaces = (graphene.relay.Node,)

class RequestServicesLog(SQLAlchemyObjectType):
    """RequestServicesLog node."""

    class Meta:
        model = ModelServiceDetailLog
        interfaces = (graphene.relay.Node,)


class RequestAttribute:
    id_client = graphene.ID(
        description="Id of the Client in the request", required=True)
    id_account_receiver = graphene.ID(
        description="The account responsable of the Request", required=True)
    time_delivery = graphene.String(
        description="Aprox time of arrive for the employee to do the work", required=True)
    direction = graphene.String(
        description="Where the employee have to go")
    detail = graphene.String(
        description="Details of the Request. Could be edited by the admin and by sellsman")
    id_products = graphene.JSONString(
        description="Product listed in the request")
    id_services = graphene.JSONString(
        description="Service listed in the request")


class UpdateRequestInput(graphene.InputObjectType):
    """Arguments to update a Product ."""
    id = graphene.ID(description="Id of the Request.", required=True)
    detail = graphene.String(
        description="Details of the Request. Could be edited by the admin and by sellsman")
    state = graphene.String(description="State of the request")
    payload = graphene.String(description='A json list string with the names of the iamges associated to a request')


class UpdateRequest(graphene.Mutation):
    """Mutation to update a Request.

        Returns true if the Requests was marked finished or canceled. 
        This also means that the request was deleted from the table Requests and 
        moved to reques_log. 
        
        - handles the image part of the request just saving the payload to the request_log

    """

    # Fields that the mutation can return
    was_updated = graphene.Boolean(
        description="if the account was updated and deleted from Requests table return true.")

    # Fields that the mutation takes as input
    class Arguments:
        input = UpdateRequestInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):

        input = dict(input)
        detail = None
        state = None
        was_updated: bool = False

        # Who is trying to update the Request?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['request.update']
        utils.evaluate_permissions(perms, account)

        if 'detail' in input:
            detail = input['detail']
            input.pop('detail')

        if 'state' in input:
            state = input['state']
            input.pop('state')

        data = utils.input_to_dictionary(input)
        utils.InputCheck().request_state_input_ok(state)

        # Update request state
        if state is not None:
            state_request = db_session.query(
                ModelRequestState).filter_by(id_request=data['id'])
            state_request.update({
                "state": state
            })

        if detail is not None:
            state_request = db_session.query(
                ModelRequestState).filter_by(id_request=data['id'])
            state_request.update({
                "detail": detail
            })

        request = db_session.query(
            ModelRequest).filter_by(id=data['id'])
        request.update({
            "edited": int(time.time())
        })
        
        # Get, again, request from db
        request = db_session.query(
            ModelRequest).filter_by(id=data['id']).first()
        # Create a copy of the request so the original objetc does not get SHITED
        request_copy = request.__dict__.copy()
        
        
        
        if state == 'finished' or state == 'canceled':
            # Create log and delete
            if ('payload' in data):
                utils.create_log(data['id'], state, data['payload'])
            else: 
                utils.create_log(data['id'], state, None)
            utils.delete_finished_canceled_req(request)
            
            """
            request_copy.pop('_sa_instance_state')
            requests_prods_copy = request.products.__dict__.copy()
            requests_servs_copy = request.services.__dict__.copy()
            requests_state_copy = request.state.__dict__.copy()
            
            request_copy['show_notification'] = True
            request_copy['products'] = []
            request_copy['services'] = []
        
            requests_state_copy.pop('_sa_instance_state')
            request_copy['state'] = {
                "detail" : requests_state_copy['detail'],
                "state" : state,
                "id_request" : requests_state_copy['id_request'],
                "id" : requests_state_copy['id']
            }

            for prod in requests_prods_copy['_sa_adapter'].data:
                del prod.__dict__['_sa_instance_state']
                request_copy['products'].append(prod.__dict__)

            for serv in requests_servs_copy['_sa_adapter'].data:
                del serv.__dict__['_sa_instance_state']
                request_copy['services'].append(serv.__dict__)
            """
            request_copy_to_emmit = utils.create_dict_to_ws_emision(request_copy, request, state)
            
            #req_dict = utils.requests_to_dict([request], True)
            #request_copy['show_notification'] = True
            PayloadRequest.received_data([request_copy_to_emmit])
            request = db_session.query(
            ModelRequest).filter_by(id=data['id']).first()

        if state == 'initiated':
            request_copy_to_emmit = utils.create_dict_to_ws_emision(request_copy, request, state)
            request_copy_to_emmit['client'] = request.Client.to_dict()
            request_copy_to_emmit['account_creator'] = request.account_creator.to_dict()
            request_copy_to_emmit['account_receiver'] = request.account_receiver.to_dict()
            PayloadRequest.received_data([request_copy_to_emmit])

            
        was_updated = True
        db_session.commit()
        return UpdateRequest(was_updated=was_updated)


class UpdateFullRequestInput(graphene.InputObjectType):
    """Arguments to update a Request ."""
    id = graphene.ID(description="Id of the Request.", required=True)
    id_client = graphene.ID(description="Id of the Client in the request")
    id_account_receiver = graphene.ID(description="The account responsable of the Request")
    time_delivery = graphene.String(
        description="Aprox time of arrive for the employee to do the work")
    direction = graphene.String(description="Where the employee have to go")
    detail = graphene.String(
        description="Details of the Request. Could be edited by the admin and by sellsman")
    id_products = graphene.JSONString(
        description="Product listed in the request")
    id_services = graphene.JSONString(
        description="Service listed in the request")

class UpdateFullRequest(graphene.Mutation):
    ''' 
        Mutation to update all the fields in a Request. 
        Returns the edited request. 
    '''

    request = graphene.Field(
        lambda: Request, description='Request edited by this mutation')
    
    # Fields that the mutation takes as input
    class Arguments:
        input = UpdateFullRequestInput(required=True)
    
    @mutation_header_jwt_required
    def mutate(self, info, input):
        input = dict(input)
        
        product_dict = None
        service_dict = None

        service_detail: list = []
        product_detail: list = []
        final_price_request: float = 0.0
        detail = None

        # Who is trying to update the Request?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['request.update']
        utils.evaluate_permissions(perms, account)

        # Cleaning data for the request
        if 'id_products' in input:
            if input['id_products'] != '':
                product_dict = utils.input_to_dict_prod_serv(
                    input['id_products'])
                input.pop('id_products')
            else:
                raise Exception(f" List of products can not be empty")
        if 'id_services' in input:
            if input['id_services'] != '':
                service_dict = utils.input_to_dict_prod_serv(
                    input['id_services'])
                input.pop('id_services')
            else:
                raise Exception(f" List of services can not be empty")

        data = utils.input_to_dictionary(input)

        # Is the input ok?
        utils.InputCheck().request_input_ok(data)
        utils.InputCheck().request_list_prod_serv(product_dict, service_dict)
        
        # Does the request exist?
        try:
            request = db_session.query(ModelRequest).filter_by(id=data['id'])
            request[0].id
        except Exception as e:
            raise Exception(f' Request does not exist. Error: {e.__cause__}')

        # Delete current detail of prods and replace it for the new one
        prod_detail = db_session.query(
                    ModelProductRequest).filter_by(id_request=request[0].id)
        for p in prod_detail:
            db_session.delete(p)
        
        if product_dict:
            # Create objects and recalculate final price according to what we need  
            for prod in product_dict:
                prod_detail = ModelProductRequest()
                try:
                    prod_db = db_session.query(ModelProduct).get(prod)
                    prod_db.id
                except Exception as e:
                    raise Exception(
                        f' Product does not exist. Error: {e.__cause__}')
                prod_detail.amount = product_dict[prod]
                prod_detail.product_ref = prod_db
                prod_detail.id_request = request[0].id
                db_session.add(prod_detail)
                final_price_request += prod_db.price * prod_detail.amount

        # Delete current detail of services and replace it for the new one
        serv_detail = db_session.query(
                ModelServiceRequest).filter_by(id_request=request[0].id)
        for s in serv_detail:
            db_session.delete(s)
        
        if service_dict:
            # Create objects and recalculate final price according to what we need  
            for serv in service_dict:
                serv_detail = ModelServiceRequest()
                try:
                    serv_db = db_session.query(ModelService).get(serv)
                    serv_db.id
                except Exception as e:
                    raise Exception(
                        f' Service does not exist. Error: {e.__cause__}')
                serv_detail.amount = service_dict[serv]
                serv_detail.service_ref = serv_db
                serv_detail.id_request = request[0].id
                db_session.add(serv_detail)
                final_price_request += serv_db.price * serv_detail.amount
        
        # Update final price if needed
        if final_price_request != 0.0:
            request.update({
                'final_price' : final_price_request
            })

        # Update detail if needed 
        if 'detail' in input and input['detail'] != '':
            detail = input['detail']
            input.pop('detail')
            if detail is not None:
                state_request = db_session.query(
                    ModelRequestState).filter_by(id_request=data['id'])
                state_request.update({
                    "detail": detail
                })
        
        # Get amd update client if needed 
        if 'id_client' in data and data['id_client'] != '':
            try:
                client = db_session.query(ModelClient).get(data['id_client'])
                request.update({
                    "id_client": client.id
                })
            except Exception as e:
                raise Exception(f' Client does not exist. Error: {e.__cause__}')
        
        # Get amd update account receiver if needed 
        if 'id_account_receiver' in data and data['id_account_receiver'] != '':
            try:
                account_receiver = db_session.query(ModelAccount).get(data['id_account_receiver'])
                
                # important! 
                if (account_receiver.id != request[0].id_account_receiver):
                    utils.notify_change_of_request(request[0])
                
                request.update({
                    "id_account_receiver": account_receiver.id
                })
            except Exception as e:
                raise Exception(f' Account receiver does not exist. Error: {e.__cause__}')

        if 'time_delivery' in data and data['time_delivery'] != '':
            request.update({
                    "time_delivery": data['time_delivery']
            })

        if 'direction' in data and data['direction'] != '':
              request.update({
                    "direction": data['direction']
            })
        
        request.update({
            "edited": str(int(time.time()))
        })

        # Save into DB
        db_session.commit()

        # Emmit changes via ws
        request_to_emmit =  db_session.query(ModelRequest).filter_by(id=data['id']).first()
        request_copy = request_to_emmit.__dict__.copy()
        requests_state_copy = request_to_emmit.state.__dict__.copy()
        request_copy_to_emmit = utils.create_dict_to_ws_emision(request_copy, 
                                                                request_to_emmit, 
                                                                requests_state_copy['state'].name)
        request_copy_to_emmit['client'] = request_to_emmit.Client.to_dict()
        request_copy_to_emmit['account_creator'] = request_to_emmit.account_creator.to_dict()
        request_copy_to_emmit['account_receiver'] = request_to_emmit.account_receiver.to_dict()

        PayloadRequest.received_data([request_copy_to_emmit])
            
        #db_session.commit()
        return UpdateFullRequest(request=None)


class Request(SQLAlchemyObjectType):
    """Request node."""

    class Meta:
        model = ModelRequest
        interfaces = (graphene.relay.Node,)


class CreateRequestInput(graphene.InputObjectType, RequestAttribute):
    """Arguments to create a Request."""
    pass


class SubscriptionRequest(graphene.ObjectType):
    account_subscription = graphene.String(
        token=graphene.String(required=True),
        last_edit=graphene.String())

    # subscription
    def resolve_account_subscription(root, context, token: str, last_edit: int = 0):
        context_request = Request.get_query(context)
        list_requests: list = []
        is_admin = False
        last_edit = int(last_edit)
        ''' 
            Filter the requests that belongs to an account and emits them over websocket.  
        '''

        # Get token from account
        try:
            verify_jwt_in_argument(token)
            id_account_token = int(get_jwt_claims()['id'])
        except Exception as e:
            raise Exception(f"Token not valid - Exeption Authorization, {e}")

        # Get account
        try:
            account = db_session.query(ModelAccount).get(id_account_token)
            if account.Role.name == 'admin':
                is_admin = True
        except Exception as e:
            raise Exception(f" Account not found: {e}")

        # Which requests are we getting?
        if is_admin:
            requests = context_request.filter((ModelRequest.id_account_creator == id_account_token)
                                              & (ModelRequest.edited >= last_edit)).all()
        else:
            requests = context_request.filter((ModelRequest.id_account_receiver == id_account_token)
                                              & (ModelRequest.edited >= last_edit)).all()

        list_requests = utils.requests_to_dict(requests, is_admin)

        # Literally some magic things happen here but it works.
        obs_rq = Observable.from_(list_requests).map(lambda rq: json.dumps(rq))
        obs_rq_queue = Observable.interval(
            1).take(1).flat_map(lambda x: obs_rq)
        obs_rq_incoming = PayloadRequest.incoming_request.\
            filter(lambda rq: request_redirecter(rq, id_account_token)).map(
                lambda rq: json.dumps(rq))
        all_obs = Observable.merge(obs_rq_queue, obs_rq_incoming)

        return all_obs


class CreateRequest(graphene.Mutation):

    """Mutation to create a Request."""

    # Fields that the mutation can return
    request = graphene.Field(
        lambda: Request, description="Request node created by this mutation.")

    # Fields that the mutation takes as input
    class Arguments:
        input = CreateRequestInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        product_dict: dict = None
        service_dict: dict = None
        service_detail: list = []
        product_detail: list = []
        detail: str = None
        final_price_request: float = 0.0
        generate_code_again: bool = True

        # Who is trying to create the Request?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['request.add']
        utils.evaluate_permissions(perms, account)

        # Cleaning data for the request
        if 'id_products' in input:
            product_dict = utils.input_to_dict_prod_serv(input['id_products'])
            input.pop('id_products')
        if 'id_services' in input:
            service_dict = utils.input_to_dict_prod_serv(input['id_services'])
            input.pop('id_services')
        if 'detail' in input:
            detail = input['detail']
            input.pop('detail')

        data = utils.input_to_dictionary(input)

        # This is a very dangerous operation but statistics are on our side.
        while generate_code_again:
            random_code = utils.random_code_request()
            requests_with_that_code = db_session.query(
                ModelRequest).filter_by(unique_id=random_code).first()
            if requests_with_that_code is None:
                data['unique_id'] = random_code
                generate_code_again = False

        try:
            client = db_session.query(ModelClient).get(data['id_client'])
            client.id
        except Exception as e:
            raise Exception(f' Client does not exist. Error: {e.__cause__}')

        # Load extra data for request
        # Createa an epoch datetime of today

        data['id_account_creator'] = account.id
        data['created'] = str(int(time.time()))
        data['edited'] = str(int(time.time()))

        # Is the input ok?
        utils.InputCheck().request_input_ok(data)
        utils.InputCheck().request_list_prod_serv(product_dict, service_dict)

        # Add detail of products for Request
        if product_dict is not None:
            for prod in product_dict:
                prod_detail = ModelProductRequest()
                try:
                    prod_db = db_session.query(ModelProduct).get(prod)
                    prod_db.id
                except Exception as e:
                    raise Exception(
                        f' Product does not exist. Error: {e.__cause__}')
                prod_detail.amount = product_dict[prod]
                prod_detail.product_ref = prod_db
                final_price_request += prod_db.price * prod_detail.amount
                # request.products.append(prod_detail)
                product_detail.append(prod_detail)

        # Add detail of services for Request
        if service_dict is not None:
            for serv in service_dict:
                serv_detail = ModelServiceRequest()
                try:
                    serv_db = db_session.query(ModelService).get(serv)
                    serv_db.id
                except Exception as e:
                    raise Exception(
                        f' Service does not exist. Error: {e.__cause__}')
                serv_detail.amount = service_dict[serv]
                serv_detail.service_ref = serv_db
                final_price_request += serv_db.price * serv_detail.amount
                # request.services.append(serv_detail)
                service_detail.append(serv_detail)

        # Add final price of request
        data['final_price'] = float(final_price_request)

        request = ModelRequest(**data)

        for p in product_detail:
            request.products.append(p)
        for s in service_detail:
            request.services.append(s)

        # Add state of request
        state = ModelRequestState()
        state.request = request
        state.state = 'pending'
        if detail is not None:
            state.detail = detail
        db_session.add(state)
        db_session.add(request)
        db_session.commit()
        db_session.refresh(request)

        # subcription
        req_dict = utils.requests_to_dict([request], True)
        print("")
        req_dict[0]['show_notification'] = True
        hola = 1

        # TODO: Basicly imitate the shit we are emmiting here! 
        PayloadRequest.received_data(req_dict)

        return CreateRequest(request=request)


class RequestDeleteAttribute:
    id = graphene.ID(description="ID of the Request", required=True)


class DeleteRequestInput(graphene.InputObjectType, RequestDeleteAttribute):
    """Arguments to delete a Product."""
    pass


class DeleteRequest(graphene.Mutation):
    """ Delete Product"""
    is_deleted = graphene.Boolean(
        description="if the Product is deleted return true")

    class Arguments:
        input = DeleteRequestInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        is_deleted: bool = False

        # Who is trying to delete the Request?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['request.delete']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        request = db_session.query(
            ModelRequest).filter_by(id=data['id']).first()
        if not request:
            db_session.rollback()
            db_session.close()
            raise Exception('Request Not found')
        try:
            db_session.delete(request)
            db_session.commit()
        except Exception as e:
            raise Exception(
                f"Error to delete request {e.__cause__}")
        is_deleted = True
        db_session.close()
        return DeleteRequest(is_deleted=is_deleted)


class ReportRequestByDateAttribute:
    start_date = graphene.String(description="Start date of the report", required=True)
    end_date = graphene.String(description="End date of the report", required=True)

class ReportRequestByDateInput(graphene.InputObjectType, ReportRequestByDateAttribute):
    """Arguments to get the requests."""
    pass

class ReportRequestByDate(graphene.Mutation):
    """ Get the requests by date"""
    requests = graphene.List(RequestLog, description="List of requests")

    class Arguments:
        input = ReportRequestByDateInput(required=True)
    
    @mutation_header_jwt_required
    def mutate(self, info, input):
        # Who is trying to get the requests?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['request.read']
        utils.evaluate_permissions(perms, account)
    
        data = utils.input_to_dictionary(input)
        start_date = data['start_date']
        end_date = data['end_date']
       
        requests = db_session.query(ModelRequestLog).filter(ModelRequestLog.created.between(start_date, end_date)).all()
        return ReportRequestByDate(requests=requests)




