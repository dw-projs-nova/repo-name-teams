from flask import Blueprint, render_template, request, redirect, url_for
from models import db, Review

main = Blueprint('main', __name__)

@main.route('/')
def index():
    reviews = Review.query.all()
    return render_template('index.html', reviews=reviews)


@main.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        if rating is None or not 1 <= rating <= 5:
            return render_template(
                'add.html',
                error='Rating must be a whole number from 1 to 5.',
            ), 400
        content = request.form.get('content', type=str)
        if content is None or len(content) > 1000:
            return render_template(
                'add.html',
                error='Content must be a string with a maximum length of 1000 characters.',
            ), 400

        new_review = Review(
            reviewer_name=request.form['reviewer_name'],
            title=request.form['title'],
            content=request.form['content'],
            rating=rating,
        )
        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('add.html')
