import enum
from typing import Dict, Any

from .base import Base
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum

from sqlalchemy.orm import relationship

class EnumState(enum.Enum):
    pending = 1
    finished = 2
    canceled = 3
    initiated = 4

'''
    States of request can only be:
        - pending
        - finished
        - canceled
        - initiaded
'''

class ModelRequestState(Base):
        """Request State model. """
        __tablename__ = 'RequestState'

        id = Column('id', Integer, primary_key=True, doc="Id of the request's state")
        id_request = Column('id_request', ForeignKey('Request.id', ondelete='CASCADE'), doc="Id of the request")
        state = Column('state', Enum(EnumState), default=0, nullable=False, doc="State of the request")
        detail = Column('detail', Text(400), doc='Detail of the request state')
        
        request = relationship("ModelRequest", back_populates="state")
        
        def to_dict(self) -> Dict[str, Any]:
                """return  shallow copy ModelAccount to dict """
                obj_dict = self.__dict__.copy()
                del obj_dict['_sa_instance_state']
                return obj_dict
