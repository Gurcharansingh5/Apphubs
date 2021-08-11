# import requests
# import json
# r = requests.post('https://api.dropboxapi.com/2/users/get_current_account', headers={"Authorization": "Bearer a041E0xGBNcAAAAAAAAAATZvqXtLNAi8XJ7tIEz8HJsrZvv8nAlVyCn5n2f1vZSN"})
# detail = json.loads(r.content.decode('utf-8'))
# print(detail['name']['display_name'])
# print(detail['email'])
# print(detail['profile_photo_url'])
from datetime import datetime
from dateutil import tz



# METHOD 2: Auto-detect zones:
from_zone = tz.tzutc()
to_zone = tz.tzlocal()

utc = datetime.utcnow()
print(utc)

utc = utc.replace(tzinfo=from_zone)

central = utc.astimezone(to_zone)
print(central.replace(microsecond=0))
