import sqlite3

try:
    conn = sqlite3.connect("databasecopy.db")    

except :
    print('e')

cursor = conn.cursor()
cursor.execute("SELECT fb_access_token,dropbox_access_token,auto_launch,last_runned FROM user;")
# print(f"user Name : {cursor.fetchall()}")
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