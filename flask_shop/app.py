from flask import Flask, request, jsonify
from datetime import timedelta
import jwt as j
from flask_jwt_extended import JWTManager, create_access_token, set_access_cookies, unset_jwt_cookies
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy

flask_app = Flask(__name__)
flask_app.config['SECRET_KEY'] = 'secret_app_key'
flask_app.config['JWT_SECRET_KEY'] = 'secret_key'
flask_app.config['JWT_TOKEN_LOCATION'] = ['cookies']
flask_app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)
flask_app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
flask_app.config["JWT_HEADER_TYPE"] = "JWT"

jwt = JWTManager(flask_app)

flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root: ... @localhost/webshopdb'
db = SQLAlchemy(flask_app)

from models import User, Products, Order


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token_cookie')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            secret_key = flask_app.config['JWT_SECRET_KEY']
            payload = j.decode(token, secret_key, algorithms=['HS256'])
            user_info = {
                'id': payload.get('sub'),
            }
            current_user = User.query.filter_by(id=user_info['id']).first()

            if current_user and current_user.is_active:
                return f(*args, **kwargs)
            else:
                return jsonify({'message': 'No such user.'})
        except:
            response = jsonify({"msg": "Token expired, login again."})
            unset_jwt_cookies(response)
            return response

    return decorated


def admin_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token_cookie')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            secret_key = flask_app.config['JWT_SECRET_KEY']
            payload = j.decode(token, secret_key, algorithms=['HS256'])
            user_info = {
                'id': payload.get('sub'),
            }
            current_user = User.query.filter_by(id=user_info['id']).first()

            if current_user and current_user.is_admin:
                return f(*args, **kwargs)
        except:
            response = jsonify({"msg": "Token expired, login again."})
            unset_jwt_cookies(response)
            return response

    return decorated


def staff_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token_cookie')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            secret_key = flask_app.config['JWT_SECRET_KEY']
            payload = j.decode(token, secret_key, algorithms=['HS256'])
            user_info = {
                'id': payload.get('sub'),
            }
            current_user = User.query.filter_by(id=user_info['id']).first()

            if current_user and current_user.is_staff:
                return f(*args, **kwargs)
        except:
            response = jsonify({"msg": "Token expired, login again."})
            unset_jwt_cookies(response)
            return response

    return decorated


@flask_app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        address = request.form.get('address')
        mobile = request.form.get('mobile')

        if not username or not password or not email or not address or not mobile:
            return jsonify({'message': 'Fill all the fields.'})
        if password != password2:
            return jsonify({'message': 'Password mismatch.'})

        hashed_password = generate_password_hash(password, method='sha256')

        user = User()
        new_user = user.add_user(user_name=username, email=email, password=hashed_password, address=address,
                                 mobile=mobile)

        return jsonify({'user': new_user})


@flask_app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(user_name=username).first()

            if user:
                if check_password_hash(user.password, password):
                    response = jsonify({"msg": "login successful"})
                    access_token = create_access_token(identity=user.id)
                    set_access_cookies(response, access_token)
                    return response
                else:
                    return jsonify({'error': 'Invalid password'}), 401
            else:
                return jsonify({'error': 'User does not exist'}), 404

        except Exception as e:
            return jsonify({'error': str(e)}), 500


@flask_app.route('/logout', methods=['POST'])
def logout():
    if request.method == 'POST':
        response = jsonify({"msg": "logout successful"})
        unset_jwt_cookies(response)
        return response


@flask_app.route("/users", methods=["GET"])
@token_required
def get_all_users():
    users = User()
    users_data = users.get_users()
    return jsonify({'users': users_data})


@flask_app.route("/users/<id>", methods=['GET', 'POST'])
@admin_user
def manage_staff(id):
    u = User()

    if request.method == 'GET':
        user_data = u.get_user_by_id(id)
        return jsonify({'user': user_data})

    if request.method == 'POST':
        user_data = u.manage_user(id)
        return jsonify({'success': 'User updated successfully.', 'user': user_data})


@flask_app.route('/add_product', methods=['POST'])
@staff_user
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock_quantity = request.form.get('quantity')

        if not name or not description or not stock_quantity or not price:
            return jsonify({'message': 'Fill all the fields.'})

        p = Products()
        new_product = p.add_product(name=name, description=description, stock_quantity=stock_quantity, price=price)

        return jsonify({'product': new_product})


@flask_app.route('/products', methods=['GET'])
@token_required
def products():
    p = Products()
    all_products = p.get_products()
    return jsonify({'products': all_products})


@flask_app.route('/order/<product>', methods=['POST'])
@token_required
def order(product):
    if request.method == 'POST':
        u = User()
        user_id = u.get_logged_in_user_id()
        quantity = request.form.get('quantity')
        product_id = product

        p = Products()
        manage_order = p.manage_order(user_id, product_id, quantity)

        if manage_order:
            o = Order()
            order_data = o.get_user_orders(user_id)
            return jsonify({'order': order_data})
        else:
            return jsonify({'order': 'Order error.'})


@flask_app.route('/pending_orders', methods=['GET', 'PUT'])
@staff_user
def pending_orders():
    o = Order()

    if request.method == 'GET':
        p_orders = o.get_pending_orders()
        return jsonify({'pending_orders': p_orders})

    if request.method == 'PUT':
        order_id = request.form.get('order_id')
        updated_orders = o.update_order_status(p_order_id=order_id)
        return jsonify({'updated_orders': updated_orders})


if __name__ == '__main__':
    flask_app.run(debug=True)
