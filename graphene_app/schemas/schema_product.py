from datetime import datetime
import hashlib
import json
import time
from graphene_sqlalchemy import SQLAlchemyObjectType
from models.model_brand import ModelBrand
from models.model_category import ModelCategory
from models.model_product import ModelProduct
from models.model_account import ModelAccount
from models.model_product_request import ModelProductRequest
from models.model_request import ModelRequest
from models.model_role import ModelRole
import graphene
from general_functions import utils
from models.base import db_session
from graphql_auth import (
    mutation_jwt_refresh_token_required, get_jwt_identity,
    create_access_token, create_refresh_token, mutation_header_jwt_required, get_jwt_claims
)
from thefuzz import fuzz


class UpdateProductInput(graphene.InputObjectType):
    """Arguments to update a Product ."""
    id =  graphene.ID(description="Id of the Product.", required=True)
    name = graphene.String(description="Name of the Product")
    detail = graphene.String(description="detail of the product")
    price = graphene.Float(description="Price of the product")
    length = graphene.Float(description="length of the product")
    width = graphene.Float(description="width of the product")
    denomination = graphene.String(description="denomination of the product")
    price2 = graphene.Float(description="another price for the product")
    is_in_stock = graphene.Boolean(description="an indicator for the stock of the product. All ")
    category_id = graphene.String(description="cateogory of the product")
    brand_id = graphene.String(description="brand of the product")


class UpdateProduct(graphene.Mutation):
    """Update a Product."""
    product = graphene.Field(
        lambda: Product, description="Product updated by this mutation.")

    class Arguments:
        input = UpdateProductInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):

        # Who is trying to update the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['product.update']
        utils.evaluate_permissions(perms, account)
        data = utils.input_to_dictionary(input)
        
        # Is the input ok?
        utils.InputCheck().product_service_input_ok(data)

        product = db_session.query(ModelProduct).get(data['id'])
        if not product:
            db_session.rollback()
            db_session.close()
            raise Exception('|$PR1002 - Product Not found')
        try:
            product = db_session.query(ModelProduct).filter_by(id=data['id'])
            product.update(input)
        except Exception as e:
            raise Exception(f'Error in update: {e.__cause__}')
        db_session.commit()

        # Updates final price in requests that are in pending state
        if 'price' in data:
            utils.update_final_price_requests(data['id'], 'product')

        product = db_session.query(ModelProduct).filter_by(id=data['id']).first()
        db_session.refresh(product)
        return UpdateProduct(product=product)

class ProductAttribute:
    name = graphene.String(description="Name of the Product", required=True)
    detail = graphene.String(description="detail of the product")
    price = graphene.Float(description="Price of the product", required=True)
    length = graphene.Float(description="length of the product")
    width = graphene.Float(description="width of the product")
    denomination = graphene.String(description="denomination of the product")
    price2 = graphene.Float(description="another price for the product")
    is_in_stock = graphene.Boolean(description="an indicator for the stock of the product. All ")
    category_id = graphene.String(description="cateogory of the product")
    brand_id = graphene.String(description="brand of the product")


class Product(SQLAlchemyObjectType):
    """Product node."""

    class Meta:
        model = ModelProduct
        interfaces = (graphene.relay.Node,)


class CreateProductInput(graphene.InputObjectType, ProductAttribute):
    """Arguments to create a product."""
    pass


class CreateProduct(graphene.Mutation):

    """Mutation to create a Product."""

    # Fields that the mutation can return
    product = graphene.Field(
        lambda: Product, description="Product node created by this mutation.")

    # Fields that the mutation takes as input
    class Arguments:
        input = CreateProductInput(required=True)
    
    @mutation_header_jwt_required
    def mutate(self, info, input):
        
        # Who is trying to create the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['product.add']
        utils.evaluate_permissions(perms, account)
        data = utils.input_to_dictionary(input)
        
        # Is the input ok?
        utils.InputCheck().product_service_input_ok(data)       

        # get Categ if the product have one
        if 'category_id' in data and data['category_id'] != None:
            db_category = db_session.query(ModelCategory).filter_by(id=data['category_id']).first()
            if db_category is None:
                raise Exception(f"Category name not found (createProduct)")
            data['category_id'] = db_category.id
        
        # get Brand if the product have one
        if 'brand_id' in data and data['brand_id'] != None:
            db_brand = db_session.query(ModelBrand).filter_by(id=data['brand_id']).first()
            if db_brand is None:
                raise Exception(f"Brand name not found (createProduct)")
            data['brand_id'] = db_brand.id

        data['name'] = data['name'].lower()
        product = ModelProduct(**data)
        db_session.add(product)
        try:
            db_session.flush()
            db_session.refresh(product)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            db_session.close()
            raise Exception(
                f"Error creating product for {data['name']} error: {e.__cause__}")
        return CreateProduct(product=product)

 
class ProductDeleteAttribute:
    id = graphene.ID(description="ID of the Product", required=True)

class DeleteProductInput(graphene.InputObjectType, ProductDeleteAttribute):
    """Arguments to delete a Product."""
    pass

class DeleteProduct(graphene.Mutation):
    """ Delete Product"""
    is_deleted = graphene.Boolean(
        description="if the Product is deleted return true")

    class Arguments:
        input = DeleteProductInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        is_deleted: bool = False

        # Who is trying to delete the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['product.delete']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        product = db_session.query(ModelProduct).filter_by(id=data['id']).first()
        if not product:
            db_session.rollback()
            db_session.close()
            raise Exception('|$PR1001 - Product Not found')
        try:
            db_session.delete(product)
            db_session.commit()
        except Exception as e:
            raise Exception(
                f"Error to delete role {e.__cause__}")
        is_deleted = True
        db_session.close()
        return DeleteProduct(is_deleted=is_deleted)


class CheckRequestsProductAttribute:
    id = graphene.ID(description="Id of the product being check.", required=True)

class CheckRequestsProductInput(graphene.InputObjectType, CheckRequestsProductAttribute):
    """Arguments to check a product."""
    pass

class CheckRequestsProduct(graphene.Mutation):
    """ Check if a given Product have any request associated.
    
        - Mutation used in FrontEnd for some validation.
    """
    have_requests = graphene.Boolean(
        description="if the product have associated requests return true")

    class Arguments:
        input = CheckRequestsProductInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        have_requests: bool = False

        # Who is trying to check for the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['product.read']
        utils.evaluate_permissions(perms, account)
        
        data = utils.input_to_dictionary(input)
        
        # First check if the creator is associated to some request in pending state
        request = db_session.query(ModelProductRequest).filter_by(id_product=int(data['id'])).first()
        if request is None:
            have_requests: bool = False
        else:
            have_requests: bool = True
            
        db_session.close()
        return CheckRequestsProduct(have_requests=have_requests)


class CheckSimilarProductAttribute:
    product_name = graphene.String(description="Name of possible misspelled product")

class CheckSimilarProductInput(graphene.InputObjectType, CheckSimilarProductAttribute):
    """Arguments to check a product."""
    pass

class similarProduct(graphene.ObjectType):
    name = graphene.String()
    percentage = graphene.Int()

class CheckSimilarProduct(graphene.Mutation):
    """ Check if a given product have ohter products similar to it base on the name.
        Here we do real science and use the "Levenshtein Distance" function 8)
        
        - Mutation used in FrontEnd for some validation.
    """
    similar_products = graphene.List(similarProduct, description="List of similar products")

    class Arguments:
        input = CheckSimilarProductInput(required=True)

    @mutation_header_jwt_required
    def mutate(self, info, input):
        similar_products: list = []
        similar_prod = {}

        # Who is trying to check for the Product?
        id_account_token = int(get_jwt_claims()['id'])
        account = db_session.query(ModelAccount).get(id_account_token)
        perms = ['product.read']
        utils.evaluate_permissions(perms, account)

        data = utils.input_to_dictionary(input)
        product_name = data['product_name'].lower()

        # Get all products from db (this could probably be cached)
        products = db_session.query(ModelProduct).all()
        for product in products:
            similarity = fuzz.ratio(product.name.lower(), product_name)
            if similarity >= 85:
                similar_prod['name'] = product.name
                similar_prod['percentage'] = similarity
                similar_products.append({**similar_prod})
                #similar_products.append(productSimilitarity(product.name, similarity))
        db_session.close()

        return CheckSimilarProduct(similar_products=similar_products)






