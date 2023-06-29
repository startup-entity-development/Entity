from typing import Dict, Any

from models.model_news import ModelNews
from models.model_news_views import ModelNewsViews

from .base import Base, db_session
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey

from .model_role_permissions import ModelRolePermission
from .model_permissions import ModelPermissions
from sqlalchemy.orm import relationship


class ModelAccount(Base):
    """Account model."""
    __tablename__ = 'Account'

    id = Column('id', Integer, primary_key=True, doc="Id of the account of the user ")
    dni = Column('dni', String(30), doc="National identification document of the person.", unique=True)
    name = Column('name', String(30), doc="Name of the person.")
    password = Column('password', String(1000), nullable=False, doc="Password of the account.")
    role_id = Column('role_id', Integer, ForeignKey('Role.id', ondelete='CASCADE'), doc='Role of the account.')
    state_account = Column('state_account', Boolean, default=1, nullable=False, doc="Estate of the account")

    username = Column('username', String(30), doc="Username of the account.", unique=True)
    location = Column ('location', String(100), doc='Location of the person')
    phone_number = Column('phone_number', String(20), doc='Phone Number of the account', unique=True)
    email = Column('email', String(60), doc="Email of the person.", unique=True)
    
        
    accountList = relationship(ModelNews, passive_deletes=True, backref='Account')
    accountListViews = relationship(ModelNewsViews, passive_deletes=True, backref='Account')

    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict

    def has_perm(self, perm):
        ''' If account have permission, return True.
            Else, raise excep.    
        '''
        permissions = db_session.query(ModelRolePermission).filter_by(id_role=self.role_id)
        for p in permissions:
            db_perm = db_session.query(ModelPermissions).get(p.id_permission)
            if perm == db_perm.name:
                return True
        raise Exception(f'Account {self.name} have no permission: {perm}.')   

    


