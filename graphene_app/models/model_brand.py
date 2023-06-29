from typing import Dict, Any
from models.model_product import ModelProduct
from .base import Base
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

class ModelBrand(Base):
    """Brand model."""
    __tablename__ = 'Brand'

    id = Column('id', Integer, primary_key=True, doc="Id of the brand")
    name = Column('name', String(30), doc="Name of the brand.")
    brandList = relationship(
        ModelProduct, passive_deletes=True, backref='Brand')

    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelBrand to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
