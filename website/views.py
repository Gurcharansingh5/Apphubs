from flask import Blueprint, render_template, request, flash, jsonify,redirect
from flask_login import login_required, current_user
from .models import Note
from . import db
import json
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix


FB_CLIENT_ID=2256808184449973    
FB_CLIENT_SECRET="bc5fa70ff4ff8dd693f804ba4f0db80c"
FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
FB_SCOPE = ["email"]
URL = "https://45064934bf8a.ngrok.io"

views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    print('current user')
    print(current_user)
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

@views.route("/fb-login")
def fblogin():
	facebook = requests_oauthlib.OAuth2Session(FB_CLIENT_ID, redirect_uri=URL + "/fb-callback", scope=FB_SCOPE)
	authorization_url, _ = facebook.authorization_url(FB_AUTHORIZATION_BASE_URL)

	return redirect(authorization_url)

@views.route("/fb-callback")
def callback():
	facebook = requests_oauthlib.OAuth2Session(
    	FB_CLIENT_ID, scope=FB_SCOPE, redirect_uri=URL + "/fb-callback"
	)

	# we need to apply a fix for Facebook here
	facebook = facebook_compliance_fix(facebook)

	token = facebook.fetch_token(
    	FB_TOKEN_URL,
    	client_secret=FB_CLIENT_SECRET,
    	authorization_response=request.url,
	)

	print(token)

	# Fetch a protected resource, i.e. user profile, via Graph API

	facebook_user_data = facebook.get(
    	"https://graph.facebook.com/me?fields=id,name,email,picture{url}"
	).json()

	print('facebook_user_data')
	print(facebook_user_data)
	email = facebook_user_data["email"]
	name = facebook_user_data["name"]
	picture_url = facebook_user_data.get("picture", {}).get("data", {}).get("url")

	return f"""
	User information: <br>
	Name: {name} <br>
	Email: {email} <br>
	Avatar <img src="{picture_url}"> <br>
	<a href="/">Home</a>
	"""