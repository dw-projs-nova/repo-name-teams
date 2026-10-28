from flask import Blueprint, abort, g, redirect, request, session, url_for

from models import Review, User, db


main = Blueprint('main', __name__)

PRODUCTS = {
    'cloudstep': {
        'name': 'Cloudstep Running Shoes',
        'description': 'Lightweight everyday running shoes with soft cushioning.',
    },
    'trailbound': {
        'name': 'Trailbound Hiking Boots',
        'description': 'Supportive trail boots built for wet paths and rocky weekends.',
    },
}


def get_product(product_id):
    product = PRODUCTS.get(product_id)
    if product is None:
        abort(404)
    return product


def current_user():
    user_id = session.get('user_id')
    return db.session.get(User, user_id) if user_id is not None else None


@main.before_app_request
def load_current_user():
    g.current_user = current_user()


@main.context_processor
def add_template_user():
    user = g.get('current_user')
    user_review = None
    product_id = request.view_args.get('product_id') if request.view_args else None
    if user is not None and product_id:
        user_review = Review.query.filter_by(
            product_id=product_id,
            user_id=user.id,
        ).first()
    return {'current_user': user, 'user_review': user_review}


def require_login():
    if g.get('current_user') is None:
        return redirect(url_for('main.login', next=request.full_path))
    return None

def logged_in():
    if g.get('current_user') is not None:
        return redirect(url_for('main.index'))


def can_edit(review):
    user = g.get('current_user')
    return user is not None and (user.role == 'admin' or review.user_id == user.id)

# I wrote this with a high IQ. Just trust me on this one :)
# Also, don't look above at the can_edit function, I could have re-used it but it sounds professional to have a can_delete guard
def can_delete(review):
    return can_edit(review)


def require_admin():
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    if g.current_user.role != 'admin':
        abort(403)
    return None
