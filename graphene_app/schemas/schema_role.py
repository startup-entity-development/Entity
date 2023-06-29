from datetime import datetime
import hashlib
import json
from graphene_sqlalchemy import SQLAlchemyObjectType
from models.model_role import ModelRole
from models.model_account import ModelAccount
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (
	mutation_jwt_refresh_token_required, get_jwt_identity,
	create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims
)

class UpdateRoleInput(graphene.InputObjectType):
	"""Arguments to update a Role ."""
	id =  graphene.ID(required=True, description="Id of the Role.")
	name = graphene.String(description="Name of the Role.")


class UpdateRole(graphene.Mutation):
	"""Update a Role."""
	role = graphene.Field(
		lambda: Role, description="Role updated by this mutation.")

	class Arguments:
		input = UpdateRoleInput(required=True)

	def mutate(self, info, input):
		data = utils.input_to_dictionary(input)

		if not utils.InputCheck().name_ok(data['name']):
			raise Exception(
				f"Invalid name. Should only contain letters and be greater than 3 characters")		
		
		role = db_session.query(ModelRole).filter_by(id=data['id'])
		if role[0].name == 'admin':
			db_session.rollback()
			db_session.close()
			raise Exception( 'Admin role can not be updated.')
		
		try:
			role.update(input)
		except Exception as e:
			raise Exception(f'Error in update: {e.__cause__}')
		db_session.commit()
		role = db_session.query(ModelRole).filter_by(id=data['id']).first()
		db_session.refresh(role)
		return UpdateRole(role=role)


class RoleAttribute:
	name = graphene.String(description="Name of the Role", required=True)


class Role(SQLAlchemyObjectType):
	"""Role node."""

	class Meta:
		model = ModelRole
		interfaces = (graphene.relay.Node,)


class CreateRoleInput(graphene.InputObjectType, RoleAttribute):
	"""Arguments to create a account."""
	pass

class CreateRole(graphene.Mutation):

	"""Mutation to create a Role."""

	# Fields that the mutation can return
	role = graphene.Field(
		lambda: Role, description="Role node created by this mutation.")

	# Fields that the mutation takes as input
	class Arguments:
		input = CreateRoleInput(required=True)
	
	def mutate(self, info, input):
		data = utils.input_to_dictionary(input)
		if not utils.InputCheck().name_ok(data['name']):
			raise Exception(
				f"Invalid name. Should only contain letters and be greater than 3 characters")
		data['name'] = data['name'].lower()
		role = ModelRole(**data)
		db_session.add(role)
		try:
			db_session.flush()
			db_session.refresh(role)
			db_session.commit()
		except Exception as e:
			db_session.rollback()
			db_session.close()
			raise Exception(
				f"Error creating role for {data['name']} error: {e.__cause__}")
		return CreateRole(role=role)


class DeleteRoleInput(graphene.InputObjectType, RoleAttribute):
	"""Arguments to create a account."""
	pass

class DeleteRole(graphene.Mutation):
	""" Delete Role"""
	is_deleted = graphene.Boolean(
		description="if the role is deleted return true")

	class Arguments:
		input = DeleteRoleInput(required=True)

	def mutate(self, info, input):
		is_deleted: bool = False
		data = utils.input_to_dictionary(input)
		role = db_session.query(ModelRole).filter_by(name=data['name']).first()
		if role.name == 'admin':
			db_session.rollback()
			db_session.close()
			raise Exception( 'Admin role can not be deleted.')
		try:
			db_session.delete(role)
			db_session.commit()
		except Exception as e:
			raise Exception(
				f"Error to delete role {e.__cause__}")
		
		is_deleted = True
		db_session.close()
		return DeleteRole(is_deleted=is_deleted)

class RoleExclude(SQLAlchemyObjectType):
    """RoleExclude node."""

    class Meta:
        model = ModelRole
        #exclude_fields = ('password', 'id')
        interfaces = (graphene.relay.Node,)