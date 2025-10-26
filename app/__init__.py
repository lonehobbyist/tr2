from flask import Flask
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_app():
    logging.info("Creating Flask application.")
    app = Flask(__name__)
    app.secret_key = 'supersecretkey'

    from . import routes
    app.register_blueprint(routes.bp)

    return app
