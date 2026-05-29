from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from datetime import datetime
import hashlib
from infrastructure.models import ScheduleSlotModel

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
from domain.entities import User, Service, ScheduleSlot

import smtplib
from email.message import EmailMessage

app = Flask(__name__, template_folder='templates')
app.config.from_object(Config)

db = Database(app.config['DATABASE_URL'])
db.create_tables()

def send_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = 'studio@photostudio.ru'
        msg['To'] = to_email

        # Для демо — просто выводим в консоль
        print(f"📧 Email to {to_email}: {subject} - {body[:50]}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


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
        client_repo = SQLAlchemyClientRepository(sess)
        use_case = UpdateOrderStatusUseCase(repo, client_repo, uow)
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
    return redirect(url_for('calendar_full'))

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


@app.route('/calendar-full')
@login_required()
def calendar_full():
    user = get_current_user()
    return render_template('calendar_full.html', user=user)


@app.route('/api/slots')
def api_get_slots():
    from domain.value_objects import OrderStatus
    with db.get_session() as sess:
        schedule_repo = SQLAlchemyScheduleRepository(sess)
        order_repo = SQLAlchemyOrderRepository(sess)
        all_slots = []
        photographers = [2]  # ID фотографа
        for p_id in photographers:
            for date in ['2026-05-29', '2026-05-30', '2026-05-31', '2026-06-01', '2026-06-02', '2026-06-03',
                         '2026-06-04', '2026-06-05']:
                slots = schedule_repo.get_slots_by_photographer(p_id, date)
                for slot in slots:
                    if slot.is_booked:
                        all_slots.append({
                            'title': f'Занято (фотограф {p_id})',
                            'start': f"{slot.date}T{slot.time_slot}:00",
                            'color': 'red'
                        })
        return jsonify(all_slots)


@app.route('/api/book-slot', methods=['POST'])
def api_book_slot():
    data = request.get_json()
    photographer_id = int(data['photographer_id'])
    date = data['date']
    time_slot = data['time_slot']
    order_id = int(data['order_id'])

    with db.get_session() as sess:
        schedule_repo = SQLAlchemyScheduleRepository(sess)
        uow = SQLAlchemyUnitOfWork(lambda: sess)

        # Проверяем, есть ли уже такой слот
        existing = sess.query(ScheduleSlotModel).filter(
            ScheduleSlotModel.photographer_id == photographer_id,
            ScheduleSlotModel.date == date,
            ScheduleSlotModel.time_slot == time_slot
        ).first()

        if existing and existing.is_booked:
            return jsonify({'error': 'Слот уже занят!'}), 400

        if not existing:
            # Создаём слот
            new_slot = ScheduleSlot(
                id=None, photographer_id=photographer_id, date=date,
                time_slot=time_slot, is_booked=True, order_id=order_id
            )
            schedule_repo.create_slots([new_slot])
        else:
            # Бронируем существующий
            schedule_repo.book_slot(existing.id, order_id)

        sess.commit()
        return jsonify({'message': f'Слот {date} {time_slot} забронирован!'})

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
    app.run(debug=True, host='0.0.0.0', port=5000)
