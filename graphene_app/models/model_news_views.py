from typing import Dict, Any


from .base import Base
from sqlalchemy import Column, ForeignKey, String, Boolean, Integer, Text, Float

from sqlalchemy.orm import relationship

class ModelNewsViews(Base):
    """News Views model."""
    __tablename__ = 'NewsViews'

    id = Column('id', Integer, primary_key=True, doc="Id of the news view")
    viewed_at = Column('viewed_at', Text(50), doc="Datetime of when the news was saw.")
    partially_viewed_at = Column('partially_viewed_at', Text(50), doc="Datetime of when the news was partyally saw (just the title).")
    news_id = Column('news_id', Integer, ForeignKey('News.id', ondelete='CASCADE'), doc='The news that where saw.')
    account_id = Column('account_id', Integer, ForeignKey('Account.id', ondelete='CASCADE'), doc='Account that saw the new.')

    newsViewsList = relationship(
         "ModelNews", backref='NewsViews')
    
    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
