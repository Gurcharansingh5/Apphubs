from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.String(150), primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    
    root_folder = db.Column(db.String(150))
    auto_launch = db.Column(db.Boolean,default=True)
    last_runned = db.Column(db.DateTime)
    time_delta = db.Column(db.Integer,default=0)

    social_details = db.relationship('SocialDetails')


class SocialDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    user_id = db.Column(db.String(150), db.ForeignKey('user.id'))

    type = db.Column(db.String(50))
    is_deleted = db.Column(db.Boolean,default=False)

    username = db.Column(db.String(50)) 
    email = db.Column(db.String(50))
    pic_url = db.Column(db.String(150))

    access_token = db.Column(db.String(256))

    last_logged_in = db.Column(db.DateTime(timezone=True))

