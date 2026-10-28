from flask import Flask
from config import Config
from dotenv import load_dotenv
from models import db
from controllers import main

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# Initializes the app
db.init_app(app)
app.register_blueprint(main)

with app.app_context():
    db.create_all()
    print("Database created at:", app.config['SQLALCHEMY_DATABASE_URI'])

if __name__ == '__main__':
    app.run(debug=True)