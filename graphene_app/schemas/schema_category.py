from datetime import datetime
import hashlib
import json
from graphene_sqlalchemy import SQLAlchemyObjectType
from models.model_brand import ModelBrand
from models.model_category import ModelCategory
from models.model_role import ModelRole
from models.model_account import ModelAccount
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (
	mutation_jwt_refresh_token_required, get_jwt_identity,
	create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims
)

class CategoryAttribute:
	name = graphene.String(description="Name of the Category", required=True)


class Category(SQLAlchemyObjectType):
	"""Category node."""

	class Meta:
		model = ModelCategory
		interfaces = (graphene.relay.Node,)

class CreateCategoryInput(graphene.InputObjectType, CategoryAttribute):
	"""Arguments to create a category."""
	pass

# The creation, in a greater app, should be controlled. In this case we dont need it.
class CreateCategory(graphene.Mutation):

	"""Mutation to create a Category."""

	# Fields that the mutation can return
	category = graphene.Field(
		lambda: Category, description="Category node created by this mutation.")

	# Fields that the mutation takes as input
	class Arguments:
		input = CreateCategoryInput(required=True)
	
	@mutation_header_jwt_required
	def mutate(self, info, input):

		 # Who is trying to create the Account?
		id_account_token = int(get_jwt_claims()['id'])
		account = db_session.query(ModelAccount).get(id_account_token)
		perms = ['category.add']
		utils.evaluate_permissions(perms, account)

		data = utils.input_to_dictionary(input)
		# if not utils.InputCheck().name_ok(data['name']):
		# 	raise Exception(
		# 		f"Invalid name. Should only contain letters and be greater than 3 characters")
		data['name'] = data['name']
		category = ModelCategory(**data)
		db_session.add(category)
		try:
			db_session.flush()
			db_session.refresh(category)
			db_session.commit()
		except Exception as e:
			db_session.rollback()
			db_session.close()
			raise Exception(
				f"Error creating role for {data['name']} error: {e.__cause__}")
		return CreateCategory(category=category)



class CategoryDeleteAttribute:
    id = graphene.ID(description="ID of the Category", required=True)

class DeleteCategoryInput(graphene.InputObjectType, CategoryDeleteAttribute):
    """Arguments to delete a Category."""
    pass

class DeleteCategory(graphene.Mutation):
    """ Delete Category"""
    is_deleted = graphene.Boolean(
        description="if the Category is deleted return true")

    class Arguments:
        input = DeleteCategoryInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        is_deleted: bool = False

        # Who is trying to delete the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['category.delete']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        category = db_session.query(ModelCategory).filter_by(id=data['id']).first()
        if not category:
            db_session.rollback()
            db_session.close()
            raise Exception('|$CA1001 - Category Not found')
        try:
            db_session.delete(category)
            db_session.commit()
        except Exception as e:
            raise Exception(
                f"Error to delete Category {e.__cause__}")
        is_deleted = True
        db_session.close()
        return DeleteCategory(is_deleted=is_deleted)



class UpdateCategoryInput(graphene.InputObjectType):
    """Arguments to update a Category ."""
    id =  graphene.ID(description="Id of the Category.", required=True)
    name = graphene.String(description="Name of the Category")

class UpdateCategory(graphene.Mutation):
    """Update a Category."""
    category = graphene.Field(
        lambda: Category, description="Product updated by this mutation.")

    class Arguments:
        input = UpdateCategoryInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to update the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['category.update']
        utils.evaluate_permissions(perms, account)
        data = utils.input_to_dictionary(input)
        
        category = db_session.query(ModelCategory).get(data['id'])
        if not category:
            db_session.rollback()
            db_session.close()
            raise Exception('|$CA1002 - Category Not found')
        try:
            category = db_session.query(ModelCategory).filter_by(id=data['id'])
            category.update(input)
        except Exception as e:
            raise Exception(f'Error in update: {e.__cause__}')
        db_session.commit()

        category = db_session.query(ModelCategory).filter_by(id=data['id']).first()
        db_session.refresh(category)
        return UpdateCategory(category=category)