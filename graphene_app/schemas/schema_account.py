from datetime import datetime
import hashlib
import json
from graphene_sqlalchemy import SQLAlchemyObjectType
from models.model_account import ModelAccount
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (
    mutation_jwt_refresh_token_required, get_jwt_identity,
    create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims
)
from models.model_request import ModelRequest
from models.model_role import ModelRole
from models.model_state_request import ModelRequestState


class UpdateAccountInput(graphene.InputObjectType):
    """Arguments to update an account."""
    id = graphene.ID(description="Id of the account being edited.", required=True)
    dni = graphene.String(description="Name of the account max len 30.")
    name = graphene.String(description="Name of the person with the account.")
    location = graphene.String(description="Location of the account. Nor required")
    username = graphene.String(description="Username of the account. Nor required but unique")
    phone_number = graphene.String(description="Phone Number of the account. Nor required but unique")
    email = graphene.String(description="Email of the account. Nor required but unique")
    role_id = graphene.String(description="Role of the account.")
    password = graphene.String(description="password of the account.")


class UpdateAccount(graphene.Mutation):
    """Update an account."""
    account = graphene.Field(
        lambda: Account, description="Account updated by this mutation.")

    class Arguments:
        input = UpdateAccountInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to create the Account?
        id_admin = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_admin)
        perms = ['account.update']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        utils.InputCheck().account_input_ok(data, True)

        # takes the name of the role and searchs for it's id
        if 'role_id' in data:
            if data['role_id'] == "" or data['role_id'] is None:
                raise Exception(
                    f"Role not provided (updateAccount)")
            db_role = db_session.query(ModelRole).filter_by(name=data['role_id']).first()
            if db_role is None:
                raise Exception(f"Role name not found (updateAccount)")
            data['role_id'] = db_role.id
        
        # update password only ifa  new one was provided
        if 'password' in data:
            if data['password'] == None or data['password'] == '': 
                del data['password']
            else :
                password = (hashlib.md5(data['password'].encode('utf-8')).hexdigest())
                data['password'] = password
        
        account = db_session.query(ModelAccount).get(data['id'])
        if not account:
            db_session.rollback()
            db_session.close()
            raise Exception(
                '|$AC1007 - Account not found')
        try:  
            account = db_session.query(ModelAccount).filter_by(id=data['id'])
            account.update(input)
        except Exception as e:
            raise Exception(f'|$AC1009 - Error in update: {e.__cause__}')
        db_session.commit()
        account = db_session.query(ModelAccount).get(data['id'])
        db_session.refresh(account)
        return UpdateAccount(account=account)


class AccountAttribute:
    name = graphene.String(description="Name of the account", required=True)
    dni = graphene.String(description="National identification document of the person.", required=True)
    role_id = graphene.String(description="The role name of the account", required=True)
    password = graphene.String(description="Password of the account.", required=True)
    location = graphene.String(description="Location of the account. Nor required")
    username = graphene.String(description="Username of the account. Nor required but unique")
    phone_number = graphene.String(description="Phone Number of the account. Nor required but unique")
    email = graphene.String(description="Email of the account. Nor required but unique")
    



class Account(SQLAlchemyObjectType):
    """Account node."""

    class Meta:
        model = ModelAccount
        interfaces = (graphene.relay.Node,)


class CreateAccountInput(graphene.InputObjectType, AccountAttribute):
    """Arguments to create a account."""
    pass


class CreateAccount(graphene.Mutation):

    """Mutation to create a account."""

    # Fields that the mutation can return
    account = graphene.Field(
        lambda: Account, description="Account node created by this mutation.")
    access_token = graphene.String()
    refresh_token = graphene.String()

    # Fields that the mutation takes as input
    class Arguments:
        input = CreateAccountInput(required=True)
    
    @mutation_header_jwt_required
    def mutate(self, info, input):
        
        # Who is trying to create the Account?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['account.add']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        utils.InputCheck().account_input_ok(data, False)
        
        # takes the name of the role and searchs for it's id
        if data['role_id'] == "" or data['role_id'] is None:
            raise Exception(
                f"Role not provided (createAccount)")
        db_role = db_session.query(ModelRole).filter_by(name=data['role_id']).first()
        if db_role is None:
            raise Exception(f"Role name not found (createAccount)")
        
        data['role_id'] = db_role.id
        password = (hashlib.md5(data['password'].encode('utf-8')).hexdigest())
        data['password'] = password
        account = ModelAccount(**data)
        db_session.add(account)
        try:
            db_session.flush()
            db_session.refresh(account)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            db_session.close()
            exception_msg: str = evaluate_exception(e.__cause__.msg)
            raise Exception(
                f"{exception_msg} | {data['dni']}")
        return CreateAccount(account=account,
                             access_token=create_access_token(
                                 account.id, user_claims={'id': account.id}),
                             refresh_token=create_refresh_token(account.id))

def evaluate_exception(exception_message:str):
    if (exception_message.find('username') != -1):
        return '|$AC1015 - Error creating account. Username duplicated'
    if (exception_message.find('dni') != -1):
        return '|$AC1016 - Error creating account. DNI duplicated'
    if (exception_message.find('phone_number') != -1):
        return '|$AC1017 - Error creating account. Phone Number duplicated'
    return exception_message

class AdminAccountAttribute:
    name = graphene.String(description="Name of the account", required=True)
    dni = graphene.String(
        description="National identification document of the person.", required=True)
    password = graphene.String(
        description="Password of the account.", required=True)

class CreateAdminAccountInput(graphene.InputObjectType, AdminAccountAttribute):
    """Arguments to create a account."""
    pass


class CreateAccountAdmin(graphene.Mutation):
    """ Mutation to create an account with the admin Role.
        Should be the first thing to do when the system "starts".  
    """

    # Fields that the mutation can return
    account = graphene.Field(
        lambda: Account, description="Account node created by this mutation.")
    access_token = graphene.String()
    refresh_token = graphene.String()

    # Fields that the mutation takes as input
    class Arguments:
        input = CreateAdminAccountInput(required=True)

    def mutate(self, info, input):
        data = utils.input_to_dictionary(input)
        utils.InputCheck().account_input_ok(data, False)
        password = (hashlib.md5(data['password'].encode('utf-8')).hexdigest())
        data['password'] = password
        
        # Asigns the admin role  
        role_admin = db_session.query(ModelRole).filter_by(name='admin').first()
        data['role_id'] = role_admin.id
        
        
        account = ModelAccount(**data)
        db_session.add(account)
        try:
            db_session.flush()
            db_session.refresh(account)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            db_session.close()
            raise Exception(
                f"Error creating account for {data['dni']} error: {e.__cause__}")
        return CreateAccount(account=account,
                             access_token=create_access_token(
                                 account.id, user_claims={'id': account.id}),
                             refresh_token=create_refresh_token(account.id))



class DeleteAccountAttribute:
    id = graphene.ID(description="Id of the account being deleted.", required=True)

class DeleteAccountInput(graphene.InputObjectType, DeleteAccountAttribute):
    """Arguments to delete an account."""
    pass

class DeleteAccount(graphene.Mutation):
    """ Delete Account"""
    is_deleted = graphene.Boolean(
        description="if the account is deleted return true")

    class Arguments:
        input = DeleteAccountInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        is_deleted: bool = False

        # Who is trying to create the Account?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['account.delete']
        utils.evaluate_permissions(perms, account)
        
        data = utils.input_to_dictionary(input)
        account = db_session.query(ModelAccount).filter_by(id=data['id']).first()
        if account is None:
            raise Exception(
                f"|$AC1006 - Account not found")
        try:
            db_session.delete(account)
            db_session.commit()
        except Exception as e:
            raise Exception(
                f"|$AC1005 - Error to delete account {e.__cause__}")
        is_deleted = True
        db_session.close()
        return DeleteAccount(is_deleted=is_deleted)


class AccountExclude(SQLAlchemyObjectType):
    """AccountExclude node."""

    class Meta:
        model = ModelAccount
        exclude_fields = ('password', 'id')
        interfaces = (graphene.relay.Node,)


class LoginAccountAttribute:
    dni = graphene.String(description="National identification document of the person.")
    username = graphene.String(description="Username of the person.")
    password = graphene.String(
        description="Password of the account.", required=True)
    
class LoginAccountInput(graphene.InputObjectType, LoginAccountAttribute):
    """Arguments to login an account."""
    pass

class LoginAccount(graphene.Mutation):
    """ Login Account"""
    account = graphene.Field(lambda: AccountExclude, description="Account node created by this mutation.")
    access_token = graphene.String()
    refresh_token = graphene.String()

    class Arguments:
        input = LoginAccountInput(required=True)

    def mutate(self, info, input):
        data = utils.input_to_dictionary(input)

        if 'dni' not in data and 'username' not in data:
             raise Exception(
                f"|$AC1020 Cant login an user without DNI or USERNAME. One must be provided")
        password = (hashlib.md5(data['password'].encode('utf-8')).hexdigest())
        data['password'] = password
        account = db_session.query(ModelAccount).filter_by(**data).first()
        if account is None:
            raise Exception(
                f"|$AC1008 - Account not found")
        return LoginAccount(account=account,
                            access_token=create_access_token(
                                account.id, user_claims={'id': account.id}),
                            refresh_token=create_refresh_token(account.id))


class CheckRequestsAccountAttribute:
    id = graphene.ID(description="Id of the account being check.", required=True)

class CheckRequestsAccountInput(graphene.InputObjectType, CheckRequestsAccountAttribute):
    """Arguments to check an account."""
    pass

class CheckRequestsAccount(graphene.Mutation):
    """ Check if a given Account have any request associated.
        Used in FrontEnd for some validation.
    """
    have_requests = graphene.Boolean(
        description="if the account have associated requests return true")

    class Arguments:
        input = CheckRequestsAccountInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        have_requests: bool = False

        # Who is trying to check for the Account?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['account.read']
        utils.evaluate_permissions(perms, account)
        
        data = utils.input_to_dictionary(input)
        
        # First check if the creator is associated to some request in pending state
        request = db_session.query(ModelRequest).filter_by(id_account_creator=int(data['id'])).first()
        if request is None:
            have_requests: bool = False
        else:
            state_request = db_session.query(ModelRequestState).filter_by(id_request=(int(request.id))).first()
            if state_request is None:
                raise Exception("ERROR: Some error related to the state of the request have happen.")
            else:
                if state_request.state.name == 'pending':
                    have_requests: bool = True
                else:
                    have_requests: bool = False
        if have_requests:
            return CheckRequestsAccount(have_requests=have_requests)
        
        # Second check for some worker
        request = db_session.query(ModelRequest).filter_by(id_account_receiver=data['id']).first()
        if request is None:
            have_requests: bool = False
        else: 
            state_request = db_session.query(ModelRequestState).filter_by(id_request=(int(request.id))).first()
            if state_request is None:
                raise Exception("ERROR: Some error related to the state of the request have happen.")
            else:
                if state_request.state.name == 'pending':
                    have_requests: bool = True
                else:
                    have_requests: bool = False
        db_session.close()
        return CheckRequestsAccount(have_requests=have_requests)