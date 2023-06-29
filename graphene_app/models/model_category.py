from typing import Dict, Any
from models.model_product import ModelProduct
from .base import Base
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship

class ModelCategory(Base):
    """Category model."""
    __tablename__ = 'Category'

    id = Column('id', Integer, primary_key=True, doc="Id of the category")
    name = Column('name', String(30), doc="Name of the category.", unique=True)
    categoryList = relationship(
        ModelProduct, passive_deletes=True, backref='Category')

    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelCategory to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
