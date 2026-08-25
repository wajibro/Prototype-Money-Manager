import os
import importlib
from flask import Flask
from flask_session import Session
from supabase import create_client, Client
from app.config import Config

supabase = create_client(Config.DB_URL, Config.DB_KEY)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=86400,
    )

    routes_dir = os.path.join(os.path.dirname(__file__), 'routes')

    for filename in os.listdir(routes_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3] 
            module = importlib.import_module(f'app.routes.{module_name}')
            blueprint_object_name = f"{module_name}_bp"
            
            if hasattr(module, blueprint_object_name):
                blueprint = getattr(module, blueprint_object_name)
                app.register_blueprint(blueprint)

    return app