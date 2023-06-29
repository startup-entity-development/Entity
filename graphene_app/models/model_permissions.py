from typing import Dict, Any

from .base import Base
from sqlalchemy import Column, Integer, Text

from sqlalchemy.orm import relationship
from .model_role_permissions import ModelRolePermission


class ModelPermissions(Base):
    """Permissions model."""
    __tablename__ = 'Permissions'

    id = Column('id', Integer, primary_key=True, doc="Id of the permission")
    name = Column('name', Text(60), doc="Description of the permission.")
    
    permissionListRole = relationship(ModelRolePermission, passive_deletes=True, backref='Permissions')
    
    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict