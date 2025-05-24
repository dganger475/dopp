# extensions.py
"""
Central place to initialize Flask extensions for the DoppleGänger app.
"""
from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_talisman import Talisman
from flask_login import LoginManager
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

cache = Cache()
# Initialize CORS with specific settings before init_app
# Assuming React frontend runs on http://localhost:5173
cors = CORS(supports_credentials=True, origins=["http://localhost:5173"])
limiter = Limiter(key_func=get_remote_address)
session = Session()
talisman = Talisman()
login_manager = LoginManager()
moment = Moment()
db = SQLAlchemy()

def init_extensions(app):
    cache.init_app(app)
    # CORS is already initialized with app-independent settings, 
    # init_app here just registers it with the app instance.
    cors.init_app(app)
    limiter.init_app(app)
    session.init_app(app)
    talisman.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    return app
