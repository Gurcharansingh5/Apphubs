import os
from facebook_business.adobjects.advideo import AdVideo
from facebook_business import FacebookSession
from facebook_business import FacebookAdsApi
from facebook_business.adobjects.advideo import AdVideo
### Setup session and api objects
session = FacebookSession(
    2256808184449973,
    'bc5fa70ff4ff8dd693f804ba4f0db80c',
    'EAAgEjhopC7UBAHALZAGMXxCFdi9k7vNt8kSikJeYklKHvt5ILzOGuVunItAL2sTkE5Cg8vp2pigUtqlpDOTOGVKZBsUJNaP4h31dxE4fZBnmLN22GFAbIXDYxjg54bU0iFJpqYZCk3oSYZBZBf1pdftIVwZC2y4UBL19YPZAnS7PJSZCy1sJeoNJw',
)
FacebookAdsApi.set_default_api(FacebookAdsApi(session))
video = AdVideo(parent_id='act_144169154493518')

def get_video_creative_id_from_file(path):

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