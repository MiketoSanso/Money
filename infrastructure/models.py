from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False)
    role = Column(String(30), nullable=False)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class ClientModel(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), nullable=False)
    birthday = Column(String(10))
    discount_percent = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)

class ServiceModel(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    service_type = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)


class OrderModel(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    photographer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    status = Column(String(30), nullable=False)
    total_cost = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    deadline = Column(DateTime, nullable=True)
    notes = Column(Text, default="")

    client = relationship("ClientModel")
    photographer = relationship("UserModel")
    items = relationship("OrderItemModel", back_populates="order", lazy='joined')


class OrderItemModel(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    price_at_time = Column(Float, nullable=False)

    order = relationship("OrderModel", back_populates="items")
    service = relationship("ServiceModel")

class ScheduleSlotModel(Base):
    __tablename__ = 'schedule_slots'

    id = Column(Integer, primary_key=True)
    photographer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(String(10), nullable=False)
    time_slot = Column(String(5), nullable=False)
    is_booked = Column(Boolean, default=False)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)

class PaymentModel(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.now)
    method = Column(String(20), nullable=False)
