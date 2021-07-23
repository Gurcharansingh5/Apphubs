from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_oauthlib.client import OAuth
from . import config
db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Note

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(str(id))

    oauth = OAuth(app)
    config.dropbox = oauth.remote_app(
    'dropbox',
    consumer_key='j3x8xr8e9aqg1gb',
    consumer_secret='kn7mpqs64v0ac8y',
    request_token_params={},
    base_url='https://www.dropbox.com/1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://api.dropbox.com/1/oauth2/token',
    authorize_url='https://www.dropbox.com/1/oauth2/authorize',
    ) 

    return app


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')


    
 