from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
import os
from flask_login import LoginManager
from flask_oauthlib.client import OAuth
from . import credentials
from .credentials import DROPBOX_CONSUMER_KEY,DROPBOX_CONSUMER_SECRET
from flask_crontab import Crontab
from .cronjob import main_cron
db = SQLAlchemy()
DB_NAME = "database.db"
crontab = Crontab()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)
    crontab.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(str(id))

    oauth = OAuth(app)
    credentials.dropbox = oauth.remote_app(
    'dropbox',
    consumer_key=DROPBOX_CONSUMER_KEY,
    consumer_secret=DROPBOX_CONSUMER_SECRET,
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


    
@crontab.job(minute="2",hour="0")
def my_scheduled_job():   
    main_cron()

#  */2 * * * *