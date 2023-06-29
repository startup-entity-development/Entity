from enum import unique
from typing import Dict, Any


from .base import Base
from sqlalchemy import Column, Float, String, Boolean, Integer, ForeignKey

from .model_state_request import ModelRequestState
from .model_service_request import ModelServiceRequest
from .model_product_request import ModelProductRequest

#test
#from .model_product import ModelProduct

from sqlalchemy.orm import relationship


class ModelRequest(Base):
        """Request model."""
        __tablename__ = 'Request'

        id = Column('id', Integer, primary_key=True, doc="Id of the request ")
        unique_id = Column('unique_id', String(10), unique=True, doc="Id for users to be able to identificate the request") # usefull in the request_log as well
        id_client = Column('id_client', Integer, ForeignKey('Client.id', ondelete='CASCADE'), doc="Id of the client in the request")
        id_account_creator = Column('id_account_creator', Integer, ForeignKey('Account.id', ondelete='CASCADE'), doc="Id of the account that created the request")
        id_account_receiver = Column('id_account_receiver', Integer, ForeignKey('Account.id', ondelete='CASCADE'), doc="Id of the account that created the request")
        time_delivery = Column('time_delivery', Integer, doc="Aproximate time delivery of the work to be done.")
        created = Column('created', Integer, doc="Record created date.")
        edited = Column('edited', Integer, doc="Record edited date.")
        direction = Column('direction', String(300), doc="Direction of the client.")
        final_price = Column('finalprice', Float, doc="Final price of the request.")
        
        products = relationship('ModelProductRequest')
        services = relationship('ModelServiceRequest')
        state = relationship("ModelRequestState", uselist=False, back_populates="request")

        account_creator = relationship("ModelAccount", foreign_keys=[id_account_creator])
        account_receiver = relationship("ModelAccount", foreign_keys=[id_account_receiver])

        def to_dict(self) -> Dict[str, Any]:
                """return  shallow copy ModelAccount to dict """
                obj_dict = self.__dict__.copy()
                del obj_dict['_sa_instance_state']
                return obj_dict
