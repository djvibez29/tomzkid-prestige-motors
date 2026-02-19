from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import db, Order, OrderItem, Product

payments = Blueprint('payments', __name__)

@payments.route('/checkout/<int:product_id>')
@login_required
def checkout(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('checkout.html', product=product)


@payments.route('/create-order/<int:product_id>')
@login_required
def create_order(product_id):
    product = Product.query.get_or_404(product_id)

    order = Order(user_id=current_user.id, total_price=product.price)
    db.session.add(order)
    db.session.commit()

    item = OrderItem(order_id=order.id,
                     product_id=product.id,
                     quantity=1,
                     price=product.price)

    db.session.add(item)

    order.status = "paid"
    db.session.commit()

    return redirect(url_for('payments.my_orders'))


@payments.route('/my-orders')
@login_required
def my_orders():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('orders.html', orders=orders)
