from typing import Dict, Any

from models.model_service import ModelService

from .base import Base
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship


class ModelServiceRequest(Base):
    """Many to Many model Service-Request."""
    __tablename__ = 'service_request'

    id_request = Column('id_request', ForeignKey('Request.id', ondelete='CASCADE'), doc="Id of the request", primary_key=True)
    id_service = Column('id_service', ForeignKey('Service.id', ondelete='CASCADE'), doc="Id of the service used in a request", primary_key=True)
    amount =  Column('amount', Integer, doc="Amount of the requested service")

    service_ref = relationship('ModelService')


    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
