from datetime import datetime
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

            try:
                from app import send_email
                client_email = client.email
                send_email(client_email, "Заказ создан",
                           f"Ваш заказ #{created.id} на сумму {created.total_cost} руб. принят.")
            except:
                pass

            self.uow.commit()
            return created


class UpdateOrderStatusUseCase:
    def __init__(self, order_repo: OrderRepository, client_repo: ClientRepository, uow: UnitOfWork):
        self.order_repo = order_repo
        self.client_repo = client_repo
        self.uow = uow

    def execute(self, order_id: int, new_status: OrderStatus) -> Order:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        with self.uow:
            updated = self.order_repo.update_status(order_id, new_status)

            # Пересчитываем total_spent клиента
            client = self.client_repo.get_by_id(order.client_id)
            if client:
                all_orders = self.order_repo.get_by_client(client.id)
                total_paid = sum(o.total_cost for o in all_orders if o.status == OrderStatus.PAID)
                client.total_spent = total_paid
                self.client_repo.update(client)
                print(f"💰 Client {client.full_name} total_spent updated to {client.total_spent}")

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
