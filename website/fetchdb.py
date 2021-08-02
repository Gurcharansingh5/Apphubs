import sqlite3
from datetime import datetime, timedelta
# date_time_str = '2021-07-31 10:51:14.641043'
# print(type(date_time_str))
# date_time_obj1=datetime.fromisoformat(date_time_str)
# date_time_obj2 = datetime.fromisoformat(date_time_str) - timedelta(minutes=10)
# date_time_obj = date_time_obj1-date_time_obj2 
# print(type(date_time_obj))
# print(date_time_obj)



# try:
#     conn = sqlite3.connect("databasecopy.db")    

# except :
#     print('e')

# cursor = conn.cursor()
# cursor.execute("SELECT fb_access_token,dropbox_access_token,auto_launch,last_runned FROM user;")
# users=[]
# print(cursor.fetchall())
# for row in cursor.fetchall():
#     user={}
#     user['fb_access_token']=row[0]
#     user['dropbox_access_token']=row[1]
#     user['auto_launch']=row[2]
#     user['last_runned']= datetime.fromisoformat(row[3])

#     users.append(user)
#     # print(user)
# # print(users)

# conn.close()