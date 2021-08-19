import os
# GOOGLE CREDENTIALS
GOOGLE_CLIENT_ID = os.environ['GOOGLE_CLIENT_ID']
GOOGLE_CLIENT_SECRET = os.environ['GOOGLE_CLIENT_SECRET']
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# FACEBOOK CREDENTIALS
FB_CLIENT_ID=os.environ['FB_CLIENT_ID']
FB_CLIENT_SECRET=os.environ['FB_CLIENT_SECRET']
FB_AUTHORIZATION_BASE_URL = "https://www.facebook.com/dialog/oauth"
FB_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"
FB_SCOPE = ["email","ads_management"]
URL = "https://9dbce98b6ad8.ngrok.io"



# DROPBOX CREDENTIALS
DROPBOX_CONSUMER_KEY=os.environ['DROPBOX_CONSUMER_KEY']
DROPBOX_CONSUMER_SECRET=os.environ['DROPBOX_CONSUMER_SECRET']

dropbox=''
