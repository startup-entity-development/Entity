from typing import Dict, Any

from .base import Base
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship



class ModelProductRequest(Base):
    """Many to Many model Product-Request."""
    __tablename__ = 'product_request'

    id_request = Column('id_request', ForeignKey('Request.id', ondelete='CASCADE'), doc="Id of the request", primary_key=True)
    id_product = Column('id_product', ForeignKey('Product.id', ondelete='CASCADE'), doc="Id of the product used in a request", primary_key=True)
    amount =  Column('amount', Integer, doc="Amount of the requested product")
    
    product_ref = relationship("ModelProduct")

    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelProductRequest to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict