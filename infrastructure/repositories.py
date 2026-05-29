from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from domain.entities import User, Client, Order, OrderItem, Service, ScheduleSlot, Payment
from domain.value_objects import UserRole, OrderStatus, ServiceType
from domain.interfaces import (
    UserRepository, ClientRepository, OrderRepository, 
    ServiceRepository, ScheduleRepository, PaymentRepository, UnitOfWork
)
from .models import UserModel, ClientModel, ServiceModel, OrderModel, OrderItemModel, ScheduleSlotModel, PaymentModel

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model) -> User:
        return User(
            id=model.id,
            login=model.login,
            password_hash=model.password_hash,
            role=UserRole(model.role),
            full_name=model.full_name,
            phone=model.phone,
            email=model.email,
            created_at=model.created_at
        )

    def get_by_id(self, user_id: int) -> Optional[User]:
        model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(model) if model else None

    def get_by_login(self, login: str) -> Optional[User]:
        model = self.session.query(UserModel).filter(UserModel.login == login).first()
        return self._to_entity(model) if model else None

    def get_by_role(self, role: UserRole) -> List[User]:
        models = self.session.query(UserModel).filter(UserModel.role == role.value).all()
        return [self._to_entity(m) for m in models]

    def create(self, user: User) -> User:
        model = UserModel(
            login=user.login,
            password_hash=user.password_hash,
            role=user.role.value,
            full_name=user.full_name,
            phone=user.phone,
            email=user.email
        )
        self.session.add(model)
        self.session.flush()
        user.id = model.id
        return user

    def update(self, user: User) -> User:
        model = self.session.query(UserModel).filter(UserModel.id == user.id).first()
        if model:
            model.login = user.login
            model.password_hash = user.password_hash
            model.role = user.role.value
            model.full_name = user.full_name
            model.phone = user.phone
            model.email = user.email
            self.session.flush()
        return user

    def delete(self, user_id: int) -> bool:
        model = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def get_all(self) -> List[User]:
        models = self.session.query(UserModel).all()
        return [self._to_entity(m) for m in models]

class SQLAlchemyClientRepository(ClientRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model) -> Client:
        return Client(
            id=model.id,
            full_name=model.full_name,
            phone=model.phone,
            email=model.email,
            birthday=model.birthday,
            discount_percent=model.discount_percent,
            total_spent=model.total_spent,
            created_at=model.created_at
        )

    def get_by_id(self, client_id: int) -> Optional[Client]:
        model = self.session.query(ClientModel).filter(ClientModel.id == client_id).first()
        return self._to_entity(model) if model else None

    def get_by_phone(self, phone: str) -> Optional[Client]:
        model = self.session.query(ClientModel).filter(ClientModel.phone == phone).first()
        return self._to_entity(model) if model else None

    def search(self, query: str) -> List[Client]:
        models = self.session.query(ClientModel).filter(
            ClientModel.full_name.contains(query) | ClientModel.phone.contains(query)
        ).all()
        return [self._to_entity(m) for m in models]

    def create(self, client: Client) -> Client:
        model = ClientModel(
            full_name=client.full_name,
            phone=client.phone,
            email=client.email,
            birthday=client.birthday,
            discount_percent=client.discount_percent,
            total_spent=client.total_spent
        )
        self.session.add(model)
        self.session.flush()
        client.id = model.id
        return client

    def update(self, client: Client) -> Client:
        model = self.session.query(ClientModel).filter(ClientModel.id == client.id).first()
        if model:
            model.full_name = client.full_name
            model.phone = client.phone
            model.email = client.email
            model.birthday = client.birthday
            model.discount_percent = client.discount_percent
            model.total_spent = client.total_spent
            self.session.flush()
        return client

    def delete(self, client_id: int) -> bool:
        model = self.session.query(ClientModel).filter(ClientModel.id == client_id).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def get_all(self) -> List[Client]:
        models = self.session.query(ClientModel).all()
        return [self._to_entity(m) for m in models]

    def get_top_clients(self, limit: int = 10) -> List[Client]:
        models = self.session.query(ClientModel).order_by(ClientModel.total_spent.desc()).limit(limit).all()
        return [self._to_entity(m) for m in models]

class SQLAlchemyServiceRepository(ServiceRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model) -> Service:
        return Service(
            id=model.id,
            name=model.name,
            service_type=ServiceType(model.service_type),
            price=model.price,
            unit=model.unit,
            is_active=model.is_active
        )

    def get_by_id(self, service_id: int) -> Optional[Service]:
        model = self.session.query(ServiceModel).filter(ServiceModel.id == service_id).first()
        return self._to_entity(model) if model else None

    def get_all_active(self) -> List[Service]:
        models = self.session.query(ServiceModel).filter(ServiceModel.is_active == True).all()
        return [self._to_entity(m) for m in models]

    def create(self, service: Service) -> Service:
        model = ServiceModel(
            name=service.name,
            service_type=service.service_type.value,
            price=service.price,
            unit=service.unit,
            is_active=service.is_active
        )
        self.session.add(model)
        self.session.flush()
        service.id = model.id
        return service

class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_entity(self, model) -> Order:
        items = []
        for item_model in model.items:
            service = Service(
                id=item_model.service.id,
                name=item_model.service.name,
                service_type=ServiceType(item_model.service.service_type),
                price=item_model.service.price,
                unit=item_model.service.unit
            )
            items.append(OrderItem(service, item_model.quantity, item_model.price_at_time))

        return Order(
            id=model.id,
            client_id=model.client_id,
            photographer_id=model.photographer_id,
            status=OrderStatus(model.status),
            items=items,
            total_cost=model.total_cost,
            created_at=model.created_at,
            deadline=model.deadline,
            notes=model.notes
        )

    def get_by_id(self, order_id: int) -> Optional[Order]:
        model = self.session.query(OrderModel).filter(OrderModel.id == order_id).first()
        if not model:
            return None
        return self._to_entity(model)

    def get_by_client(self, client_id: int) -> List[Order]:
        models = self.session.query(OrderModel).filter(OrderModel.client_id == client_id).all()
        return [self._to_entity(m) for m in models]

    def get_by_status(self, status: OrderStatus) -> List[Order]:
        models = self.session.query(OrderModel).filter(OrderModel.status == status.value).all()
        return [self._to_entity(m) for m in models]

    def get_by_period(self, start: datetime, end: datetime) -> List[Order]:
        models = self.session.query(OrderModel).filter(
            OrderModel.created_at >= start,
            OrderModel.created_at <= end
        ).all()
        return [self._to_entity(m) for m in models]

    def create(self, order: Order) -> Order:
        model = OrderModel(
            client_id=order.client_id,
            photographer_id=order.photographer_id,
            status=order.status.value,
            total_cost=order.total_cost,
            deadline=order.deadline,
            notes=order.notes
        )
        self.session.add(model)
        self.session.flush()

        for item in order.items:
            item_model = OrderItemModel(
                order_id=model.id,
                service_id=item.service.id,
                quantity=item.quantity,
                price_at_time=item.price_at_time
            )
            self.session.add(item_model)

        order.id = model.id
        return order

    def update(self, order: Order) -> Order:
        model = self.session.query(OrderModel).filter(OrderModel.id == order.id).first()
        if model:
            model.client_id = order.client_id
            model.photographer_id = order.photographer_id
            model.status = order.status.value
            model.total_cost = order.total_cost
            model.deadline = order.deadline
            model.notes = order.notes
            self.session.flush()
        return order

    def update_status(self, order_id: int, status: OrderStatus) -> Order:
        model = self.session.query(OrderModel).filter(OrderModel.id == order_id).first()
        if model:
            model.status = status.value
            self.session.flush()
            return self.get_by_id(order_id)
        raise ValueError("Order not found")

    def get_all(self) -> List[Order]:
        models = self.session.query(OrderModel).all()
        return [self._to_entity(m) for m in models]

class SQLAlchemyScheduleRepository(ScheduleRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_free_slots(self, photographer_id: int, date: str) -> List[ScheduleSlot]:
        models = self.session.query(ScheduleSlotModel).filter(
            ScheduleSlotModel.photographer_id == photographer_id,
            ScheduleSlotModel.date == date,
            ScheduleSlotModel.is_booked == False
        ).all()
        return [ScheduleSlot(m.id, m.photographer_id, m.date, m.time_slot, m.is_booked, m.order_id) for m in models]

    def book_slot(self, slot_id: int, order_id: int) -> ScheduleSlot:
        model = self.session.query(ScheduleSlotModel).filter(ScheduleSlotModel.id == slot_id).first()
        if model and not model.is_booked:
            model.is_booked = True
            model.order_id = order_id
            self.session.flush()
            return ScheduleSlot(model.id, model.photographer_id, model.date, model.time_slot, model.is_booked, model.order_id)
        raise ValueError("Slot not available")

    def get_slots_by_photographer(self, photographer_id: int, date: str) -> List[ScheduleSlot]:
        models = self.session.query(ScheduleSlotModel).filter(
            ScheduleSlotModel.photographer_id == photographer_id,
            ScheduleSlotModel.date == date
        ).all()
        return [ScheduleSlot(m.id, m.photographer_id, m.date, m.time_slot, m.is_booked, m.order_id) for m in models]

    def create_slots(self, slots: List[ScheduleSlot]) -> List[ScheduleSlot]:
        models = []
        for slot in slots:
            model = ScheduleSlotModel(
                photographer_id=slot.photographer_id,
                date=slot.date,
                time_slot=slot.time_slot,
                is_booked=slot.is_booked,
                order_id=slot.order_id
            )
            self.session.add(model)
            models.append(model)
        self.session.flush()
        return [ScheduleSlot(m.id, m.photographer_id, m.date, m.time_slot, m.is_booked, m.order_id) for m in models]

class SQLAlchemyPaymentRepository(PaymentRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(self, payment: Payment) -> Payment:
        model = PaymentModel(
            order_id=payment.order_id,
            amount=payment.amount,
            method=payment.method
        )
        self.session.add(model)
        self.session.flush()
        payment.id = model.id
        return payment

    def get_by_order(self, order_id: int) -> List[Payment]:
        models = self.session.query(PaymentModel).filter(PaymentModel.order_id == order_id).all()
        return [Payment(m.id, m.order_id, m.amount, m.payment_date, m.method) for m in models]

    def get_total_by_period(self, start: datetime, end: datetime) -> float:
        total = self.session.query(PaymentModel.amount).filter(
            PaymentModel.payment_date >= start,
            PaymentModel.payment_date <= end
        ).all()
        return sum(t[0] for t in total)

class SQLAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None

    def __enter__(self):
        self.session = self.session_factory()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        self.session.close()
        self.session = None

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
