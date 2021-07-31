from datetime import datetime
import credentials
import sqlite3

import os,shutil,csv,requests
import dropbox,json
from zipfile import ZipFile
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.advideo import AdVideo
from facebook_business import FacebookSession
from facebook_business import FacebookAdsApi
from facebook_business.adobjects.advideo import AdVideo

def getUsersFromDBfile():
    try:
        conn = sqlite3.connect("databasecopy.db")    
    except :
        print('e')

    cursor = conn.cursor()
    cursor.execute("SELECT fb_access_token,dropbox_access_token,auto_launch,last_runned FROM user;")
    users=[]
    for row in cursor.fetchall():
        user={}
        user['fb_access_token']=row[0]
        user['dropbox_access_token']=row[1]
        user['auto_launch']=row[2]
        user['last_runned']=row[3]
        users.append(user)
        # print(user)

    print(users)
    conn.close()
    return users

def findReadyFolderPaths(rootFolder,usertoken):
    if rootFolder:
        dbx = dropbox.Dropbox(usertoken)   
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

def path_to_dict(path):
    d = {'name': os.path.basename(path)}
    if os.path.isdir(path):
        d['type'] = "directory"
        d['children'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir\
(path)]
    else:
        d['type'] = "file"
    return d


def downloadCampaignFolder(path,campaign_name,accessToken):
    dbx = dropbox.Dropbox(accessToken)  
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
    os.environ['FB_USER_ACCESS_TOKEN'] = access_token

    r = requests.get('https://graph.facebook.com/v11.0/me/adaccounts?access_token='+access_token).json()
    os.environ['AD_ACCOUNT_ID']= r['data'][0]['id']

    r = requests.get('https://graph.facebook.com/v11.0/me/accounts?access_token='+access_token).json()
    os.environ['PAGE_ID'] = r['data'][0]['id']

def get_video_creative_id_from_file(path,accessToken):
    AD_ACCOUNT_ID = os.environ['AD_ACCOUNT_ID']
    FB_USER_ACCESS_TOKEN = accessToken
    ### Setup session and api objects
    session = FacebookSession(credentials.FB_CLIENT_ID,credentials.FB_CLIENT_SECRET,FB_USER_ACCESS_TOKEN)
    FacebookAdsApi.set_default_api(FacebookAdsApi(session))
    video = AdVideo(parent_id=AD_ACCOUNT_ID)

    print('get_video_creative_id_from_file')
    path = path.replace('"\"','/')
    print(path)

    folder_path = os.getcwd().replace('\\','/')
    video_path = folder_path+'/'+path
    print('videopath')
    print(video_path)
    
    # set video fields
    video[AdVideo.Field.filepath] = video_path

    # remote create
    video.remote_create()
    video.waitUntilEncodingReady()

    print(video)
    return video['id']

def launch_campaign(campaign,access_token,ad_settings):
    AD_ACCOUNT_ID=os.environ['AD_ACCOUNT_ID']
    PAGE_ID=os.environ['PAGE_ID']
    
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
                        video_ID = get_video_creative_id_from_file(campaign['name']+'/'+adsets['name']+'/'+ads['name'],accessToken=user['fb_access_token'])
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

def get_video_creative_id_from_file(path,accessToken):
    AD_ACCOUNT_ID = os.environ['AD_ACCOUNT_ID']
    FB_USER_ACCESS_TOKEN = accessToken
    ### Setup session and api objects
    session = FacebookSession(credentials.FB_CLIENT_ID,credentials.FB_CLIENT_SECRET,FB_USER_ACCESS_TOKEN)
    FacebookAdsApi.set_default_api(FacebookAdsApi(session))
    video = AdVideo(parent_id=AD_ACCOUNT_ID)


    print('get_video_creative_id_from_file')
    path = path.replace('"\"','/')
    print(path)

    folder_path = os.getcwd().replace('\\','/')
    video_path = folder_path+'/'+path
    print('videopath')
    print(video_path)
    
    # set video fields
    video[AdVideo.Field.filepath] = video_path

    # remote create
    video.remote_create()
    video.waitUntilEncodingReady()

    print(video)
    return video['id']

users = getUsersFromDBfile()
auto = True
for user in users:
    if user['auto_launch'] > 0:
        print('auto launch activated')

        if user['fb_access_token'] and user['dropbox_access_token']:
            print('fb and db token found')
            set_access_token_page_and_adaccount(user['fb_access_token'])
            dbx=dropbox.Dropbox(user['dropbox_access_token'])
            print('dbx connected')

            # if user.last_runned - datetime.now() > user.time:
            if True:                    
                # get path of ready folder
                readyfolderpaths = findReadyFolderPaths('superlucky',user['dropbox_access_token'])
                print('readyfolder paths')
                print(readyfolderpaths)

                if readyfolderpaths:       
                    for camp, adsets in readyfolderpaths.items():
                        print('for camp, adsets in readyfolderpaths.items()')
                        print(camp,adsets['path'])
                        campaign_name = camp
                        path = adsets['path']
                        
                        ready_folder_directory_tree = downloadCampaignFolder(path=path,campaign_name=campaign_name,accessToken=user['dropbox_access_token']) 
                        print('ready_folder_directory_tree')
                        print(readyfolderpaths)

                        # Read settings from settings.csv
                        ad_settings = get_settings_from_csv(campaign_name)

                        launch_campaign(ad_settings=ad_settings,campaign=ready_folder_directory_tree,access_token=user['fb_access_token'])

                        # Move campaign folder to ready folder
                        launch_folder_path = path.replace('READY','LAUNCHED')
                        dbx.files_move(from_path=path,to_path=launch_folder_path)

                        #delete downloaded folder from local
                        folder_path = os.getcwd().replace('\\','/')
                        shutil.rmtree(folder_path+'/'+campaign_name,"Authors")

                        # user.last_runned = datetime.now()
