# INNER IMPORTS
from .models import User,SocialDetails
from . import db
from . credentials import GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET,GOOGLE_DISCOVERY_URL
from website.credentials import FB_AUTHORIZATION_BASE_URL,FB_CLIENT_ID,FB_CLIENT_SECRET,FB_SCOPE,FB_TOKEN_URL,URL
from . import credentials

# INTERNAL IMPORTS
import requests,json
import os
from datetime import datetime
from dateutil import tz

# EXTERNAL IMPORTS
from flask import Blueprint, render_template, request, redirect, url_for, session,flash
from flask_login import login_user, login_required, logout_user, current_user
from oauthlib.oauth2 import WebApplicationClient
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix


os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
client = WebApplicationClient(GOOGLE_CLIENT_ID)
auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route("/loginurl")
def googleLoginURL():
    
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@auth.route("/loginurl/callback")
def googleCallback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400


    user = User.query.filter_by(email=users_email).first()
    if not user:
        password1 = unique_id
        new_user = User(id=unique_id,email=users_email, first_name= users_name, password=password1)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
    else:
    # # Begin user session by logging the user in
        login_user(user, remember=True)

    # Send user back to homepage
    return redirect(url_for('views.home'))


@auth.route("/fb-login")
def facebookLoginURL():
	facebook = requests_oauthlib.OAuth2Session(FB_CLIENT_ID, redirect_uri=URL + "/fb-callback", scope=FB_SCOPE)
	authorization_url, _ = facebook.authorization_url(FB_AUTHORIZATION_BASE_URL)

	return redirect(authorization_url)

@auth.route("/fb-callback")
def facebookCallback():
    facebook = requests_oauthlib.OAuth2Session(
    	FB_CLIENT_ID, scope=FB_SCOPE, redirect_uri=URL + "/fb-callback"
	)

	# we need to apply a fix for Facebook here
    facebook = facebook_compliance_fix(facebook)
    token = facebook.fetch_token(FB_TOKEN_URL, client_secret=FB_CLIENT_SECRET, authorization_response=request.url)
    print("asdssdsafsdafdafsdfsdf")
    print(token)
    # Fetch a protected resource, i.e. user profile, via Graph API
    facebook_user_data = facebook.get("https://graph.facebook.com/me?fields=id,name,email,picture{url}").json()
    
    if not 'email' in facebook_user_data:
        flash('Please Login with a valid Facebook Ad Account.', category='error') 

    else:
        # get current time
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()
        utc = datetime.utcnow()
        utc = utc.replace(tzinfo=from_zone)
        central = utc.astimezone(to_zone)

        new_social_user = SocialDetails(user_id = current_user.id,
                                type = 'facebook',
                                email = facebook_user_data["email"],
                                username = facebook_user_data["name"],
                                pic_url = facebook_user_data.get("picture", {}).get("data", {}).get("url"),
                                access_token = token['access_token'],
                                last_logged_in = central
                                )
        db.session.add(new_social_user)
        db.session.commit()

    return redirect(url_for('views.home'))

@auth.route('/dropboxlogin')
def dropboxLoginURL():
    return credentials.dropbox.authorize(callback=URL+'/login/authorized')
    
@auth.route('/login/authorized')
def dropboxCallback():
    resp = credentials.dropbox.authorized_response()
    print('^&^&^&^&^&^&^&^&^&^&^&^&^&')
    print(resp)
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error'],
            request.args['error_description']
        )
    dropbox_access_token = resp['access_token']
    session['dropbox_token'] = (resp['access_token'], '')

    # Fetch a protected resource, i.e. user profile
    dropbox_user_data = requests.post('https://api.dropboxapi.com/2/users/get_current_account', headers={"Authorization": f"Bearer {dropbox_access_token}"}).json()

    # get current time
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = datetime.utcnow()
    utc = utc.replace(tzinfo=from_zone)
    central = utc.astimezone(to_zone)
    
    new_social_user = SocialDetails(user_id = current_user.id,
                        type = 'dropbox',
                        email = dropbox_user_data["email"],
                        username = dropbox_user_data['name']['display_name'],
                        pic_url = dropbox_user_data.get('profile_photo_url','https://image.flaticon.com/icons/png/512/149/149071.png'),
                        access_token = dropbox_access_token,
                        last_logged_in = central.replace(microsecond=0)
                        )
    db.session.add(new_social_user)
    db.session.commit()

    return redirect(url_for('views.home'))