from flask import Flask
from controller.sensor_controller import sensor_bp
# from db import db

app = Flask(__name__)
app.config.from_object("config")  # Load database config

# db.init_app(app)  # Initialize database

# Register Blueprints
app.register_blueprint(sensor_bp, url_prefix='/api/sensor')

if __name__ == '__main__':
    app.run(debug=True)
