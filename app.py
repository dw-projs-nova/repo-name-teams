from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from config import Config
from sqlalchemy import inspect, text
from models import db, Review, User
from controllers import main

app = Flask(__name__)
app.config.from_object(Config)

# Initializes the app
db.init_app(app)
app.register_blueprint(main)

with app.app_context():
    db.create_all()

    columns = {column['name'] for column in inspect(db.engine).get_columns('reviews')}
    if 'product_id' not in columns:
        db.session.execute(text(
            "ALTER TABLE reviews ADD COLUMN product_id VARCHAR(40) NOT NULL DEFAULT 'aurora'"
        ))
        db.session.commit()

    columns = {column['name'] for column in inspect(db.engine).get_columns('reviews')}
    if 'user_id' not in columns:
        db.session.execute(text("ALTER TABLE reviews ADD COLUMN user_id INTEGER"))
        db.session.commit()

    columns = {column['name'] for column in inspect(db.engine).get_columns('reviews')}
    if 'approved' not in columns:
        db.session.execute(text(
            "ALTER TABLE reviews ADD COLUMN approved BOOLEAN NOT NULL DEFAULT 1"
        ))
        db.session.commit()

    db.session.execute(text(
        "UPDATE reviews SET product_id = 'cloudstep' WHERE product_id = 'aurora'"
    ))
    db.session.execute(text(
        "UPDATE reviews SET product_id = 'trailbound' WHERE product_id = 'nova'"
    ))

    db.session.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_review_user_product "
        "ON reviews(user_id, product_id) WHERE user_id IS NOT NULL"
    ))

    examples = {
        'cloudstep': [
            ('Maya Chen', 'Comfortable from the first mile', 'Cloudstep shoes have soft cushioning and feel light on long neighborhood runs.', 5),
            ('Jordan Lee', 'Great for everyday runs', 'The support feels balanced and the flexible sole is comfortable without being too squishy.', 4),
        ],
        'trailbound': [
            ('Priya Shah', 'Ready for rocky trails', 'The Trailbound boots have strong grip and kept my feet dry on a muddy weekend hike.', 5),
            ('Alex Morgan', 'Secure and supportive', 'These feel sturdy on uneven ground, with enough padding for a full day outside.', 4),
        ],
    }
    for product_id, product_examples in examples.items():
        existing_titles = {
            title
            for (title,) in db.session.query(Review.title)
            .filter_by(product_id=product_id)
            .all()
        }
        db.session.add_all([
            Review(
                product_id=product_id,
                reviewer_name=reviewer_name,
                title=title,
                content=content,
                rating=rating,
            )
            for reviewer_name, title, content, rating in product_examples
            if title not in existing_titles
        ])
    db.session.commit()
    print("Database created at:", app.config['SQLALCHEMY_DATABASE_URI'])

if __name__ == '__main__':
    app.run(debug=True)