import os

# Создаём структуру папок
folders = [
    'domain',
    'application',
    'infrastructure',
    'interfaces/templates',
    'interfaces/static/css',
    'tests'
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)

# Создаём __init__.py файлы
init_files = [
    'domain/__init__.py',
    'application/__init__.py',
    'infrastructure/__init__.py',
    'interfaces/__init__.py',
    'tests/__init__.py'
]

for init_file in init_files:
    with open(init_file, 'w') as f:
        f.write('')

# ========== config.py ==========
with open('config.py', 'w', encoding='utf-8') as f:
    f.write('''import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'studio-secret-key-2025'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///photo_studio.db'
    DEBUG = True
''')

# ========== domain/value_objects.py ==========
with open('domain/value_objects.py', 'w', encoding='utf-8') as f:
    f.write('''from dataclasses import dataclass
from enum import Enum
import re

class UserRole(Enum):
    ADMIN = "admin"
    DIRECTOR = "director"
    ACCOUNTANT = "accountant"
    ADMINISTRATOR = "administrator"
    PHOTOGRAPHER = "photographer"
    CLIENT = "client"

class OrderStatus(Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    COMPLETED = "completed"
    PAID = "paid"
    CANCELLED = "cancelled"

class ServiceType(Enum):
    PHOTO_SESSION = "photo_session"
    PRINT = "print"
    RETOUCH = "retouch"
    STUDIO_RENT = "studio_rent"

@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$', self.value):
            raise ValueError(f"Invalid email: {self.value}")

@dataclass(frozen=True)
class Phone:
    value: str

    def __post_init__(self):
        digits = re.sub(r'\\D', '', self.value)
        if len(digits) < 10 or len(digits) > 12:
            raise ValueError(f"Invalid phone: {self.value}")

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "RUB"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
''')

# ========== domain/entities.py ==========
with open('domain/entities.py', 'w', encoding='utf-8') as f:
    f.write('''from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .value_objects import UserRole, OrderStatus, ServiceType, Email, Phone, Money

@dataclass
class User:
    id: Optional[int]
    login: str
    password_hash: str
    role: UserRole
    full_name: str
    phone: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Client:
    id: Optional[int]
    full_name: str
    phone: str
    email: str
    birthday: Optional[str]
    discount_percent: int = 0
    total_spent: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def apply_discount(self, amount: Money) -> Money:
        if self.discount_percent > 0:
            discounted = amount.amount * (100 - self.discount_percent) / 100
            return Money(discounted, amount.currency)
        return amount

@dataclass
class Service:
    id: Optional[int]
    name: str
    service_type: ServiceType
    price: float
    unit: str
    is_active: bool = True

@dataclass
class OrderItem:
    service: Service
    quantity: float
    price_at_time: float

    def subtotal(self) -> float:
        return self.quantity * self.price_at_time

@dataclass
class Order:
    id: Optional[int]
    client_id: int
    photographer_id: Optional[int]
    status: OrderStatus
    items: List[OrderItem]
    total_cost: float
    created_at: datetime
    deadline: Optional[datetime]
    notes: str = ""

    def calculate_total(self) -> float:
        return sum(item.subtotal() for item in self.items)

    def can_cancel(self) -> bool:
        return self.status in [OrderStatus.NEW, OrderStatus.CONFIRMED]

    def can_proceed(self) -> bool:
        return self.status in [OrderStatus.NEW, OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS]

@dataclass
class ScheduleSlot:
    id: Optional[int]
    photographer_id: int
    date: str
    time_slot: str
    is_booked: bool
    order_id: Optional[int]

@dataclass
class Payment:
    id: Optional[int]
    order_id: int
    amount: float
    payment_date: datetime
    method: str
''')

# ========== domain/interfaces.py ==========
with open('domain/interfaces.py', 'w', encoding='utf-8') as f:
    f.write('''from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from .entities import User, Client, Order, Service, ScheduleSlot, Payment
from .value_objects import UserRole, OrderStatus

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]: pass
    @abstractmethod
    def get_by_login(self, login: str) -> Optional[User]: pass
    @abstractmethod
    def get_by_role(self, role: UserRole) -> List[User]: pass
    @abstractmethod
    def create(self, user: User) -> User: pass
    @abstractmethod
    def update(self, user: User) -> User: pass
    @abstractmethod
    def delete(self, user_id: int) -> bool: pass
    @abstractmethod
    def get_all(self) -> List[User]: pass

class ClientRepository(ABC):
    @abstractmethod
    def get_by_id(self, client_id: int) -> Optional[Client]: pass
    @abstractmethod
    def get_by_phone(self, phone: str) -> Optional[Client]: pass
    @abstractmethod
    def search(self, query: str) -> List[Client]: pass
    @abstractmethod
    def create(self, client: Client) -> Client: pass
    @abstractmethod
    def update(self, client: Client) -> Client: pass
    @abstractmethod
    def delete(self, client_id: int) -> bool: pass
    @abstractmethod
    def get_all(self) -> List[Client]: pass
    @abstractmethod
    def get_top_clients(self, limit: int = 10) -> List[Client]: pass

class OrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]: pass
    @abstractmethod
    def get_by_client(self, client_id: int) -> List[Order]: pass
    @abstractmethod
    def get_by_status(self, status: OrderStatus) -> List[Order]: pass
    @abstractmethod
    def get_by_period(self, start: datetime, end: datetime) -> List[Order]: pass
    @abstractmethod
    def create(self, order: Order) -> Order: pass
    @abstractmethod
    def update(self, order: Order) -> Order: pass
    @abstractmethod
    def update_status(self, order_id: int, status: OrderStatus) -> Order: pass
    @abstractmethod
    def get_all(self) -> List[Order]: pass

class ServiceRepository(ABC):
    @abstractmethod
    def get_by_id(self, service_id: int) -> Optional[Service]: pass
    @abstractmethod
    def get_all_active(self) -> List[Service]: pass
    @abstractmethod
    def create(self, service: Service) -> Service: pass

class ScheduleRepository(ABC):
    @abstractmethod
    def get_free_slots(self, photographer_id: int, date: str) -> List[ScheduleSlot]: pass
    @abstractmethod
    def book_slot(self, slot_id: int, order_id: int) -> ScheduleSlot: pass
    @abstractmethod
    def get_slots_by_photographer(self, photographer_id: int, date: str) -> List[ScheduleSlot]: pass
    @abstractmethod
    def create_slots(self, slots: List[ScheduleSlot]) -> List[ScheduleSlot]: pass

class PaymentRepository(ABC):
    @abstractmethod
    def create(self, payment: Payment) -> Payment: pass
    @abstractmethod
    def get_by_order(self, order_id: int) -> List[Payment]: pass
    @abstractmethod
    def get_total_by_period(self, start: datetime, end: datetime) -> float: pass

class UnitOfWork(ABC):
    @abstractmethod
    def __enter__(self): pass
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb): pass
    @abstractmethod
    def commit(self): pass
    @abstractmethod
    def rollback(self): pass
''')

# ========== application/dto.py ==========
with open('application/dto.py', 'w', encoding='utf-8') as f:
    f.write('''from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class CreateClientDTO:
    full_name: str
    phone: str
    email: str
    birthday: Optional[str] = None

@dataclass
class CreateOrderDTO:
    client_id: int
    photographer_id: Optional[int]
    items: List[dict]
    deadline: Optional[str]
    notes: str = ""

@dataclass
class OrderResponseDTO:
    id: int
    client_name: str
    photographer_name: Optional[str]
    status: str
    total_cost: float
    created_at: str
    items_count: int

@dataclass
class ReportDTO:
    period_start: str
    period_end: str
    total_orders: int
    total_revenue: float
    avg_order_value: float
    top_clients: List[dict]
    photographer_stats: List[dict]
''')

# ========== application/use_cases.py (сокращённая версия) ==========
with open('application/use_cases.py', 'w', encoding='utf-8') as f:
    f.write('''from datetime import datetime
from typing import List, Optional
from domain.entities import Client, Order, OrderItem, Service
from domain.value_objects import OrderStatus, Money, UserRole
from domain.interfaces import (
    ClientRepository, OrderRepository, ServiceRepository, 
    ScheduleRepository, PaymentRepository, UserRepository, UnitOfWork
)
from .dto import CreateClientDTO, CreateOrderDTO, ReportDTO

class CreateClientUseCase:
    def __init__(self, client_repo: ClientRepository, uow: UnitOfWork):
        self.client_repo = client_repo
        self.uow = uow

    def execute(self, dto: CreateClientDTO) -> Client:
        existing = self.client_repo.get_by_phone(dto.phone)
        if existing:
            raise ValueError(f"Client with phone {dto.phone} already exists")

        client = Client(
            id=None,
            full_name=dto.full_name,
            phone=dto.phone,
            email=dto.email,
            birthday=dto.birthday,
            discount_percent=0,
            total_spent=0.0
        )

        with self.uow:
            created = self.client_repo.create(client)
            self.uow.commit()
            return created

class CreateOrderUseCase:
    def __init__(self, order_repo: OrderRepository, client_repo: ClientRepository, 
                 service_repo: ServiceRepository, schedule_repo: ScheduleRepository,
                 uow: UnitOfWork):
        self.order_repo = order_repo
        self.client_repo = client_repo
        self.service_repo = service_repo
        self.schedule_repo = schedule_repo
        self.uow = uow

    def execute(self, dto: CreateOrderDTO) -> Order:
        client = self.client_repo.get_by_id(dto.client_id)
        if not client:
            raise ValueError("Client not found")

        items = []
        total = 0.0
        for item_data in dto.items:
            service = self.service_repo.get_by_id(item_data['service_id'])
            if not service:
                raise ValueError(f"Service {item_data['service_id']} not found")
            order_item = OrderItem(
                service=service,
                quantity=item_data['quantity'],
                price_at_time=service.price
            )
            items.append(order_item)
            total += order_item.subtotal()

        discounted_total = client.apply_discount(Money(total)).amount

        deadline = datetime.fromisoformat(dto.deadline) if dto.deadline else None

        order = Order(
            id=None,
            client_id=dto.client_id,
            photographer_id=dto.photographer_id,
            status=OrderStatus.NEW,
            items=items,
            total_cost=discounted_total,
            created_at=datetime.now(),
            deadline=deadline,
            notes=dto.notes
        )

        with self.uow:
            created = self.order_repo.create(order)
            self.uow.commit()
            return created

class UpdateOrderStatusUseCase:
    def __init__(self, order_repo: OrderRepository, uow: UnitOfWork):
        self.order_repo = order_repo
        self.uow = uow

    def execute(self, order_id: int, new_status: OrderStatus) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if not order.can_proceed() and new_status != OrderStatus.CANCELLED:
            raise ValueError(f"Cannot change status from {order.status.value}")

        with self.uow:
            updated = self.order_repo.update_status(order_id, new_status)
            self.uow.commit()
            return updated

class CalculateCostUseCase:
    def __init__(self, service_repo: ServiceRepository):
        self.service_repo = service_repo

    def execute(self, items: List[dict]) -> float:
        total = 0.0
        for item in items:
            service = self.service_repo.get_by_id(item['service_id'])
            if not service:
                raise ValueError(f"Service {item['service_id']} not found")
            total += service.price * item['quantity']
        return total

class GetDashboardStatsUseCase:
    def __init__(self, order_repo: OrderRepository, client_repo: ClientRepository):
        self.order_repo = order_repo
        self.client_repo = client_repo

    def execute(self) -> dict:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        orders_today = self.order_repo.get_by_period(today, datetime.now())

        active_orders = self.order_repo.get_by_status(OrderStatus.IN_PROGRESS)
        active_orders.extend(self.order_repo.get_by_status(OrderStatus.CONFIRMED))

        return {
            'total_clients': len(self.client_repo.get_all()),
            'orders_today': len(orders_today),
            'active_orders': len(active_orders),
            'revenue_today': sum(o.total_cost for o in orders_today if o.status == OrderStatus.PAID)
        }

class GenerateReportUseCase:
    def __init__(self, order_repo: OrderRepository, payment_repo: PaymentRepository, 
                 client_repo: ClientRepository, user_repo: UserRepository):
        self.order_repo = order_repo
        self.payment_repo = payment_repo
        self.client_repo = client_repo
        self.user_repo = user_repo

    def execute(self, start_date: str, end_date: str) -> ReportDTO:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        orders = self.order_repo.get_by_period(start, end)
        paid_orders = [o for o in orders if o.status == OrderStatus.PAID]

        revenue = sum(o.total_cost for o in paid_orders)

        clients = self.client_repo.get_all()
        client_spending = {c.id: 0 for c in clients}
        for o in paid_orders:
            if o.client_id in client_spending:
                client_spending[o.client_id] += o.total_cost

        top_clients = sorted(
            [{"id": cid, "full_name": next((c.full_name for c in clients if c.id == cid), ""), "total": total}
             for cid, total in client_spending.items() if total > 0],
            key=lambda x: x["total"], reverse=True
        )[:5]

        photographers = self.user_repo.get_by_role(UserRole.PHOTOGRAPHER)
        photographer_stats = []
        for p in photographers:
            photographer_orders = [o for o in orders if o.photographer_id == p.id]
            photographer_stats.append({
                "name": p.full_name,
                "orders_count": len(photographer_orders),
                "revenue": sum(o.total_cost for o in photographer_orders if o.status == OrderStatus.PAID)
            })

        return ReportDTO(
            period_start=start_date,
            period_end=end_date,
            total_orders=len(orders),
            total_revenue=revenue,
            avg_order_value=revenue / len(orders) if orders else 0,
            top_clients=top_clients,
            photographer_stats=photographer_stats
        )
''')

# ========== infrastructure/models.py ==========
with open('infrastructure/models.py', 'w', encoding='utf-8') as f:
    f.write('''from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
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

class OrderItemModel(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False)
    quantity = Column(Float, nullable=False)
    price_at_time = Column(Float, nullable=False)

    order = relationship("OrderModel")
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
''')

# ========== infrastructure/database.py ==========
with open('infrastructure/database.py', 'w', encoding='utf-8') as f:
    f.write('''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base

class Database:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=True)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine))

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.SessionLocal()

    def close(self):
        self.SessionLocal.remove()
''')

# ========== infrastructure/repositories.py (упрощённая, но рабочая версия) ==========
with open('infrastructure/repositories.py', 'w', encoding='utf-8') as f:
    f.write('''from typing import List, Optional
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
''')

# ========== app.py (основной файл) ==========
with open('app.py', 'w', encoding='utf-8') as f:
    f.write('''from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import hashlib

from config import Config
from infrastructure.database import Database
from infrastructure.repositories import (
    SQLAlchemyUserRepository, SQLAlchemyClientRepository, SQLAlchemyOrderRepository,
    SQLAlchemyServiceRepository, SQLAlchemyScheduleRepository, SQLAlchemyPaymentRepository,
    SQLAlchemyUnitOfWork
)
from application.use_cases import (
    CreateClientUseCase, CreateOrderUseCase, UpdateOrderStatusUseCase,
    CalculateCostUseCase, GetDashboardStatsUseCase, GenerateReportUseCase
)
from application.dto import CreateClientDTO, CreateOrderDTO
from domain.value_objects import UserRole, OrderStatus, ServiceType
from domain.entities import User, Service

app = Flask(__name__)
app.config.from_object(Config)

db = Database(app.config['DATABASE_URL'])
db.create_tables()

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        with db.get_session() as sess:
            repo = SQLAlchemyUserRepository(sess)
            return repo.get_by_id(user_id)
    return None

def login_required(role=None):
    def decorator(f):
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect(url_for('login_page'))
            if role and user.role != role:
                return "Access denied", 403
            return f(*args, **kwargs)
        wrapped.__name__ = f.__name__
        return wrapped
    return decorator

@app.route('/')
def index():
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        password_hash = hashlib.md5(password.encode()).hexdigest()

        with db.get_session() as sess:
            repo = SQLAlchemyUserRepository(sess)
            user = repo.get_by_login(login)

            if user and user.password_hash == password_hash:
                session['user_id'] = user.id
                return redirect(url_for('dashboard'))
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/dashboard')
@login_required()
def dashboard():
    user = get_current_user()
    with db.get_session() as sess:
        order_repo = SQLAlchemyOrderRepository(sess)
        client_repo = SQLAlchemyClientRepository(sess)
        use_case = GetDashboardStatsUseCase(order_repo, client_repo)
        stats = use_case.execute()

    return render_template('dashboard.html', user=user, stats=stats)

@app.route('/clients')
@login_required()
def clients_list():
    user = get_current_user()
    with db.get_session() as sess:
        repo = SQLAlchemyClientRepository(sess)
        clients = repo.get_all()

    return render_template('clients.html', user=user, clients=clients)

@app.route('/clients/create', methods=['GET', 'POST'])
@login_required()
def client_create():
    user = get_current_user()
    if request.method == 'POST':
        dto = CreateClientDTO(
            full_name=request.form['full_name'],
            phone=request.form['phone'],
            email=request.form['email'],
            birthday=request.form.get('birthday')
        )

        with db.get_session() as sess:
            repo = SQLAlchemyClientRepository(sess)
            uow = SQLAlchemyUnitOfWork(lambda: sess)
            use_case = CreateClientUseCase(repo, uow)
            try:
                client = use_case.execute(dto)
                return redirect(url_for('clients_list'))
            except ValueError as e:
                return render_template('client_form.html', user=user, error=str(e))

    return render_template('client_form.html', user=user)

@app.route('/orders')
@login_required()
def orders_list():
    user = get_current_user()
    with db.get_session() as sess:
        repo = SQLAlchemyOrderRepository(sess)
        orders = repo.get_all()

    return render_template('orders.html', user=user, orders=orders)

@app.route('/orders/create', methods=['GET', 'POST'])
@login_required()
def order_create():
    user = get_current_user()

    with db.get_session() as sess:
        client_repo = SQLAlchemyClientRepository(sess)
        service_repo = SQLAlchemyServiceRepository(sess)
        clients = client_repo.get_all()
        services = service_repo.get_all_active()

    if request.method == 'POST':
        items = []
        service_ids = request.form.getlist('service_id[]')
        quantities = request.form.getlist('quantity[]')

        for sid, qty in zip(service_ids, quantities):
            if sid and float(qty) > 0:
                items.append({'service_id': int(sid), 'quantity': float(qty)})

        dto = CreateOrderDTO(
            client_id=int(request.form['client_id']),
            photographer_id=int(request.form['photographer_id']) if request.form.get('photographer_id') else None,
            items=items,
            deadline=request.form.get('deadline'),
            notes=request.form.get('notes', '')
        )

        with db.get_session() as sess:
            order_repo = SQLAlchemyOrderRepository(sess)
            client_repo2 = SQLAlchemyClientRepository(sess)
            service_repo2 = SQLAlchemyServiceRepository(sess)
            schedule_repo = SQLAlchemyScheduleRepository(sess)
            uow = SQLAlchemyUnitOfWork(lambda: sess)
            use_case = CreateOrderUseCase(order_repo, client_repo2, service_repo2, schedule_repo, uow)
            try:
                order = use_case.execute(dto)
                return redirect(url_for('orders_list'))
            except ValueError as e:
                return render_template('order_form.html', user=user, clients=clients, services=services, error=str(e))

    return render_template('order_form.html', user=user, clients=clients, services=services)

@app.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required()
def order_update_status(order_id):
    new_status = request.form['status']
    with db.get_session() as sess:
        repo = SQLAlchemyOrderRepository(sess)
        uow = SQLAlchemyUnitOfWork(lambda: sess)
        use_case = UpdateOrderStatusUseCase(repo, uow)
        try:
            use_case.execute(order_id, OrderStatus(new_status))
        except ValueError as e:
            return str(e), 400
    return redirect(url_for('orders_list'))

@app.route('/api/calculate-cost', methods=['POST'])
def api_calculate_cost():
    data = request.get_json()
    items = data.get('items', [])

    with db.get_session() as sess:
        repo = SQLAlchemyServiceRepository(sess)
        use_case = CalculateCostUseCase(repo)
        try:
            total = use_case.execute(items)
            return jsonify({'total': total})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

@app.route('/calendar')
@login_required()
def calendar():
    user = get_current_user()
    return render_template('calendar.html', user=user)

@app.route('/reports')
@login_required()
def reports():
    user = get_current_user()

    start_date = request.args.get('start_date', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    with db.get_session() as sess:
        order_repo = SQLAlchemyOrderRepository(sess)
        payment_repo = SQLAlchemyPaymentRepository(sess)
        client_repo = SQLAlchemyClientRepository(sess)
        user_repo = SQLAlchemyUserRepository(sess)
        use_case = GenerateReportUseCase(order_repo, payment_repo, client_repo, user_repo)
        report = use_case.execute(start_date, end_date)

    return render_template('reports.html', user=user, report=report, start_date=start_date, end_date=end_date)

@app.route('/users')
@login_required(role=UserRole.ADMIN)
def users_list():
    user = get_current_user()
    with db.get_session() as sess:
        repo = SQLAlchemyUserRepository(sess)
        users = repo.get_all()
    return render_template('users.html', user=user, users=users)

def init_demo_data():
    with db.get_session() as sess:
        user_repo = SQLAlchemyUserRepository(sess)

        existing = user_repo.get_by_login('admin')
        if not existing:
            admin = User(
                id=None,
                login='admin',
                password_hash=hashlib.md5('admin123'.encode()).hexdigest(),
                role=UserRole.ADMIN,
                full_name='Администратор',
                phone='+7(999)123-45-67',
                email='admin@photostudio.ru'
            )
            user_repo.create(admin)

            photographer = User(
                id=None,
                login='photographer',
                password_hash=hashlib.md5('photo123'.encode()).hexdigest(),
                role=UserRole.PHOTOGRAPHER,
                full_name='Иванов Иван',
                phone='+7(999)765-43-21',
                email='ivan@photostudio.ru'
            )
            user_repo.create(photographer)
            sess.commit()

        service_repo = SQLAlchemyServiceRepository(sess)
        if len(service_repo.get_all_active()) == 0:
            services = [
                ('Фотосессия 1 час', 'photo_session', 5000.0, 'час'),
                ('Печать фото 10x15', 'print', 50.0, 'шт'),
                ('Ретушь 1 фото', 'retouch', 300.0, 'шт'),
                ('Аренда студии 1 час', 'studio_rent', 2500.0, 'час'),
            ]
            for name, s_type, price, unit in services:
                svc = Service(id=None, name=name, service_type=ServiceType(s_type), price=price, unit=unit)
                service_repo.create(svc)
            sess.commit()

with app.app_context():
    init_demo_data()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
''')

# ========== HTML шаблоны ==========

# base.html
with open('interfaces/templates/base.html', 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Фотостудия - Управление заказами</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('dashboard') }}">Фотостудия «Объектив»</a>
            <div>
                {% if user %}
                <span class="text-white me-3">Привет, {{ user.full_name }} ({{ user.role.value }})</span>
                <a href="{{ url_for('clients_list') }}" class="btn btn-outline-light btn-sm me-1">Клиенты</a>
                <a href="{{ url_for('orders_list') }}" class="btn btn-outline-light btn-sm me-1">Заказы</a>
                <a href="{{ url_for('reports') }}" class="btn btn-outline-light btn-sm me-1">Отчёты</a>
                <a href="{{ url_for('logout') }}" class="btn btn-outline-light btn-sm">Выйти</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
''')

# login.html
with open('interfaces/templates/login.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-4">
        <h2 class="text-center">Вход в систему</h2>
        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="mb-3">
                <label>Логин</label>
                <input type="text" name="login" class="form-control" required>
            </div>
            <div class="mb-3">
                <label>Пароль</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Войти</button>
        </form>
        <div class="mt-3 text-muted small">Демо: admin / admin123 | photographer / photo123</div>
    </div>
</div>
{% endblock %}
''')

# dashboard.html
with open('interfaces/templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<h1>Панель управления</h1>
<div class="row mt-4">
    <div class="col-md-3">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5>Клиентов</h5>
                <h2>{{ stats.total_clients }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5>Заказов сегодня</h5>
                <h2>{{ stats.orders_today }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-warning">
            <div class="card-body">
                <h5>Активных заказов</h5>
                <h2>{{ stats.active_orders }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-white bg-danger">
            <div class="card-body">
                <h5>Выручка сегодня</h5>
                <h2>{{ stats.revenue_today }} ₽</h2>
            </div>
        </div>
    </div>
</div>
<div class="row mt-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">Быстрые действия</div>
            <div class="card-body">
                <a href="{{ url_for('client_create') }}" class="btn btn-outline-primary">+ Новый клиент</a>
                <a href="{{ url_for('order_create') }}" class="btn btn-outline-success">+ Новый заказ</a>
                <a href="{{ url_for('calendar') }}" class="btn btn-outline-info">Расписание</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''')

# clients.html
with open('interfaces/templates/clients.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h1>Клиенты</h1>
    <a href="{{ url_for('client_create') }}" class="btn btn-primary">+ Добавить клиента</a>
</div>
<table class="table table-striped">
    <thead>
        <tr><th>ID</th><th>ФИО</th><th>Телефон</th><th>Email</th><th>Скидка</th><th>Потрачено</th></tr>
    </thead>
    <tbody>
        {% for client in clients %}
        <tr>
            <td>{{ client.id }}</td>
            <td>{{ client.full_name }}</td>
            <td>{{ client.phone }}</td>
            <td>{{ client.email }}</td>
            <td>{{ client.discount_percent }}%</td>
            <td>{{ client.total_spent }} ₽</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
''')

# client_form.html
with open('interfaces/templates/client_form.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<h1>{% if client %}Редактировать{% else %}Новый клиент{% endif %}</h1>
{% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
<form method="POST">
    <div class="mb-3"><label>ФИО</label><input type="text" name="full_name" class="form-control" required></div>
    <div class="mb-3"><label>Телефон</label><input type="text" name="phone" class="form-control" required></div>
    <div class="mb-3"><label>Email</label><input type="email" name="email" class="form-control" required></div>
    <div class="mb-3"><label>Дата рождения</label><input type="date" name="birthday" class="form-control"></div>
    <button type="submit" class="btn btn-success">Сохранить</button>
    <a href="{{ url_for('clients_list') }}" class="btn btn-secondary">Отмена</a>
</form>
{% endblock %}
''')

# orders.html
with open('interfaces/templates/orders.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-3">
    <h1>Заказы</h1>
    <a href="{{ url_for('order_create') }}" class="btn btn-primary">+ Новый заказ</a>
</div>
<table class="table table-striped">
    <thead>
        <tr><th>ID</th><th>Клиент</th><th>Фотограф</th><th>Статус</th><th>Сумма</th><th>Дата</th><th>Действия</th></tr>
    </thead>
    <tbody>
        {% for order in orders %}
        <tr>
            <td>{{ order.id }}</td>
            <td>{{ order.client_id }}</td>
            <td>{{ order.photographer_id or '-' }}</td>
            <td>
                <form method="POST" action="{{ url_for('order_update_status', order_id=order.id) }}" style="display:inline">
                    <select name="status" onchange="this.form.submit()" class="form-select form-select-sm" style="width:auto;display:inline-block">
                        <option value="new" {% if order.status.value == 'new' %}selected{% endif %}>Новый</option>
                        <option value="confirmed" {% if order.status.value == 'confirmed' %}selected{% endif %}>Подтверждён</option>
                        <option value="in_progress" {% if order.status.value == 'in_progress' %}selected{% endif %}>В работе</option>
                        <option value="ready" {% if order.status.value == 'ready' %}selected{% endif %}>Готов</option>
                        <option value="completed" {% if order.status.value == 'completed' %}selected{% endif %}>Выдан</option>
                        <option value="paid" {% if order.status.value == 'paid' %}selected{% endif %}>Оплачен</option>
                        <option value="cancelled" {% if order.status.value == 'cancelled' %}selected{% endif %}>Отменён</option>
                    </select>
                </form>
            </td>
            <td>{{ order.total_cost }} ₽</td>
            <td>{{ order.created_at.strftime('%d.%m.%Y') if order.created_at else '-' }}</td>
            <td>-</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
''')

# order_form.html
with open('interfaces/templates/order_form.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<h1>Новый заказ</h1>
{% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
<form method="POST">
    <div class="mb-3">
        <label>Клиент</label>
        <select name="client_id" class="form-control" required>
            <option value="">Выберите клиента</option>
            {% for client in clients %}
            <option value="{{ client.id }}">{{ client.full_name }} ({{ client.phone }})</option>
            {% endfor %}
        </select>
    </div>
    <div class="mb-3">
        <label>Фотограф</label>
        <select name="photographer_id" class="form-control">
            <option value="">Не выбран</option>
            <option value="2">Иванов Иван</option>
        </select>
    </div>
    <div class="mb-3">
        <label>Услуги</label>
        <div id="services-container">
            <div class="row mb-2">
                <div class="col"><select name="service_id[]" class="form-control">
                    <option value="">Выберите услугу</option>
                    {% for service in services %}
                    <option value="{{ service.id }}">{{ service.name }} - {{ service.price }} ₽/{{ service.unit }}</option>
                    {% endfor %}
                </select></div>
                <div class="col"><input type="number" name="quantity[]" class="form-control" placeholder="Кол-во" step="0.01"></div>
            </div>
        </div>
        <button type="button" class="btn btn-sm btn-secondary" onclick="addService()">+ Добавить услугу</button>
    </div>
    <div class="mb-3"><label>Срок (дедлайн)</label><input type="datetime-local" name="deadline" class="form-control"></div>
    <div class="mb-3"><label>Примечания</label><textarea name="notes" class="form-control" rows="3"></textarea></div>
    <button type="submit" class="btn btn-success">Создать заказ</button>
    <a href="{{ url_for('orders_list') }}" class="btn btn-secondary">Отмена</a>
</form>
<script>
function addService() {
    const container = document.getElementById('services-container');
    const div = document.createElement('div');
    div.className = 'row mb-2';
    div.innerHTML = '<div class="col"><select name="service_id[]" class="form-control">{% for service in services %}<option value="{{ service.id }}">{{ service.name }} - {{ service.price }} ₽/{{ service.unit }}</option>{% endfor %}</select></div><div class="col"><input type="number" name="quantity[]" class="form-control" placeholder="Кол-во" step="0.01"></div>';
    container.appendChild(div);
}
</script>
{% endblock %}
''')

# calendar.html
with open('interfaces/templates/calendar.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<h1>Расписание</h1>
<div class="alert alert-info">Календарь бронирования студии и фотографов (в разработке)</div>
{% endblock %}
''')

# reports.html
with open('interfaces/templates/reports.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<h1>Отчёты</h1>
<form method="GET" class="row g-3 mb-4">
    <div class="col-auto"><label>С</label><input type="date" name="start_date" value="{{ start_date }}" class="form-control"></div>
    <div class="col-auto"><label>По</label><input type="date" name="end_date" value="{{ end_date }}" class="form-control"></div>
    <div class="col-auto"><button type="submit" class="btn btn-primary mt-4">Показать</button></div>
</form>
<div class="row">
    <div class="col-md-6">
        <div class="card"><div class="card-header">Основные показатели</div>
        <div class="card-body">
            <p>Всего заказов: <strong>{{ report.total_orders }}</strong></p>
            <p>Выручка: <strong>{{ report.total_revenue }} ₽</strong></p>
            <p>Средний чек: <strong>{{ "%.2f"|format(report.avg_order_value) }} ₽</strong></p>
        </div></div>
    </div>
    <div class="col-md-6">
        <div class="card"><div class="card-header">Топ клиентов</div>
        <div class="card-body">
            <ul>{% for client in report.top_clients %}<li>{{ client.full_name }}: {{ client.total }} ₽</li>{% endfor %}</ul>
        </div></div>
    </div>
</div>
<div class="card mt-3"><div class="card-header">Статистика фотографов</div>
<div class="card-body">
    <table class="table"><thead><tr><th>Фотограф</th><th>Заказов</th><th>Выручка</th></tr></thead>
    <tbody>{% for stat in report.photographer_stats %}<tr><td>{{ stat.name }}</td><td>{{ stat.orders_count }}</td><td>{{ stat.revenue }} ₽</td></tr>{% endfor %}</tbody>
    </table>
</div></div>
{% endblock %}
''')

# users.html
with open('interfaces/templates/users.html', 'w', encoding='utf-8') as f:
    f.write('''{% extends "base.html" %}
{% block content %}
<h1>Пользователи</h1>
<table class="table table-striped">
    <thead><tr><th>ID</th><th>Логин</th><th>ФИО</th><th>Роль</th><th>Телефон</th><th>Email</th></tr></thead>
    <tbody>
        {% for u in users %}
        <tr><td>{{ u.id }}</td><td>{{ u.login }}</td><td>{{ u.full_name }}</td><td>{{ u.role.value }}</td><td>{{ u.phone }}</td><td>{{ u.email }}</td></tr>
        {% endfor %}
    </tbody>
</table>
{% endblock %}
''')

print("✅ Все файлы успешно созданы!")
print("Теперь запусти: python app.py")
print("Логин: admin, пароль: admin123")