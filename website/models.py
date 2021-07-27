from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.String(150), primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    fb_access_token = db.Column(db.String(150))
    dropbox_access_token = db.Column(db.String(150))

