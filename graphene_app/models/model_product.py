from typing import Dict, Any

from .base import Base
from sqlalchemy import Column, ForeignKey, String, Boolean, Integer, Text, Float

#from .model_product_request import ModelProductRequest
from sqlalchemy.orm import relationship

class ModelProduct(Base):
    """Product model."""
    __tablename__ = 'Product'

    id = Column('id', Integer, primary_key=True, doc="Id of the product ")
    name = Column('name', String(30), doc="Name of the product.")
    detail = Column('detail', Text(60), doc="Detail of the product.")
    length = Column('lenght', Float(2), doc='Length of the product')
    width = Column('width', Float(2), doc="Length of the product")
    denomination = Column('denomination', Text(60), doc="denomination of the product")
    price = Column('price', Float(2), doc="Price of the product")
    price2 = Column('price2', Float(2), doc="another price for the product")
    is_in_stock = Column('is_in_stock', Boolean, doc='Indicate if there is stock of a product', default=1)
    brand_id = Column('brand_id', Integer, ForeignKey('Brand.id', ondelete='CASCADE'), doc='Brand of the product.')
    category_id = Column('category_id', Integer, ForeignKey('Category.id', ondelete='CASCADE'), doc='Category of the product.')


    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
