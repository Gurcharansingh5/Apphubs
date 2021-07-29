# INNER IMPORTS
import re
from . credentials import FB_AUTHORIZATION_BASE_URL,FB_CLIENT_ID,FB_CLIENT_SECRET,FB_SCOPE,FB_TOKEN_URL,URL
from . import credentials
from .models import User
from . import db

# INTERNAL IMPORTS
import os
import requests

# external imports
from flask import Blueprint, render_template, request,redirect,url_for,session
from flask_login import login_required, current_user
import dropbox
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():

    print(credentials.FB_USER_ACCESS_TOKEN)
    print("request.method "+request.method)

    if request.method == 'POST':
        user = User.query.filter_by(email=current_user.email).first()
        set_access_token_page_and_adaccount(user.fb_access_token)

        dropbox_ready_folder = request.form.get('path')     
        print('before',credentials.dropbox_ready_folder_path)   
        credentials.dropbox_ready_folder_path = dropbox_ready_folder
        print('before',credentials.dropbox_ready_folder_path)   

        campaign_name = request.form.get('campaign')


        folder_path = os.getcwd().replace('\\','/')
        file_path = folder_path+'/website/functionality.py'
        command = 'python '+file_path+' '+campaign_name
        print(command)
        os.system(command) 

        return 'your ad will be launched in few seconds'
       

    user = User.query.filter_by(email=current_user.email).first()

    if user.fb_access_token:
        set_access_token_page_and_adaccount(user.fb_access_token)

    rows  = []
    if user.dropbox_access_token:
        credentials.DROPBOX_ACCESS_TOKEN = user.dropbox_access_token

        readyfolderpaths = findReadyFolderPaths()        
        for camp, adsets in readyfolderpaths.items():
            path = adsets['path']
            item = {}
            ad_items = []
            for adsets, resource in adsets.items():
                if adsets != 'path':
                    ad_item = {}
                    ad_item['adset'] = adsets
                    ad_item['resource'] = resource
                    ad_items.append(ad_item)
            item['camp'] = camp
            item['path'] = path
            item['ads'] = ad_items
            rows.append(item)

        print(rows)

    return render_template("home.html", user=current_user,rows=rows)


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
    token = facebook.fetch_token(FB_TOKEN_URL, client_secret=FB_CLIENT_SECRET, authorization_response=request.url)
    print(token)
    user = User.query.filter_by(email=current_user.email).first()
    user.fb_access_token = token['access_token']
    db.session.commit()

    return redirect(url_for('views.home'))

@views.route('/dropboxlogin')
def dropboxlogin():

    print(url_for('views.dropbox_authorized'))
    return credentials.dropbox.authorize(callback=URL+'/login/authorized')
    
@views.route('/login/authorized')
def dropbox_authorized():
    resp = credentials.dropbox.authorized_response()
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
    campaign={}

    user = User.query.filter_by(email=current_user.email).first()
    dbx = dropbox.Dropbox(user.dropbox_access_token)    
    print("[SUCCESS] dropbox account linked")
    ready_campaign_path = []
    for entry in dbx.files_list_folder('/superlucky/').entries:
        for subEntry in dbx.files_list_folder('/superlucky/'+entry.name).entries:
            if subEntry.name == 'READY':
                # print(subEntry.name)      

                for campaigns in dbx.files_list_folder('/superlucky/'+entry.name+'/'+subEntry.name).entries:
                    # print(campaigns.name)                    
                    ready_campaign_path.append(campaigns.path_display) 

                    adset={}
                    for adsets in dbx.files_list_folder('/superlucky/'+entry.name+'/'+subEntry.name+'/'+campaigns.name).entries:
                        print(adsets.name)  
                        if not adsets.name.endswith('.csv'):             
                            adcreative=[]
                            for adcreatives in dbx.files_list_folder('/superlucky/'+entry.name+'/'+subEntry.name+'/'+campaigns.name+'/'+adsets.name).entries:
                                # print(adcreatives.name)
                                adcreative.append(adcreatives.name)

                            adset[adsets.name] = adcreative
                        campaign[campaigns.name] = adset
                        campaign[campaigns.name]['path'] = campaigns.path_display


    # print(ready_campaign_path)
    # print(campaign)
    return campaign

def set_access_token_page_and_adaccount(access_token):
    credentials.FB_USER_ACCESS_TOKEN = access_token
    r = requests.get('https://graph.facebook.com/v11.0/me/adaccounts?access_token='+access_token).json()
    print(r['data'][0]['id'])
    credentials.AD_ACCOUNT_ID= r['data'][0]['id']
    r = requests.get('https://graph.facebook.com/v11.0/me/accounts?access_token='+access_token).json()
    print(r['data'][0]['id'])

    credentials.PAGE_ID = r['data'][0]['id']
    

