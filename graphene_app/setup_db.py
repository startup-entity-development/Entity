from sqlalchemy_utils import database_exists, drop_database, create_database
import logging
import sys
from models.model_account import ModelAccount
from models.model_role import ModelRole
from models.model_client import ModelClient
from models.model_service import ModelService
from models.model_product import ModelProduct
from models.model_request import ModelRequest
from models.model_permissions import ModelPermissions
from models.model_role_permissions import ModelRolePermission
from models.model_state_request import ModelRequestState
from models.model_product_request import ModelProductRequest
from models.model_service_request import ModelServiceRequest
from models.model_request_log import ModelRequestLog, ModelProductDetailLog, ModelServiceDetailLog
from models.model_brand import ModelBrand
from models.model_category import ModelCategory
from models.model_news import ModelNews
from models.model_news_views import ModelNewsViews
from models import base as b


from sqlalchemy.orm.collections import InstrumentedList 

from sqlalchemy import inspect
from sqlalchemy import insert

# Load logging configuration
log = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def create_all_models(interactive: bool = False) -> None:

    log.info(f"create all models called interactive = {interactive}. ")
    if not database_exists(b.engine.url):
        create_database(b.engine.url)
    try:
        log.warning(f"Go ahead !")
        b.Base.metadata.create_all(b.engine)
        log.warning(f"all done!!!, and look good")
    except Exception as e:
        if database_exists(b.engine.url):
            try:
                if interactive is False:
                    raise Exception(f" interactive option off.\n Trying to create database and tables,"
                                    "but somethings go wrong.. error: {e} ")
                else:
                    a = input(
                        "Fail to create all models, drop database and retry ?, Yes = y, Cancel = c ")
                    while a != 'y' or a != 'c':
                        if a == 'y':
                            log.warning(f"Go ahead !")
                            drop_database(b.engine.url)
                            create_database(b.engine.url)
                            b.Base.metadata.create_all(b.engine)
                            log.warning(f"all done!!!, and look good")
                            return
                        if a == 'c':
                            log.warning(f"Proccess canceled")
                        if a != 'y' or 'c':
                            log.warning(f"input option out the scope")

            except Exception as e:
                log.error(
                    f"file: setup_db.py method:, create_all_models fail {e}")

def create_default_permissions():
    ''' 
        Creates four default permissions for every table that
        the developer believes it's necessary. 
    '''
    for table in b.engine.table_names():
        default_permissions = ['add', 'delete', 'update', 'read']
        print("Create permissions for table: " + table + '? ---- (Y/N)')
        #answer = str(input()).upper()
        answer = 'Y'
        if answer == 'Y':
            for default in default_permissions: 
                perm = table.lower() + '.' + default
                add_perm = ModelPermissions(name=perm)
                b.db_session.add(add_perm)
                b.db_session.commit()
            print("Permissions created!")
        elif answer == 'N':
            print("Skiping...")
            pass
        else:
            print("Don't you see the options?")
            print("Skiping...")
    
    # Custom perms
    # Here should be some custom perms but there is not a truly need for it.


def create_default_roles():
    ''' 
        Creates the default roles for NordesteBaterias, meaning this function is
        extremely custom.

        There are just two roles: 
            - admin: Can do anything except for CRUD of Roles and Permissions
            - sellsman: Can only Read and Update the request_state
    '''
    roles:list = ['admin', 'sellsman', 'wholesale']
    wholesale_perms:list = ['news.read', 'newsviews.update']
    sellsman_perms:list = ['request.update']
    perms = b.db_session.query(ModelPermissions).all()

    # Adds roles
    for r in roles:
        role = ModelRole(name=r)
        b.db_session.add(role)
        b.db_session.commit()

    db_role_admin = b.db_session.query(ModelRole).filter_by(name='admin').first()
    db_role_sells = b.db_session.query(ModelRole).filter_by(name='sellsman').first()
    db_role_wholesale = b.db_session.query(ModelRole).filter_by(name='wholesale').first()
    
    #Perms for sellsman:
    for sp in sellsman_perms:
        for p in perms:
            if p.name == sp:
                role_perms = ModelRolePermission(
                    id_role=db_role_sells.id,
                    id_permission=p.id
                )
                b.db_session.add(role_perms)
                b.db_session.commit()

    # Perms for wholesale
    for wp in wholesale_perms:
        for p in perms:
            if p.name == wp:
                role_perms = ModelRolePermission(
                    id_role=db_role_wholesale.id,
                    id_permission=p.id
                )
                b.db_session.add(role_perms)
                b.db_session.commit()
    
    # Perms for admin
    for p in perms:
        if 'role' in p.name or 'permissions' in p.name:
            pass
        else:
            role_perms = ModelRolePermission(
                id_role=db_role_admin.id,
                id_permission=p.id
            )
            b.db_session.add(role_perms)
            b.db_session.commit()


def create_default_services():
    ''' 
        Creates the default services for NordesteBaterias, meaning this function is
        extremely custom.

        This function acctually is not mean to be done. The system is able to
        create services in a parametric way, but this function is only used for delivery time reasons.'''
    services:list = [
        {'name' :'servicio1', 
        'detail': 'un detalle', 
        'price': 100}, 
        
        {'name' :'servicio2',
        'detail': 'un detalle',
        'price': 200},
        ]

    for s in services:
        service = ModelService(name=s['name'], detail=s['detail'], price=s['price'])
        b.db_session.add(service)
        b.db_session.commit()

    
'''
def many_to_many_prod_request():

    prods_list = []
    
    # Delete everything so we start clean
    accounts = b.db_session.query(ModelAccount).all()
    for account in accounts:
        b.db_session.delete(account)
        b.db_session.commit()

    requests = b.db_session.query(ModelRequest).all()
    for request in requests:
        b.db_session.delete(request)
        b.db_session.commit()

    products = b.db_session.query(ModelProduct).all()
    for product in products:
        b.db_session.delete(product)
        b.db_session.commit()
    
    
    # Create product
    p = ModelProduct()
    p.name = "some prod"
    p.price = 456
    p.detail = "some detail"
    b.db_session.add(p)
    b.db_session.commit()

    # create Second product
    p2 = ModelProduct()
    p2.name = "some prod"
    p2.price = 456
    p2.detail = "some detail"
    b.db_session.add(p2)
    b.db_session.commit()

    # Create client
    c = ModelClient()
    c.name = "a name"
    c.phone_number: "12222222"
    b.db_session.add(c)
    b.db_session.commit()

    # Create account
    a = ModelAccount()
    a.dni = "23123123"
    a.name = "leo"
    a.password = "12313"
    a.role_id: 1
    a.state_account = 1
    b.db_session.add(a)
    b.db_session.commit()


    # Create Request
    r = ModelRequest()
    r.id_client = c.id
    r.id_account_creator = a.id
    r.id_account_receiver = a.id
    r.time_delivery = 123
    r.direction = "some dir"

    # Create detail
    prods_of_request = ModelProductRequest()
    
    # Populate detail
    product1 = b.db_session.query(ModelProduct).get(p.id)
    product2 = b.db_session.query(ModelProduct).get(p2.id)
    prods_of_request.amount = 3
    prods_of_request.product_ref = product1

    # add product1
    r.products.append(prods_of_request)

    prods_of_request = ModelProductRequest()
    prods_of_request.amount = 3
    prods_of_request.product_ref = product2

    # add product2
    r.products.append(prods_of_request)

    b.db_session.add(r)
    b.db_session.flush()
    b.db_session.refresh(r)
    b.db_session.commit()

'''

# def delete_everything():
#     # Delete everything so we start clean
#     accounts = b.db_session.query(ModelAccount).all()
#     for account in accounts:
#         b.db_session.delete(account)
#         b.db_session.commit()

#     requests = b.db_session.query(ModelRequest).all()
#     for request in requests:
#         b.db_session.delete(request)
#         b.db_session.commit()

#     products = b.db_session.query(ModelProduct).all()
#     for product in products:
#         b.db_session.delete(product)
#         b.db_session.commit()

#     # delete all services in db
#     services = b.db_session.query(ModelService).all()
#     for service in services:
#         b.db_session.delete(service)
#         b.db_session.commit()
    
#     # Delete all clients in db
#     clients = b.db_session.query(ModelClient).all()
#     for client in clients:
#         b.db_session.delete(client)
#         b.db_session.commit()


def test_function():
    # get account by id
    account = b.db_session.query(ModelAccount).get(3)
    role = account.Role.name
    print(account)
    print(account)
                


if __name__ == '__main__':
    #log.info('Create models {}'.format(b.db_name))
    #base.Base.metadata.drop_all(base.engine)
    create_all_models(interactive=True)
    create_default_permissions()
    
    # Specific of this project
    create_default_roles()
    #create_default_services()

    #test of many to many
    #many_to_many_prod_request()

    #delete_everything()
    #test_function()
    
    
