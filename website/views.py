from functools import partial
from flask import Blueprint, render_template, request, flash, jsonify,redirect,url_for,session
from flask_login import login_required, current_user
from .models import Note,User
from . import db
import json
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
from . import config
import dropbox
import os
from zipfile import ZipFile
# external imports
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi

from  . adVideoCreativee import get_video_creative_id_from_file

access_token = 'EAAgEjhopC7UBANIosjWMEPQ9isBFf9nJsszL0Peu5HBCw8iB84jdgT8tKemhzatMh40HZC3fzBqBrFZA42WX6vee4RGAAYiHhG94wb0e9tkgWKdf3DfX5VDPZAc2PZBU5aKZBAHejluTm4988RPCWqn3OmcAbLZC6QmQk4WAaYMacQdyKJGKyZB'
app_secret = 'bc5fa70ff4ff8dd693f804ba4f0db80c'
app_id = 2256808184449973 
id = 'act_144169154493518'
FacebookAdsApi.init(access_token=access_token)



FB_CLIENT_ID=2256808184449973    
FB_CLIENT_SECRET="bc5fa70ff4ff8dd693f804ba4f0db80c"
FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
FB_SCOPE = ["email","ads_management"]
URL = "https://9ba698e93f61.ngrok.io" #update line 82 as well

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    print("request.method "+request.method)
    if request.method == 'POST':
        dropbox_ready_folder = request.form.get('path')
        campaign_name = request.form.get('campaign')
        print('path path path path path path')
        print(dropbox_ready_folder)

        # download campaign folder(zip) to local, extract it and the directory tree as dict
        directory_tree = downloadCampaignFolder(dropbox_ready_folder)
        print('directory_tree directory_tree')
        print(directory_tree)
        # launch campaign
        launch_campaign(directory_tree)

       

    user = User.query.filter_by(email=current_user.email).first()

    if user.dropbox_access_token:
        readyfolderpaths = findReadyFolderPaths()
        print(readyfolderpaths)
        print(type(readyfolderpaths))
        return render_template("home.html", user=current_user,paths=readyfolderpaths)

    return render_template("home.html", user=current_user,paths=[])

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
    token = facebook.fetch_token(FB_TOKEN_URL, client_secret=FB_CLIENT_SECRET, authorization_response=request.url)
    print(token)
    user = User.query.filter_by(email=current_user.email).first()
    user.fb_access_token = token['access_token']
    db.session.commit()

    return redirect(url_for('views.home'))

@views.route('/dropboxlogin')
def dropboxlogin():

    print(url_for('views.dropbox_authorized'))
    return config.dropbox.authorize(callback='https://9ba698e93f61.ngrok.io/login/authorized')
    
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
                        # print(adsets.name)              
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

def downloadCampaignFolder(path,campaign_name='camp2'):
    print("downloadCampaignFolder path path")
    print(path)
    user = User.query.filter_by(email=current_user.email).first()
    dbx = dropbox.Dropbox(user.dropbox_access_token)  

    folder_path = os.getcwd().replace('\\','/')
    file_name = "READY.zip"
    print(folder_path+'/'+file_name)

    # download folder as zip
    dbx.files_download_zip_to_file(path=path,download_path=folder_path+'/'+file_name)

    # extract the downloaded zip
    with ZipFile(file_name, 'r') as zip:
        print('Extracting all the files now...')
        zip.extractall()
        print('Done!')

    #convert directory structure to dict

    ready_directory_str = json.dumps(path_to_dict(folder_path+'/'+campaign_name))
    ready_directory = json.loads(ready_directory_str)
    print("downloadCampaignFolder directory tree")
    print(ready_directory)
    return ready_directory

def path_to_dict(path):
    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir\
(path)]
    else:
        d['type'] = "file"
    return d

def launch_campaign(campaign):
    print('ready directory in launch campaign')
    print(campaign)

    # for campaigns in ready_directory['children']:
    # print(campaigns['name'])

    create_campaign_params = {
                'name': campaign['name'],
                'objective': 'LINK_CLICKS',
                
                'status': 'ACTIVE',
                'special_ad_categories': [],
    }

    campaign_id = AdAccount(id).create_campaign(fields=[],params=create_campaign_params)
    print ('campaign_id =============='+campaign_id['id'])

    if 'children' in campaign:
        for adsets in campaign['children']:
            print(adsets['name'])
            create_ad_set_params = {
                'name': adsets['name'],
                'optimization_goal': 'REACH',
                'billing_event': 'IMPRESSIONS',
                'bid_amount': '2000',
                'daily_budget': '100000',
                'campaign_id': campaign_id['id'],
                'targeting': {'geo_locations':{'countries':['US']},'facebook_positions':['feed']},
                'status': 'ACTIVE',
            }
            ad_set_id = AdAccount(id).create_ad_set(fields=[],params=create_ad_set_params,)
            print ('ad_set_id =============='+ad_set_id['id'])

            if 'children' in adsets:
                for ads in adsets['children']:
                    print(campaign['name']+'/'+adsets['name']+'/'+ads['name']+ "    jfsidjfidgfagi")
                    video_ID = get_video_creative_id_from_file(campaign['name']+'/'+adsets['name']+'/'+ads['name'])
                    print(video_ID)
                    create_ad_creative_params = {
                        'name': 'new Sample Creative',
                        'object_story_spec': {'page_id':100237612354550,'video_data':{'image_url':'https://avatars.githubusercontent.com/u/8880186?s=88&u=ccd6fc36312b4d34e68fff60580f18ddddc58729&v=4','video_id':video_ID,'call_to_action':{'type':'INSTALL_MOBILE_APP','value':{'link':"https://play.google.com/store/apps/details?id=com.ludo.king"}}}},
                    }

                    adCreative = AdAccount(id).create_ad_creative(fields=[],params=create_ad_creative_params,)
                    print ('adCreative_id =============='+adCreative['id'])

                    create_ad_params = {

                        'name':ads['name'],
                        'adset_id': ad_set_id['id'],
                        'creative': {'creative_id':adCreative['id']},
                        'status': 'ACTIVE',
                        'object_story_spec': {'call_to_action':{'type':'LIKE_PAGE','e':{'page':"100237612354550"}}}
                        }
                    ad_id = AdAccount(id).create_ad(fields=[],params=create_ad_params)
                    print ('ad_id =============='+ad_id['id'])





    

