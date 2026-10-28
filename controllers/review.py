from flask import abort, g, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError

from controllers.shared import can_edit, get_product, main, require_login
from models import Review, db


@main.route('/')
def index():
    return redirect(url_for('main.product', product_id='cloudstep'))


@main.route('/products/<product_id>')
def product(product_id):
    product = get_product(product_id)
    reviews = Review.query.filter_by(product_id=product_id, approved=True).order_by(Review.created_at.desc()).all()
    review_count = len(reviews)
    review_average = round(sum(review.rating for review in reviews) / review_count, 1) if review_count else None
    return render_template(
        'index.html',
        product_id=product_id,
        product=product,
        reviews=reviews,
        review_count=review_count,
        review_average=review_average,
    )


@main.route('/reviews/add/<product_id>', methods=['GET', 'POST'])
def add(product_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect
    product = get_product(product_id)
    existing_review = Review.query.filter_by(product_id=product_id, user_id=g.current_user.id).first()
    if existing_review is not None:
        return redirect(url_for('main.edit_review', review_id=existing_review.id))

    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or len(title) > 200:
            return render_template('add.html', product_id=product_id, product=product,
                                   error='Title is required and must be 200 characters or fewer.'), 400
        if rating is None or not 1 <= rating <= 5:
            return render_template('add.html', product_id=product_id, product=product,
                                   error='Rating must be a whole number from 1 to 5.'), 400
        if not content or len(content) > 1000:
            return render_template('add.html', product_id=product_id, product=product,
                                   error='Content is required and must be 1000 characters or fewer.'), 400

        new_review = Review(
            user_id=g.current_user.id,
            product_id=product_id,
            reviewer_name=g.current_user.display_name,
            title=title,
            content=content,
            rating=rating,
            approved=False,
        )
        db.session.add(new_review)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            existing_review = Review.query.filter_by(
                product_id=product_id,
                user_id=g.current_user.id,
            ).one()
            return redirect(url_for('main.edit_review', review_id=existing_review.id))
        return render_template('review_submitted.html', product_id=product_id, product=product)
    return render_template('add.html', product_id=product_id, product=product)


@main.route('/reviews/<int:review_id>/edit', methods=['GET', 'POST'])
def edit_review(review_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    review = db.session.get(Review, review_id)
    if review is None:
        abort(404)
    if not can_edit(review):
        abort(403)

    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or len(title) > 200:
            return render_template('edit.html', review=review,
                                   error='Title is required and must be 200 characters or fewer.'), 400
        if rating is None or not 1 <= rating <= 5:
            return render_template('edit.html', review=review,
                                   error='Rating must be a whole number from 1 to 5.'), 400
        if not content or len(content) > 1000:
            return render_template('edit.html', review=review,
                                   error='Content is required and must be 1000 characters or fewer.'), 400

        review.title = title
        review.content = content
        review.rating = rating
        db.session.commit()
        return redirect(url_for('main.product', product_id=review.product_id))

    return render_template('edit.html', review=review)


@main.route('/reviews/<int:review_id>/delete', methods=['POST'])
def delete_review(review_id):
    login_redirect = require_login()
    if login_redirect:
        return login_redirect

    review = db.session.get(Review, review_id)
    if review is None:
        abort(404)
    if not can_edit(review):
        abort(403)

    db.session.delete(review)
    db.session.commit()

    if g.current_user.role == 'admin' and request.args.get('next') == 'admin':
        return redirect(url_for('main.admin_reviews'))
    return redirect(url_for('main.account'))
