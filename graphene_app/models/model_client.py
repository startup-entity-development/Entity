from enum import unique
from typing import Dict, Any

from .base import Base
from sqlalchemy import Column, String, Boolean, Integer, Float, UniqueConstraint

from .model_request import ModelRequest
from sqlalchemy.orm import relationship


class ModelClient(Base):
	"""Client model."""
	__tablename__ = 'Client'

	id = Column('id', Integer, primary_key=True, doc="Id of the client ")
	name = Column('name', String(30), doc="Name of the client.")
	# direction = Column('direction', String(30), doc="Direction of the client.")
	phone_number = Column('phone_number', String(20), doc='Phone nomber of the client', unique=True)

	clientList = relationship(ModelRequest, passive_deletes=True, backref='Client')

	def to_dict(self) -> Dict[str, Any]:
		"""return  shallow copy ModelClient to dict """
		obj_dict = self.__dict__.copy()
		del obj_dict['_sa_instance_state']
		return obj_dict
