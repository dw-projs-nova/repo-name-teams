from flask import abort, render_template, request

from controllers_mail import send_review_approved_email
from controllers_shared import main, require_admin
from models import Review, db


@main.route('/admin/reviews', methods=['GET', 'POST'])
def admin_reviews():
    access_error = require_admin()
    if access_error:
        return access_error

    message = None
    if request.method == 'POST':
        review_id = request.form.get('review_id', type=int)
        action = request.form.get('action')
        review = db.session.get(Review, review_id) if review_id else None
        if review is None or action not in {'approve', 'reject', 'delete'}:
            abort(400)

        if action == 'delete':
            db.session.delete(review)
            message = 'Review deleted.'
        else:
            was_approved = review.approved
            review.approved = action == 'approve'
            message = 'Review approved.' if review.approved else 'Review rejected.'
            if review.approved and not was_approved:
                send_review_approved_email(review)
        db.session.commit()

    status = request.args.get('status', 'pending')
    query = Review.query
    if status == 'approved':
        query = query.filter_by(approved=True)
    elif status == 'rejected':
        query = query.filter_by(approved=False)
    elif status == 'all':
        pass
    else:
        status = 'pending'
        query = query.filter_by(approved=False)

    reviews = query.order_by(Review.created_at.desc()).all()
    counts = {
        'pending': Review.query.filter_by(approved=False).count(),
        'approved': Review.query.filter_by(approved=True).count(),
        'all': Review.query.count(),
    }
    return render_template(
        'admin/reviews.html',
        reviews=reviews,
        status=status,
        counts=counts,
        message=message,
    )
