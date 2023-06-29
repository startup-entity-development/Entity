from typing import Dict, Any

from models.model_news_views import ModelNewsViews


from .base import Base
from sqlalchemy import Column, ForeignKey, String, Boolean, Integer, Text, Float

from sqlalchemy.orm import relationship

class ModelNews(Base):
    """News model."""
    __tablename__ = 'News'

    id = Column('id', Integer, primary_key=True, doc="Id of the news ")
    title = Column('title', String(140), doc="Title of the news.")
    body = Column('body', Text(400), doc="Body of the new.")
    created = Column('created', Text(50), doc="Datetime of when the news was created.")
    image_url = Column('image_url', Text(100), doc='image url of the news.')
    account_id = Column('account_id', Integer, ForeignKey('Account.id', ondelete='CASCADE'), doc='Account that created the news.')

    



    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
