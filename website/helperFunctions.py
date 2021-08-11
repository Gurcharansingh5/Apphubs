# INTERNAL IMPORTS
import csv
import os
import requests

# EXTERNAL IMPORTS
import dropbox

def launch_campaign_script(command):
    os.system(command) 

def getRowsFromReadyPath(readyfolderpaths,access_token,count):
    rows  = []
    counter = 0
    for camp, adsets in readyfolderpaths.items():
        con = True if count == 0 else counter < count
        if con : 
            path = adsets['path']
            campaign_settings = get_campaign_settings_from_csv(path=path,access_token=access_token)

            SKU = adsets['SKU']
            item = {}
            ad_items = []
            for adsets, resource in adsets.items():
                if adsets != 'path' and adsets != 'SKU':
                    ad_item = {}
                    ad_item['adset'] = adsets
                    ad_item['resource'] = resource
                    ad_items.append(ad_item)
            item['camp'] = camp
            item['path'] = path
            item['ads'] = ad_items
            item['SKU'] = SKU
            item['settings'] = campaign_settings
            rows.append(item)
            counter +=1
        
    return rows
    # print(rows)
    
# function for checking if Ready folder exists
def findReadyFolderPaths(rootFolder,access_token):
    if rootFolder:
        dbx = dropbox.Dropbox(access_token)   
        print("[SUCCESS] dropbox account linked")
        campaign={}    
        for entry in dbx.files_list_folder('/'+rootFolder).entries:     
            # entry here is the SKU
            if isinstance(entry,dropbox.files.FolderMetadata):
                for subEntry in dbx.files_list_folder('/'+rootFolder+'/'+entry.name).entries:
                    # subentry here is the folders inside SKU folder
                    if subEntry.name == 'READY':
                        for campaigns in dbx.files_list_folder('/'+rootFolder+'/'+entry.name+'/'+subEntry.name).entries:
                            ready_campaign_path= '/'+rootFolder+'/'+entry.name+'/'+subEntry.name+'/'+campaigns.name
                            adset={}
                            for adsets in dbx.files_list_folder(ready_campaign_path).entries:
                                if not adsets.name.endswith('.csv'):             
                                    adcreative=[]
                                    ready_adset_path = ready_campaign_path+'/'+adsets.name
                                    for adcreatives in dbx.files_list_folder(ready_adset_path).entries:
                                        adcreative.append(adcreatives.name)
                                    adset[adsets.name] = adcreative

                                campaign[campaigns.name] = adset
                                campaign[campaigns.name]['path'] = campaigns.path_display
                                campaign[campaigns.name]['SKU'] = entry.name



        return campaign
    else:
        return None

def get_campaign_settings_from_csv(path,access_token):
    dbx = dropbox.Dropbox(access_token)   
    # print("[SUCCESS] dropbox account linked")
    metadata, f = dbx.files_download(path+'/settings.csv')
    csv_reader = csv.reader(f.content.decode().splitlines(), delimiter=',')
    list_of_rows = []  
    for row in csv_reader:
        list_of_rows.append(row)
    res = {list_of_rows[0][i]: list_of_rows[1][i] for i in range(len(list_of_rows[0]))}
    return res

def set_access_token_page_and_adaccount(access_token):
    r = requests.get('https://graph.facebook.com/v11.0/me/adaccounts?access_token='+access_token).json()
    AD_ACCOUNT_ID= r['data'][0]['id']
    r = requests.get('https://graph.facebook.com/v11.0/me/accounts?access_token='+access_token).json()
    PAGE_ID= r['data'][0]['id']
    return AD_ACCOUNT_ID,PAGE_ID

def fb_token_valid(access_token):
    # print(access_token)
    r = requests.get('https://graph.facebook.com/v11.0/me/?access_token='+access_token).json()
    print(r)
    return True if 'id' in r else False

    