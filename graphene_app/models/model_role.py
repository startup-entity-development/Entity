from typing import Dict, Any

from .base import Base
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from models.model_account import ModelAccount
from .model_role_permissions import ModelRolePermission
from sqlalchemy.orm import relationship


class ModelRole(Base):
    """Role model."""
    __tablename__ = 'Role'

    id = Column('id', Integer, primary_key=True,
                doc="Id of the Role")
    name = Column('name', String(30), doc="Role asociated with permissions.", unique=True)


    roleList = relationship(
        ModelAccount, passive_deletes=True, backref='Role')
    roleListPerms = relationship(ModelRolePermission, passive_deletes=True, backref='Role')

    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
