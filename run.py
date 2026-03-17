import os
from app import create_app
from app.extensions import db

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
