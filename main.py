import sys
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QHBoxLayout
from sqlalchemy import create_engine, MetaData, Table, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Подключение к базе данных PostgreSQL
DATABASE_URL = "postgresql+psycopg2://postgres:123@localhost:5432/qwe"  # Замените на свои данные
engine = create_engine(DATABASE_URL)

# Создание сессии
Session = sessionmaker(bind=engine)
session = Session()

# Подключение к таблицам
metadata = MetaData()
metadata.reflect(bind=engine)

# Получение таблиц
cart_table = metadata.tables['cart']
service_table = metadata.tables['Service']
category_table = metadata.tables['category']

def get_cart_data():
    """Функция для получения всех заказов из таблицы Cart."""
    query = session.query(cart_table).all()
    return query

def plot_orders_by_service():
    """Функция для построения графика количества заказов по услугам."""
    try:
        # Получение данных о заказах
        carts = session.query(cart_table).all()

        if not carts:
            raise ValueError("Данные о заказах отсутствуют.")

        service_summary = {}  # Словарь для хранения итогов по услугам

        for cart in carts:
            # Получение услуги и категории по id
            service = session.query(service_table).filter_by(id=cart.product_id).first()
            if service is None:
                continue
            category = session.query(category_table).filter_by(id=service.category_id).first()

            # Формируем строку "Название услуги | Категория"
            service_name = f"{service.service_name} | {category.category_name}" if category else service.service_name
            quantity = cart.quantity
            total = service.price * quantity

            if service_name in service_summary:
                service_summary[service_name]['total_quantity'] += quantity
                service_summary[service_name]['total_price'] += total
            else:
                service_summary[service_name] = {
                    'total_quantity': quantity,
                    'total_price': total
                }

        services = list(service_summary.keys())
        total_prices = [info['total_price'] for info in service_summary.values()]
        total_quantity = sum(info['total_quantity'] for info in service_summary.values())
        overall_total_price = sum(info['total_price'] for info in service_summary.values())

        # Построение графика
        plt.figure(figsize=(18, 8))
        bars = plt.bar(services, total_quantity, color='skyblue')  # Используем количество заявок для высоты столбца
        plt.xlabel('Услуги')
        plt.ylabel('Количество заказов')
        plt.title('Количество заказов по услугам')

        # Добавляем общую стоимость и количество заявок для каждой услуги на график
        for bar, service in zip(bars, services):
            quantity = service_summary[service]['total_quantity']
            total_price = service_summary[service]['total_price']
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     f'{quantity}\n{total_price:.2f} руб.', ha='center', va='bottom')

        # Отображение общей информации о количестве и стоимости
        total_info = f"Общее количество заявок: {total_quantity}, Общая стоимость: {overall_total_price:.2f} руб."
        plt.figtext(0.99, 0.01, total_info, horizontalalignment='right')

        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Ошибка при построении графика: {e}")
        raise

class ReportApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Отчеты по заказам')
        self.setGeometry(100, 100, 800, 600)

        # Кнопка для построения графика
        self.button = QPushButton('Построить график', self)
        self.button.clicked.connect(self.plot_graph)

        # Увеличиваем размер кнопки
        self.button.setFixedSize(200, 50)  # Размер кнопки: ширина 200, высота 50

        # Основной layout
        layout = QVBoxLayout()
        layout.addWidget(self.button)

        # Установка кнопки в левый верхний угол
        layout.setContentsMargins(10, 10, 0, 0)  # Устанавливаем отступы для кнопки

        # Главный виджет
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def plot_graph(self):
        try:
            # Вызов функции для построения графика
            plot_orders_by_service()
        except Exception as e:
            # Вывод ошибки в диалоговом окне
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText(f"Произошла ошибка: {str(e)}")
            error_dialog.setWindowTitle("Ошибка")
            error_dialog.exec_()


def plot_orders_by_week():
    """Функция для построения графика заказов по неделям."""
    try:
        carts = session.query(cart_table).all()

        if not carts:
            raise ValueError("Данные о заказах отсутствуют.")

        weekly_summary = {}

        for cart in carts:
            created_date = cart.created_timestamp.date()
            week_start = created_date - timedelta(days=created_date.weekday())

            service = session.query(service_table).filter_by(id=cart.product_id).first()
            if service is None:
                continue
            total_price = service.price * cart.quantity

            if week_start in weekly_summary:
                weekly_summary[week_start]['total_quantity'] += cart.quantity
                weekly_summary[week_start]['total_price'] += total_price
            else:
                weekly_summary[week_start] = {
                    'total_quantity': cart.quantity,
                    'total_price': total_price
                }

        weeks = sorted(weekly_summary.keys())
        total_quantities = [weekly_summary[week]['total_quantity'] for week in weeks]
        total_prices = [weekly_summary[week]['total_price'] for week in weeks]

        fig, ax1 = plt.subplots(figsize=(18, 8))

        ax1.set_xlabel('Неделя')
        ax1.set_ylabel('Количество заказов', color='tab:blue')
        bars = ax1.bar(weeks, total_quantities, color='tab:blue', alpha=0.6)
        ax1.tick_params(axis='y', labelcolor='tab:blue')

        ax2 = ax1.twinx()
        ax2.set_ylabel('Общая сумма', color='tab:red')
        ax2.plot(weeks, total_prices, color='tab:red', marker='o')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()

        for bar, total, quantity in zip(bars, total_prices, total_quantities):
            ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     f'{quantity} шт.\n{total:.2f} руб.', ha='center', va='bottom')

        footer_text = "\n".join([f"{week.strftime('%Y-%m-%d')}: {quantity} заказов, {total:.2f} руб."
                                 for week, quantity, total in zip(weeks, total_quantities, total_prices)])
        plt.figtext(0.5, -0.15, footer_text, ha='center', fontsize=10, wrap=True)

        plt.title('Количество и сумма заказов по неделям')
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f"Ошибка при построении графика: {e}")
        raise

class ReportApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Отчеты по заказам')
        self.setGeometry(100, 100, 800, 600)

        # Кнопка для построения графика заказов по услугам
        self.service_button = QPushButton('Построить график по услугам', self)
        self.service_button.clicked.connect(self.plot_graph_by_service)
        self.service_button.setFixedSize(200, 50)

        # Кнопка для построения графика заказов по неделям
        self.weekly_button = QPushButton('Построить график по неделям', self)
        self.weekly_button.clicked.connect(self.plot_graph_by_week)
        self.weekly_button.setFixedSize(200, 50)

        # Layout для кнопок
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.service_button)
        button_layout.addWidget(self.weekly_button)

        # Основной layout
        layout = QVBoxLayout()
        layout.addLayout(button_layout)

        # Установка кнопок в левый верхний угол
        layout.setContentsMargins(10, 10, 0, 0)

        # Главный виджет
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def plot_graph_by_service(self):
        try:
            plot_orders_by_service()
        except Exception as e:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText(f"Произошла ошибка: {str(e)}")
            error_dialog.setWindowTitle("Ошибка")
            error_dialog.exec_()

    def plot_graph_by_week(self):
        try:
            plot_orders_by_week()
        except Exception as e:
            error_dialog = QMessageBox()
            error_dialog.setIcon(QMessageBox.Critical)
            error_dialog.setText(f"Произошла ошибка: {str(e)}")
            error_dialog.setWindowTitle("Ошибка")
            error_dialog.exec_()

# Запуск приложения
def main():
    app = QApplication(sys.argv)
    main_window = ReportApp()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
