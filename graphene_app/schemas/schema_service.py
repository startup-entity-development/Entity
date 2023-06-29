from datetime import datetime
import hashlib
import json
from graphene_sqlalchemy import SQLAlchemyObjectType
from models.model_service import ModelService
from models.model_account import ModelAccount
from models.model_role import ModelRole
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (
    mutation_jwt_refresh_token_required, get_jwt_identity,
    create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims, util
)
from models.model_service_request import ModelServiceRequest

class UpdateServiceInput(graphene.InputObjectType):
    """Arguments to update a Service ."""
    id =  graphene.ID(description="Id of the Service.", required=True)
    name = graphene.String(description="Name of the Service")
    detail = graphene.String(description="detail of the Service")
    price = graphene.Float(description="Price of the Service")


class UpdateService(graphene.Mutation):
    """Update a Service."""
    service = graphene.Field(
        lambda: Service, description="Service updated by this mutation.")

    class Arguments:
        input = UpdateServiceInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        # Who is trying to update the Service?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['service.update']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        utils.InputCheck().product_service_input_ok(data)

        service = db_session.query(ModelService).get(data['id'])
        if service is None:
            db_session.rollback()
            db_session.close()
            raise Exception('|$SE1002 - Service Not found')
        try:
            service = db_session.query(ModelService).filter_by(id=data['id'])
            service.update(data)
        except Exception as e:
            raise Exception(f'Error in update: {e.__cause__}')
        db_session.commit()

        if 'price' in data:
            utils.update_final_price_requests(data['id'], 'service')

        service = db_session.query(ModelService).filter_by(id=data['id']).first()
        db_session.refresh(service)
        return UpdateService(service=service)


class ServiceAttribute:
    name = graphene.String	(description="Name of the Service", required=True)
    detail = graphene.String(description="detail of the Service")
    price = graphene.Float	(description="Price of the Service", required=True)


class Service(SQLAlchemyObjectType):
    """Service node."""

    class Meta:
        model = ModelService
        interfaces = (graphene.relay.Node,)


class CreateServiceInput(graphene.InputObjectType, ServiceAttribute):
    """Arguments to create a Service."""
    pass


class CreateService(graphene.Mutation):

    """Mutation to create a Service."""

    # Fields that the mutation can return
    service = graphene.Field(
        lambda: Service, description="Service node created by this mutation.")

    # Fields that the mutation takes as input
    class Arguments:
        input = CreateServiceInput(required=True)
    
    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to create the Service?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['service.add']
        utils.evaluate_permissions(perms, account)
        
        data = utils.input_to_dictionary(input)
        utils.InputCheck().product_service_input_ok(data)
        
        data['name'] = data['name'].lower()
        service = ModelService(**data)
        db_session.add(service)
        try:
            db_session.flush()
            db_session.refresh(service)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            db_session.close()
            raise Exception(
                f"Error creating service for {data['name']} error: {e.__cause__}")
        return CreateService(service=service)

 
class ServiceDeleteAttribute:
    id = graphene.ID(description="ID of the Service", required=True)

class DeleteServiceInput(graphene.InputObjectType, ServiceDeleteAttribute):
    """Arguments to delete a Service."""
    pass

class DeleteService(graphene.Mutation):
    """ Delete Service"""
    is_deleted = graphene.Boolean(
        description="if the Service is deleted return true")

    class Arguments:
        input = DeleteServiceInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        is_deleted: bool = False
        
        # Who is trying to delete the Service?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['service.delete']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        service = db_session.query(ModelService).filter_by(id=data['id']).first()
        if not service:
            db_session.rollback()
            db_session.close()
            raise Exception('|$SE1001 - Service Not found')
        try:
            db_session.delete(service)
            db_session.commit()
        except Exception as e:
            raise Exception(
                f" Error to delete Service {e.__cause__}")
        is_deleted = True
        db_session.close()
        return DeleteService(is_deleted=is_deleted)



class CheckRequestsServiceAttribute:
    id = graphene.ID(description="Id of the service being check.", required=True)

class CheckRequestsServiceInput(graphene.InputObjectType, CheckRequestsServiceAttribute):
    """Arguments to check a product."""
    pass

class CheckRequestsService(graphene.Mutation):
    """ Check if a given Service have any request associated.
        Used in FrontEnd for some validation.
    """
    have_requests = graphene.Boolean(
        description="if the service have associated requests return true")

    class Arguments:
        input = CheckRequestsServiceInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        have_requests: bool = False

        # Who is trying to check for the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['account.read']
        utils.evaluate_permissions(perms, account)
        
        data = utils.input_to_dictionary(input)
        
        # First check if the creator is associated to some request in pending state
        request = db_session.query(ModelServiceRequest).filter_by(id_service=int(data['id'])).first()
        if request is None:
            have_requests: bool = False
        else:
            have_requests: bool = True
            
        db_session.close()
        return CheckRequestsService(have_requests=have_requests)