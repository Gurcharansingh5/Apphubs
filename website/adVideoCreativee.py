import os
from facebook_business.adobjects.advideo import AdVideo
from facebook_business import FacebookSession
from facebook_business import FacebookAdsApi
from facebook_business.adobjects.advideo import AdVideo
import credentials

def get_video_creative_id_from_file(path,access_token,ad_account_id):
    AD_ACCOUNT_ID = ad_account_id
    FB_USER_ACCESS_TOKEN = access_token
    
    ### Setup session and api objects
    session = FacebookSession(credentials.FB_CLIENT_ID,credentials.FB_CLIENT_SECRET,FB_USER_ACCESS_TOKEN)
    FacebookAdsApi.set_default_api(FacebookAdsApi(session))
    video = AdVideo(parent_id=AD_ACCOUNT_ID)
    path = path.replace('"\"','/')

    folder_path = os.getcwd().replace('\\','/')
    video_path = folder_path+'/'+path
    
    # set video fields
    video[AdVideo.Field.filepath] = video_path

    # remote create
    video.remote_create()
    video.waitUntilEncodingReady()
    return video['id']