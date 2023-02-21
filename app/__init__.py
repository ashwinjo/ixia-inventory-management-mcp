from flask import Flask

def create_app():
    """Initialize the flask app instance
    """
    app = Flask(__name__)
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    return app