# INNER IMPORTS
import re
from . credentials import FB_AUTHORIZATION_BASE_URL,FB_CLIENT_ID,FB_CLIENT_SECRET,FB_SCOPE,FB_TOKEN_URL,URL
from . import credentials
from .models import User
from . import db

# INTERNAL IMPORTS
import os
import csv
import requests
import threading


# external imports
from flask import Blueprint, render_template, request,redirect,url_for,session,flash
from flask_login import login_required, current_user
import dropbox
import requests_oauthlib
from requests_oauthlib.compliance_fixes import facebook_compliance_fix

views = Blueprint('views', __name__)

def launch_campaign_script(command):
    os.system(command) 


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    print("request.method "+request.method)

    if request.method == 'POST':
        user = User.query.filter_by(email=current_user.email).first()

        dropbox_ready_folder = request.form.get('path')     
        campaign_name = request.form.get('campaign')

        os.environ['DROPBOX_READY_FOLDER_PATH']=dropbox_ready_folder

        folder_path = os.getcwd().replace('\\','/')
        file_path = folder_path+'/website/functionality.py'
        command = 'python '+file_path+' '+campaign_name
        print(command)
        t1 = threading.Thread(target=launch_campaign_script, args=(command,))
        t1.start()
        flash('Campaign will be launched in few seconds', category='success')    

    selected_root_folder = request.args.get('root_folder')
    user = User.query.filter_by(email=current_user.email).first()
    if user.fb_access_token:
        set_access_token_page_and_adaccount(user.fb_access_token)

    rows  = []
    root_folders = []
    if user.dropbox_access_token:
        os.environ['DROPBOX_ACCESS_TOKEN'] = user.dropbox_access_token
        dbx = dropbox.Dropbox(user.dropbox_access_token)   
        print("[SUCCESS] dropbox account linked")
        for entry in dbx.files_list_folder("").entries:
            root_folders.append(entry.name)
        print(root_folders)

        readyfolderpaths = findReadyFolderPaths(selected_root_folder)       
        print('ready folder path')
        print(readyfolderpaths) 
        if readyfolderpaths :
            for camp, adsets in readyfolderpaths.items():

                path = adsets['path']
                campaign_settings = get_campaign_settings_from_csv(path)

                SKU = adsets['SKU']
                item = {}
                ad_items = []
                for adsets, resource in adsets.items():
                    if adsets != 'path' and adsets != 'SKU':
                        ad_item = {}
                        ad_item['adset'] = adsets
                        ad_item['resource'] = resource
                        ad_items.append(ad_item)
                item['camp'] = camp
                item['path'] = path
                item['ads'] = ad_items
                item['SKU'] = SKU
                item['settings'] = campaign_settings
                rows.append(item)

            # print(rows)

    return render_template("home.html", user=current_user,rows=rows,root_folders=root_folders) 


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
def findReadyFolderPaths(rootFolder):
    if rootFolder:
        dbx = dropbox.Dropbox(os.environ['DROPBOX_ACCESS_TOKEN'])   
        print("[SUCCESS] dropbox account linked")
        campaign={}    
        for entry in dbx.files_list_folder('/'+rootFolder).entries:     
            # entry here is the SKU
            if isinstance(entry,dropbox.files.FolderMetadata):
                for subEntry in dbx.files_list_folder('/'+rootFolder+'/'+entry.name).entries:
                    # subentry here is the folders inside SKU folder
                    if subEntry.name == 'READY':
                        for campaigns in dbx.files_list_folder('/'+rootFolder+'/'+entry.name+'/'+subEntry.name).entries:
                            # print("entry.name")
                            # print(entry.name)

                            # print("campaigns.name")
                            # print(campaigns.name)   

                            ready_campaign_path= '/'+rootFolder+'/'+entry.name+'/'+subEntry.name+'/'+campaigns.name
                            # print('ready_campaign_path')
                            # print(ready_campaign_path)

                            adset={}
                            for adsets in dbx.files_list_folder(ready_campaign_path).entries:
                                # print(adsets.name)  
                                if not adsets.name.endswith('.csv'):             
                                    adcreative=[]
                                    ready_adset_path = ready_campaign_path+'/'+adsets.name
                                    # print('ready_adset_path')
                                    # print(ready_adset_path)
                                    for adcreatives in dbx.files_list_folder(ready_adset_path).entries:
                                        # print(adcreatives.name)
                                        adcreative.append(adcreatives.name)
                                    adset[adsets.name] = adcreative

                                campaign[campaigns.name] = adset
                                campaign[campaigns.name]['path'] = campaigns.path_display
                                campaign[campaigns.name]['SKU'] = entry.name


        # print('campaign campaign campaign')
        # print(campaign)
        return campaign
    else:
        return None

def find_root_folder():
    dbx = dropbox.Dropbox(os.environ['DROPBOX_ACCESS_TOKEN'])   
    print("[SUCCESS] dropbox account linked")
    for entry in dbx.files_list_folder("").entries:
        print("shfdhdfh   "+entry.name)

def get_campaign_settings_from_csv(path):
    dbx = dropbox.Dropbox(os.environ['DROPBOX_ACCESS_TOKEN'])   
    print("[SUCCESS] dropbox account linked")
    metadata, f = dbx.files_download(path+'/settings.csv')
    csv_reader = csv.reader(f.content.decode().splitlines(), delimiter=',')
    list_of_rows = []  
    for row in csv_reader:
        list_of_rows.append(row)
    res = {list_of_rows[0][i]: list_of_rows[1][i] for i in range(len(list_of_rows[0]))}
    # print("get_campaign_settings_from_csv : ", res)
    return res

    

def set_access_token_page_and_adaccount(access_token):
    os.environ['FB_USER_ACCESS_TOKEN'] = access_token

    r = requests.get('https://graph.facebook.com/v11.0/me/adaccounts?access_token='+access_token).json()
    os.environ['AD_ACCOUNT_ID']= r['data'][0]['id']

    r = requests.get('https://graph.facebook.com/v11.0/me/accounts?access_token='+access_token).json()
    os.environ['PAGE_ID'] = r['data'][0]['id']

    

