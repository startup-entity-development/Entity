from typing import Dict, Any

from .base import Base
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey


class ModelRolePermission(Base):
    """Role Permissions model."""
    __tablename__ = 'role_permissions'

    id = Column('id', Integer, primary_key=True, doc="Id of the role permissions")
    id_role = Column('id_role', ForeignKey('Role.id', ondelete='CASCADE'), doc="Id of the role")
    id_permission = Column('id_permission', ForeignKey('Permissions.id', ondelete='CASCADE'), doc="Id of the permission")
    
    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict