from datetime import datetime
import hashlib
import json
from graphene_sqlalchemy import SQLAlchemyObjectType
from models.model_brand import ModelBrand
from models.model_role import ModelRole
from models.model_account import ModelAccount
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (
	mutation_jwt_refresh_token_required, get_jwt_identity,
	create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims
)

class BrandAttribute:
	name = graphene.String(description="Name of the Brand", required=True)


class Brand(SQLAlchemyObjectType):
	"""Brand node."""

	class Meta:
		model = ModelBrand
		interfaces = (graphene.relay.Node,)

class CreateBrandInput(graphene.InputObjectType, BrandAttribute):
	"""Arguments to create a Brand."""
	pass

# The creation, in a greater app, should be controlled. In this case we dont need it.
class CreateBrand(graphene.Mutation):

	"""Mutation to create a Brand."""

	# Fields that the mutation can return
	brand = graphene.Field(
		lambda: Brand, description="Brand node created by this mutation.")

	# Fields that the mutation takes as input
	class Arguments:
		input = CreateBrandInput(required=True)
	
	@mutation_header_jwt_required
	def mutate(self, info, input):

		 # Who is trying to create the Account?
		id_account_token = int(get_jwt_claims()['id'])
		account = db_session.query(ModelAccount).get(id_account_token)
		perms = ['brand.add']
		utils.evaluate_permissions(perms, account)

		data = utils.input_to_dictionary(input)
		# if not utils.InputCheck().name_ok(data['name']):
		# 	raise Exception(
		# 		f"Invalid name. Should only contain letters and be greater than 3 characters")
		data['name'] = data['name']
		brand = ModelBrand(**data)
		db_session.add(brand)
		try:
			db_session.flush()
			db_session.refresh(brand)
			db_session.commit()
		except Exception as e:
			db_session.rollback()
			db_session.close()
			raise Exception(
				f"Error creating Brand for {data['name']} error: {e.__cause__}")
		return CreateBrand(brand=brand)



class BrandDeleteAttribute:
    id = graphene.ID(description="ID of the Brand", required=True)

class DeleteBrandInput(graphene.InputObjectType, BrandDeleteAttribute):
    """Arguments to delete a Brand."""
    pass

class DeleteBrand(graphene.Mutation):
    """ Delete Brand"""
    is_deleted = graphene.Boolean(
        description="if the Brand is deleted return true")

    class Arguments:
        input = DeleteBrandInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        is_deleted: bool = False

        # Who is trying to delete the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['brand.delete']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        brand = db_session.query(ModelBrand).filter_by(id=data['id']).first()
        if not brand:
            db_session.rollback()
            db_session.close()
            raise Exception('|$BR1001 - Brand Not found')
        try:
            db_session.delete(brand)
            db_session.commit()
        except Exception as e:
            raise Exception(
                f"Error to delete Brand {e.__cause__}")
        is_deleted = True
        db_session.close()
        return DeleteBrand(is_deleted=is_deleted)



class UpdateBrandInput(graphene.InputObjectType):
    """Arguments to update a Brand ."""
    id =  graphene.ID(description="Id of the Brand.", required=True)
    name = graphene.String(description="Name of the Brand")

class UpdateBrand(graphene.Mutation):
    """Update a Brand."""
    brand = graphene.Field(
        lambda: Brand, description="Brand updated by this mutation.")

    class Arguments:
        input = UpdateBrandInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to update the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['brand.update']
        utils.evaluate_permissions(perms, account)
        data = utils.input_to_dictionary(input)
        
        brand = db_session.query(ModelBrand).get(data['id'])
        if not brand:
            db_session.rollback()
            db_session.close()
            raise Exception('|$BR1002 - Brand Not found')
        try:
            brand = db_session.query(ModelBrand).filter_by(id=data['id'])
            brand.update(input)
        except Exception as e:
            raise Exception(f'Error in update: {e.__cause__}')
        db_session.commit()

        brand = db_session.query(ModelBrand).filter_by(id=data['id']).first()
        db_session.refresh(brand)
        return UpdateBrand(brand=brand)