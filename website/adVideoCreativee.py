import os
from facebook_business.adobjects.advideo import AdVideo
from facebook_business import FacebookSession
from facebook_business import FacebookAdsApi
from facebook_business.adobjects.advideo import AdVideo

def get_video_creative_id_from_file(path):

    from . credentials import FB_CLIENT_ID,FB_CLIENT_SECRET,FB_USER_ACCESS_TOKEN,AD_ACCOUNT_ID
    
    ### Setup session and api objects
    session = FacebookSession(FB_CLIENT_ID,FB_CLIENT_SECRET,FB_USER_ACCESS_TOKEN)
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