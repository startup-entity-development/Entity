from itertools import product
from math import prod
from graphene_sqlalchemy import SQLAlchemyConnectionField
import graphene
from schemas.schema_backup import ConfirmationBackUp, CreateBackUp
from schemas.schema_brand import CreateBrand, DeleteBrand, UpdateBrand
from schemas.schema_category import CreateCategory, DeleteCategory, UpdateCategory

from schemas.schema_product import CreateProduct
from schemas.schema_request import CreateRequest
from .schema_account import *
from .schema_role import *
from .schema_product import *
from .schema_service import *
from .schema_client import *
from .schema_request import *
from .schema_brand import *
from .schema_category import *
from .schema_news import *


class Query(graphene.ObjectType):
    """Query objects for GraphQL API."""

    node = graphene.relay.Node.Field()

    account = graphene.relay.Node.Field(Account)
    accountList = SQLAlchemyConnectionField(AccountExclude)

    role = graphene.relay.Node.Field(Role)
    roleList = SQLAlchemyConnectionField(Role)

    product = graphene.relay.Node.Field(Product)
    productList = SQLAlchemyConnectionField(Product)
 
    service = graphene.relay.Node.Field(Service)
    serviceList = SQLAlchemyConnectionField(Service)

    brand = graphene.relay.Node.Field(Brand)
    brandList = SQLAlchemyConnectionField(Brand)

    category = graphene.relay.Node.Field(Category)
    categoryList = SQLAlchemyConnectionField(Category)

    client = graphene.relay.Node.Field(Client)
    clientList = SQLAlchemyConnectionField(Client)

    news = graphene.relay.Node.Field(News)
    newsList = SQLAlchemyConnectionField(News)

    viewsNews = graphene.relay.Node.Field(ViewsNews)
    viewsNewsList = SQLAlchemyConnectionField(ViewsNews)

    request = graphene.relay.Node.Field(Request)
    requestList = SQLAlchemyConnectionField(Request)
    requestLogList = SQLAlchemyConnectionField(RequestLog)

class Mutation(graphene.ObjectType):
    createAccount = CreateAccount.Field()
    createaAdminAccount = CreateAccountAdmin.Field()
    updateAccount = UpdateAccount.Field()
    deleteAccount = DeleteAccount.Field()
    loginAccount = LoginAccount.Field()
    checkRequestAccount = CheckRequestsAccount.Field()

    createRole = CreateRole.Field()
    updateRole = UpdateRole.Field()
    deleteRole = DeleteRole.Field()

    createCategory = CreateCategory.Field()
    deleteCategory = DeleteCategory.Field()
    updateCategory = UpdateCategory.Field()

    createBrand = CreateBrand.Field()
    deleteBrand = DeleteBrand.Field()
    updateBrand = UpdateBrand.Field()

    createProduct = CreateProduct.Field()
    updateProduct = UpdateProduct.Field()
    deleteProduct = DeleteProduct.Field()
    checkRequestsProduct = CheckRequestsProduct.Field()
    checkSimilarProduct = CheckSimilarProduct.Field()

    createService = CreateService.Field()
    updateService = UpdateService.Field()
    deleteService = DeleteService.Field()
    checkRequestsService = CheckRequestsService.Field()

    createClient = CreateClient.Field()
    updateClient = UpdateClient.Field()
    deleteClient = DeleteClient.Field()
    checkRequestsClient = CheckRequestsClient.Field()

    createRequest = CreateRequest.Field()
    deleteRequest = DeleteRequest.Field()
    UpdateRequest = UpdateRequest.Field()
    UpdateFullRequest = UpdateFullRequest.Field()
    listRequestsByDate = ReportRequestByDate.Field()
    
    createBackUp = CreateBackUp.Field()
    confirmationBackUp = ConfirmationBackUp.Field()

    createNews = CreateNews.Field()
    updateNews = UpdateNews.Field()
    deleteNews = DeleteNews.Field()
    viewsOfNews = ViewsOfNews.Field()


schema = graphene.Schema(query=Query, mutation=Mutation, subscription=SubscriptionRequest)