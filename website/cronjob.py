from datetime import datetime,timedelta
from . import credentials
# import credentials
import sqlite3
import pathlib
import logging
import os,shutil,csv,requests
import dropbox,json
from zipfile import ZipFile
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.advideo import AdVideo
from facebook_business import FacebookSession
from facebook_business import FacebookAdsApi
from facebook_business.adobjects.advideo import AdVideo

#Create and configure logger
logging.basicConfig(filename="newfile.log",
                    format='%(asctime)s %(message)s',
                    filemode='w')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)

class Interact_with_DB:

    def __init__(self):
        try:
            db_path = str(pathlib.Path(__file__).parent.resolve())+'/database.db'
            self.conn = sqlite3.connect(db_path)    
        except Exception as ex:
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)

    def getUsersFromDBfile(self):        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id,auto_launch,last_runned,time_delta FROM user;") 
        queryset= cursor.fetchall() 
        users=[]
        for row in queryset:
            user={}
            fb_query = "SELECT access_token FROM social_details WHERE user_id='"+row[0]+"' AND type='facebook' AND is_deleted=False"            
            cursor.execute(fb_query)
            fb_queryset= cursor.fetchone() 
            user['fb_access_token']=fb_queryset[0]

            db_query = "SELECT access_token FROM social_details WHERE user_id='"+row[0]+"' AND type='dropbox' AND is_deleted=False"            
            cursor.execute(db_query)
            db_queryset= cursor.fetchone() 
            user['dropbox_access_token']=db_queryset[0]
            
            print('enteres')
            user['auto_launch']=row[1]
            user['last_runned']= None

            if row[2] :
                user['last_runned']= datetime.fromisoformat(row[2])
            
            user['time_delta'] = row[3]
            print(user)
            users.append(user)
        print(users)
        return users
    
    def updateLastRunned(self,last_runned,dropbox_access_token):        
        cursor = self.conn.cursor()
        query = f"UPDATE user SET last_runned='{last_runned}' WHERE dropbox_access_token='{dropbox_access_token}'"
        print(query)
        cursor.execute(query)   
        self.conn.commit()   

def findReadyFolderPaths(rootFolder,usertoken):
    if rootFolder:
        dbx = dropbox.Dropbox(usertoken)   
        print("[SUCCESS] dropbox account linked")
        campaign={}    
            
        for entry in dbx.files_list_folder('/'+rootFolder.name).entries:     
            # entry here is the SKU
            if isinstance(entry,dropbox.files.FolderMetadata):
                for subEntry in dbx.files_list_folder('/'+rootFolder.name+'/'+entry.name).entries:
                    # subentry here is the folders inside SKU folder
                    if subEntry.name == 'READY':
                        for campaigns in dbx.files_list_folder('/'+rootFolder.name+'/'+entry.name+'/'+subEntry.name).entries:
                            # print("entry.name")
                            # print(entry.name)

                            # print("campaigns.name")
                            # print(campaigns.name)   

                            ready_campaign_path= '/'+rootFolder.name+'/'+entry.name+'/'+subEntry.name+'/'+campaigns.name
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

    folder_path = str(pathlib.Path(__file__).parent.resolve()).replace('\\','/')
    file_name = "READY.zip"
    download_path=folder_path+'/'+file_name
    print(download_path)

    # download folder as zip
    dbx.files_download_zip_to_file(path=path,download_path=download_path)

    # extract the downloaded zip
    with ZipFile(download_path, 'r') as zip:
        print('Extracting all the files now...')
        zip.extractall(folder_path)
        print('Done!')
    os.remove(folder_path+'/'+file_name)
    #convert directory structure to dict

    ready_directory_str = json.dumps(path_to_dict(folder_path+'/'+campaign_name))
    ready_directory = json.loads(ready_directory_str)
    print("downloadCampaignFolder directory tree")
    print(ready_directory)
    return ready_directory

def get_settings_from_csv(campaign):
    folder_path = str(pathlib.Path(__file__).parent.resolve()).replace('\\','/')
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
    print('set_access_token_page_and_adaccount')
    print(access_token)
    r = requests.get('https://graph.facebook.com/v11.0/me/adaccounts?access_token='+access_token).json()
    AD_ACCOUNT_ID= r['data'][0]['id']

    r = requests.get('https://graph.facebook.com/v11.0/me/accounts?access_token='+access_token).json()
    PAGE_ID = r['data'][0]['id']

    return AD_ACCOUNT_ID,PAGE_ID

def get_video_creative_id_from_file(path,accessToken,ad_account_id):
    AD_ACCOUNT_ID = ad_account_id
    FB_USER_ACCESS_TOKEN = accessToken
    ### Setup session and api objects
    session = FacebookSession(credentials.FB_CLIENT_ID,credentials.FB_CLIENT_SECRET,FB_USER_ACCESS_TOKEN)
    FacebookAdsApi.set_default_api(FacebookAdsApi(session))
    video = AdVideo(parent_id=AD_ACCOUNT_ID)

    print('get_video_creative_id_from_file')
    path = path.replace('"\"','/')
    print(path)

    folder_path = str(pathlib.Path(__file__).parent.resolve()).replace('\\','/')
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

def launch_campaign(campaign,access_token,ad_settings,ad_account_id,page_id):
    AD_ACCOUNT_ID=ad_account_id
    PAGE_ID=page_id
    
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
                        video_ID = get_video_creative_id_from_file(campaign['name']+'/'+adsets['name']+'/'+ads['name'],accessToken=access_token,ad_account_id=ad_account_id)
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

def get_video_creative_id_from_file(path,accessToken,ad_account_id):
    AD_ACCOUNT_ID = ad_account_id
    FB_USER_ACCESS_TOKEN = accessToken
    ### Setup session and api objects
    session = FacebookSession(credentials.FB_CLIENT_ID,credentials.FB_CLIENT_SECRET,FB_USER_ACCESS_TOKEN)
    FacebookAdsApi.set_default_api(FacebookAdsApi(session))
    video = AdVideo(parent_id=AD_ACCOUNT_ID)


    print('get_video_creative_id_from_file')
    path = path.replace('"\"','/')
    print(path)

    folder_path = str(pathlib.Path(__file__).parent.resolve()).replace('\\','/')
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


def main_cron():   

    db_obj = Interact_with_DB()
    users= db_obj.getUsersFromDBfile()
    logger.info("execution starts")
    print('execution starts')
    print(users)
    for user in users:
        if user['auto_launch'] > 0:
            logger.info("auto launch activated")
            print('auto launch activated')
            if user['fb_access_token'] and user['dropbox_access_token']:
                logger.info("fb and db token found")
                print('fb and db token found')

                ad_account_id,page_id =set_access_token_page_and_adaccount(access_token = user['fb_access_token'])
                dbx=dropbox.Dropbox(user['dropbox_access_token'])
                logger.info("dbx connected")
                print('dbx connected')

                if user['last_runned'] == None or datetime.now() - user['last_runned'] >= timedelta(minutes=user['time_delta']):
                    for root_folder in dbx.files_list_folder("").entries:
                        readyfolderpaths = findReadyFolderPaths(rootFolder=root_folder,usertoken=user['dropbox_access_token'])
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

                                launch_campaign(ad_settings=ad_settings,campaign=ready_folder_directory_tree,access_token=user['fb_access_token'],ad_account_id=ad_account_id,page_id=page_id)
                                logger.info("campaign launched")

                                db_obj.updateLastRunned(last_runned=datetime.now(),dropbox_access_token=user['dropbox_access_token'])
                                # Move campaign folder to ready folder
                                launch_folder_path = path.replace('READY','LAUNCHED')
                                dbx.files_move(from_path=path,to_path=launch_folder_path)

                                #delete downloaded folder from local
                                folder_path = str(pathlib.Path(__file__).parent.resolve()).replace('\\','/')
                                shutil.rmtree(folder_path+'/'+campaign_name,"Authors")
                            
                                # user.last_runned = datetime.now()
                        else:
                            print('no campaigns to launch in '+root_folder.name )
main_cron()