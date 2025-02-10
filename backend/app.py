from flask import Flask
from backend.controller.flower_controller import flower_bp
# from db import db

app = Flask(__name__)
app.config.from_object("config")  # Load database config

# db.init_app(app)  # Initialize database

# Register Blueprints
app.register_blueprint(flower_bp, url_prefix='/api/flower')

if __name__ == '__main__':
    app.run(debug=True)
