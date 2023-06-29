from datetime import datetime
import re
import hashlib
import json
from graphene_sqlalchemy import SQLAlchemyObjectType
from models.model_client import ModelClient
from models.model_request import ModelRequest
from models.model_role import ModelRole
from models.model_account import ModelAccount
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (
    mutation_jwt_refresh_token_required, get_jwt_identity,
    create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims
)

class UpdateClientInput(graphene.InputObjectType):
    """Arguments to update a Client ."""
    id =  graphene.ID(required=True, description="Id of the Client.")
    name = graphene.String(description="Name of the Client")
    #direction = graphene.String(description="Direction of the client")
    phone_number = graphene.String(description="Phone Number of the Client")



class UpdateClient(graphene.Mutation):
    """Update a Client."""
    client = graphene.Field(
        lambda: Client, description="Client updated by this mutation.")

    class Arguments:
        input = UpdateClientInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to create the Client?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['client.update']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        utils.InputCheck().client_input_ok(data)

        client = db_session.query(ModelClient).get(data['id'])
        if not client:
            db_session.rollback()
            db_session.close()
            raise Exception('|$CL1003 - Client Not found')
        
        try:
            client = db_session.query(ModelClient).filter_by(id=data['id'])
            client.update(input)
        except Exception as e:
            raise Exception(f'Error in update: {e.__cause__}')
        db_session.commit()
        client = db_session.query(ModelClient).get(data['id'])
        db_session.refresh(client)
        return UpdateClient(client=client)


class ClientAttribute:
    name = graphene.String(description="Name of the Client") # Not required I GUESS. I may be wrong...
    #direction = graphene.String(description="Direction of the client")
    phone_number = graphene.String(description="Phone Number of the Client", required=True)


class Client(SQLAlchemyObjectType):
    """Client node."""

    class Meta:
        model = ModelClient
        interfaces = (graphene.relay.Node,)


class CreateClientInput(graphene.InputObjectType, ClientAttribute):
    """Arguments to create a Client."""
    pass

class CreateClient(graphene.Mutation):

    """Mutation to create a Client."""

    # Fields that the mutation can return
    client = graphene.Field(
        lambda: Client, description="Client node created by this mutation.")

    # Fields that the mutation takes as input
    class Arguments:
        input = CreateClientInput(required=True)
    
    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to create the Client?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['client.add']
        utils.evaluate_permissions(perms, account)
        
        data = utils.input_to_dictionary(input)
        utils.InputCheck().client_input_ok(data)

        client = ModelClient(**data)
        db_session.add(client)
        try:
            db_session.flush()
            db_session.refresh(client)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            db_session.close()
            raise Exception(
                f"Error creating Client for {data['name']} error: {e.__cause__}")
        return CreateClient(client=client)

 
class ClientDeleteAttribute:
    id = graphene.ID(description="ID of the Client", required=True)

class DeleteClientInput(graphene.InputObjectType, ClientDeleteAttribute):
    """Arguments to delete a Client."""
    pass

class DeleteClient(graphene.Mutation):
    """ Delete Client"""
    is_deleted = graphene.Boolean(
        description="if the Client is deleted return true")

    class Arguments:
        input = DeleteClientInput(required=True)
    
    @mutation_header_jwt_required
    def mutate(self, info, input):
        is_deleted: bool = False
        # Who is trying to create the Client?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['client.delete']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        utils.InputCheck().client_input_ok(data)

        client = db_session.query(ModelClient).filter_by(id=data['id']).first()
        if not client:
            db_session.rollback()
            db_session.close()
            raise Exception('|$CL1004 - Client Not found')
        try:
            db_session.delete(client)
            db_session.commit()
        except Exception as e:
            raise Exception(
                f"Error to delete role {e.__cause__}")
        is_deleted = True
        db_session.close()
        return DeleteClient(is_deleted=is_deleted)


class CheckRequestsClientAttribute:
    id = graphene.ID(description="Id of the client being check.", required=True)

class CheckRequestsClientInput(graphene.InputObjectType, CheckRequestsClientAttribute):
    """Arguments to check a client."""
    pass

class CheckRequestsClient(graphene.Mutation):
    """ Check if a given Client have any request associated.
        Used in FrontEnd for some validation.
    """
    have_requests = graphene.Boolean(
        description="if the client have associated requests return true")

    class Arguments:
        input = CheckRequestsClientInput(required=True)

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
        request = db_session.query(ModelRequest).filter_by(id_client=int(data['id'])).first()
        if request is None:
            have_requests: bool = False
        else:
            have_requests: bool = True
            
        db_session.close()
        return CheckRequestsClient(have_requests=have_requests)