from app import db
import pymysql
from flask import request, jsonify
from datetime import datetime
import jwt as j

connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            db='webshopdb',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(300))
    address = db.Column(db.String(80))
    mobile = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean)
    is_staff = db.Column(db.Boolean)
    is_active = db.Column(db.Boolean)

    def get_users(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                        SELECT *
                        FROM users
                        """)
            result = cursor.fetchall()
            return result

    def add_user(self, user_name, email, password, address, mobile):
        with connection.cursor() as cursor:
            cursor.callproc("add_user",
                           [user_name, email, password, address, mobile])
            result = cursor.fetchall()
            connection.commit()
            return result

    def get_user_by_id(self, id):
        with connection.cursor() as cursor:
            cursor.callproc("get_user", [id])
            result = cursor.fetchall()
            return result

    def get_logged_in_user_id(self):
        token = request.cookies.get('access_token_cookie')
        if not token:
            return jsonify({'message': 'Not logged in.'}), 401

        from app import flask_app
        secret_key = flask_app.config['JWT_SECRET_KEY']
        payload = j.decode(token, secret_key, algorithms=['HS256'])
        user_info = {
            'id': payload.get('sub'),
        }
        return user_info['id']


    def manage_user(self, id):
        with connection.cursor() as cursor:
            cursor.callproc("manage_user", [id])
            result = cursor.fetchall()
            connection.commit()
            return result

class Products(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    description = db.Column(db.String(300))
    price = db.Column(db.Float)
    stock_quantity = db.Column(db.Integer)
    is_available = db.Column(db.Boolean)

    def add_product(self, name, description, price, stock_quantity):
        with connection.cursor() as cursor:
            cursor.callproc("add_product",
                           [name, description, price, stock_quantity])
            result = cursor.fetchall()
            connection.commit()
            return result

    def get_products(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                        SELECT *
                        FROM products
                        """)
            result = cursor.fetchall()
            return result

    def manage_order(self, user_id, product_id, quantity):
        try:
            with connection.cursor() as cursor:
                cursor.callproc('manage_order', [user_id, product_id, quantity])
                connection.commit()
                return True
        except:
            return False

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))

    def get_user_orders(self, user_id):
        with connection.cursor() as cursor:
            cursor.callproc('get_user_orders', [user_id])
            result = cursor.fetchall()
            return result

    def get_pending_orders(self):
        with connection.cursor() as cursor:
            cursor.execute("""
                        SELECT *
                        FROM orders
                        WHERE status = 'Pending'
                        """)
            result = cursor.fetchall()
            return result

    def update_order_status(self, p_order_id):
        with connection.cursor() as cursor:
            cursor.execute('update_order_status', [p_order_id])
            result = cursor.fetchall()
            connection.commit()
            return result

class OrderDetails(db.Model):
    __tablename__ = 'order_details'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    quantity = db.Column(db.Integer)
    total_amount = db.Column(db.Float)
