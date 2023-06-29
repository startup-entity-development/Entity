from typing import Dict, Any

from .base import Base
from sqlalchemy import Column, String, Boolean, Integer, Text, Float

#from .model_service_request import ModelServiceRequest
from sqlalchemy.orm import relationship


class ModelService(Base):
    """Service model."""
    __tablename__ = 'Service'

    id = Column('id', Integer, primary_key=True, doc="Id of the service ")
    name = Column('name', String(30), doc="Name of the service.")
    detail = Column('detail', Text(60), doc="Detail of the service.")
    price = Column('price', Float(2), doc="Price of the service")

    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
