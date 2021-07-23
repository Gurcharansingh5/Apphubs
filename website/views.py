from flask import Blueprint, render_template, request, flash, jsonify,redirect,url_for,session
from flask_login import login_required, current_user
from .models import Note,User
from . import db
import json
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
from . import config
import dropbox


FB_CLIENT_ID=2256808184449973    
FB_CLIENT_SECRET="bc5fa70ff4ff8dd693f804ba4f0db80c"
FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
FB_SCOPE = ["email"]
URL = "https://e60817398c01.ngrok.io"

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')
    readyfolderpaths = findReadyFolderPaths()
    return render_template("home.html", user=current_user,paths=readyfolderpaths)


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
    print('current user')
    print(current_user.email)
    facebook = requests_oauthlib.OAuth2Session(
    	FB_CLIENT_ID, scope=FB_SCOPE, redirect_uri=URL + "/fb-callback"
	)

	# we need to apply a fix for Facebook here
    facebook = facebook_compliance_fix(facebook)
    token = facebook.fetch_token(FB_TOKEN_URL,
    	client_secret=FB_CLIENT_SECRET,
    	authorization_response=request.url,
	)
    print(token)
    user = User.query.filter_by(email=current_user.email).first()
    user.fb_access_token = token['access_token']
    db.session.commit()

    return redirect(url_for('views.home'))

@views.route('/dropboxlogin')
def dropboxlogin():

    print(url_for('views.dropbox_authorized'))
    return config.dropbox.authorize(callback='https://911ffec4b3b1.ngrok.io/login/authorized')
    
@views.route('/login/authorized')
def dropbox_authorized():
    resp = config.dropbox.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )
    print(resp)
    session['dropbox_token'] = (resp['access_token'], '')
    print(session['dropbox_token'])
    user = User.query.filter_by(email=current_user.email).first()
    user.dropbox_access_token = resp['access_token']
    db.session.commit()

    return redirect(url_for('views.home'))


# function for checking if Ready folder exists
def findReadyFolderPaths():
    user = User.query.filter_by(email=current_user.email).first()
    dbx = dropbox.Dropbox(user.dropbox_access_token)    
    print("[SUCCESS] dropbox account linked")
    ready_campaign_path = []
    for entry in dbx.files_list_folder('/superlucky/').entries:
        for subEntry in dbx.files_list_folder('/superlucky/'+entry.name).entries:
            if subEntry.name == 'READY':
                print(subEntry.name)
                for subsubEntry in dbx.files_list_folder('/superlucky/'+entry.name+'/'+subEntry.name).entries:
                    ready_campaign_path.append(subsubEntry.path_display) 
    print(ready_campaign_path)
    return ready_campaign_path
    
    
