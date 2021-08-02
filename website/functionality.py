# INNER IMPORTS
from adVideoCreativee import get_video_creative_id_from_file

# INTERNAL IMPORTS
import json
import os
import csv
import shutil
import sys
import requests

# external imports
from zipfile import ZipFile
import dropbox
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi


campaign_name=sys.argv[1]
DROPBOX_ACCESS_TOKEN = sys.argv[2]
dropbox_ready_folder = sys.argv[3]
FB_USER_ACCESS_TOKEN = sys.argv[4]

def path_to_dict(path):
    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir\
(path)]
    else:
        d['type'] = "file"
    return d

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)  

def downloadCampaignFolder(path,campaign_name):
    print("downloadCampaignFolder path path")
    print(path)

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
    os.remove(folder_path+'/'+file_name)
    #convert directory structure to dict

    ready_directory_str = json.dumps(path_to_dict(folder_path+'/'+campaign_name))
    ready_directory = json.loads(ready_directory_str)
    print("downloadCampaignFolder directory tree")
    print(ready_directory)
    return ready_directory

def get_settings_from_csv(campaign):
    folder_path = os.getcwd().replace('\\','/')
    folder_path = folder_path+'/'+campaign

    with open(folder_path+'/settings.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        list_of_rows = []  
        for row in csv_reader:
            list_of_rows.append(row)

    res = {list_of_rows[0][i]: list_of_rows[1][i] for i in range(len(list_of_rows[0]))}
    print("list_of_rows : ", res)
    return res

def set_access_token_page_and_adaccount(access_token):

    r = requests.get('https://graph.facebook.com/v11.0/me/adaccounts?access_token='+access_token).json()
    print(r)
    AD_ACCOUNT_ID= r['data'][0]['id']

    r = requests.get('https://graph.facebook.com/v11.0/me/accounts?access_token='+access_token).json()
    print(r)
    PAGE_ID= r['data'][0]['id']

    return AD_ACCOUNT_ID,PAGE_ID

def launch_campaign(campaign,access_token,ad_settings):
    AD_ACCOUNT_ID,PAGE_ID = set_access_token_page_and_adaccount(access_token)       
    
    FacebookAdsApi.init(access_token=access_token)

    create_campaign_params = {
                'name': campaign['name'],
                'objective': ad_settings['campaign_objective'],                
                'status': ad_settings['campaign_status'],
                'special_ad_categories': [],
    }
    print('AD_ACCOUNT_ID ',AD_ACCOUNT_ID)
    campaign_id = AdAccount(AD_ACCOUNT_ID).create_campaign(fields=[],params=create_campaign_params)
    print ('campaign_id =============='+campaign_id['id'])

    if 'children' in campaign:
        for adsets in campaign['children']:            
            print(adsets['name'])
            if not adsets['name'].endswith('.csv'):             

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
                ad_set_id = AdAccount(AD_ACCOUNT_ID).create_ad_set(fields=[],params=create_ad_set_params,)
                print ('ad_set_id =============='+ad_set_id['id'])

                if 'children' in adsets:
                    for ads in adsets['children']:
                        print(campaign['name']+'/'+adsets['name']+'/'+ads['name']+ "    jfsidjfidgfagi")
                        video_ID = get_video_creative_id_from_file(campaign['name']+'/'+adsets['name']+'/'+ads['name'],access_token=access_token,ad_account_id=AD_ACCOUNT_ID)
                        print(video_ID)
                        create_ad_creative_params = {
                            'name': 'new Sample Creative',
                            'object_story_spec': {'page_id':PAGE_ID,'video_data':{'image_url':'https://avatars.githubusercontent.com/u/8880186?s=88&u=ccd6fc36312b4d34e68fff60580f18ddddc58729&v=4','video_id':video_ID,'call_to_action':{'type':'INSTALL_MOBILE_APP','value':{'link':"https://play.google.com/store/apps/details?id=com.ludo.king"}}}},
                        }

                        adCreative = AdAccount(AD_ACCOUNT_ID).create_ad_creative(fields=[],params=create_ad_creative_params,)
                        print ('adCreative_id =============='+adCreative['id'])

                        create_ad_params = {

                            'name':ads['name'],
                            'adset_id': ad_set_id['id'],
                            'creative': {'creative_id':adCreative['id']},
                            'status': 'ACTIVE',
                            'object_story_spec': {'call_to_action':{'type':'LIKE_PAGE','e':{'page':PAGE_ID}}}
                            }
                        ad_id = AdAccount(AD_ACCOUNT_ID).create_ad(fields=[],params=create_ad_params)
                        print ('ad_id =============='+ad_id['id'])


# download campaign folder(zip) to local, extract it and the directory tree as dict
directory_tree = downloadCampaignFolder(path=dropbox_ready_folder,campaign_name=campaign_name) 
print('directory_tree directory_tree')
print(directory_tree)

# Read settings from settings.csv
ad_settings = get_settings_from_csv(campaign_name)

# launch campaign
launch_campaign(ad_settings=ad_settings,campaign=directory_tree,access_token=FB_USER_ACCESS_TOKEN)

# Move campaign folder to ready folder
launch_folder_path = dropbox_ready_folder.replace('READY','LAUNCHED')
dbx.files_move(from_path=dropbox_ready_folder,to_path=launch_folder_path)

#delete downloaded folder from local
folder_path = os.getcwd().replace('\\','/')
shutil.rmtree(folder_path+'/'+campaign_name,"Authors")