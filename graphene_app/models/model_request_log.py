from typing import Dict, Any
from .base import Base
from sqlalchemy import Column, Float, String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship


class ModelRequestLog(Base):
    """Request log model."""
    __tablename__ = 'request_log'

    id = Column('id', Integer, primary_key=True, doc="Id of the request log")
    unique_id = Column('unique_id', String(
        10), doc="Identification of the orignal request so we are free to delete the one that was in pending state")
    client_name = Column('client_name', String(
        30), doc="Client name of the request")
    client_phone = Column('client_phone', String(30),
                          doc="Phone of the client")
    time_delivery = Column('time_delivery', Integer,
                           doc="Aproximate time delivery of the work to be done.")
    direction = Column('direction', String(300), doc="Direction of the client.")
    account_creator_name = Column('account_creator_name', String(
        30), doc="Name of the account that created the request")
    account_creator_dni = Column('account_creator_dni', String(
        30), doc="DNI of the account that created the request")
    account_receiver_name = Column('account_receiver_name', String(
        30), doc="Name of the account to which the request was assigned")
    account_receiver_dni = Column('account_receiver_dni', String(
        30), doc="DNI of the account to which the request was assigned")
    final_state = Column('final_state', String(
        30), doc="The final state to which the request was marked")
    final_price = Column('finalprice', Float,
                         doc="Final price of the request.")
    created = Column('created', Integer, doc="Record created date.")
    detail = Column('detail', String(400), doc="Fianl detail of the request.")
    associated_images = Column('associated_images', String(1000), doc='A json enconded string that identifies the images located in the server')

    products_log = relationship('ModelProductDetailLog')
    service_log = relationship('ModelServiceDetailLog')

    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict


class ModelProductDetailLog(Base):
    "Product Detail Log Model"
    __tablename__ = 'product_detail_log'

    id = Column('id', Integer, primary_key=True, doc="Id of the request log")
    id_request_log = Column('id_request_log', ForeignKey(
        'request_log.id', ondelete='CASCADE'), doc="Id of the request log")
    product_name = Column('product_name', String(
        30), doc="Name of the product used in the detail of the request")
    product_price = Column(
        'product_price', Float, doc="Price of the product used in the detail of the request")
    amount_product = Column('amount_product', Integer, doc="Amount of the product used in the detail of the request")

    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict


class ModelServiceDetailLog(Base):
    "Service Detail Log Model"
    __tablename__ = 'service_detail_log'

    id = Column('id', Integer, primary_key=True, doc="Id of the request log")
    id_request_log = Column('id_request_log', ForeignKey(
        'request_log.id', ondelete='CASCADE'), doc="Id of the request log")
    service_name = Column('service_name', String(
        30), doc="Name of the service used in the detail of the request")
    service_price = Column(
        'service_price', Float, doc="Price of the service used in the detail of the request")
    amount_service = Column('amount_service', Integer, doc="Amount of the service used in the detail of the request")


    def to_dict(self) -> Dict[str, Any]:
        """return  shallow copy ModelAccount to dict """
        obj_dict = self.__dict__.copy()
        del obj_dict['_sa_instance_state']
        return obj_dict
