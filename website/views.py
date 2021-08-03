# INNER IMPORTS
from .models import User
from . import db
from website.helperFunctions import findReadyFolderPaths,fb_token_valid,launch_campaign_script,getRowsFromReadyPath

# INTERNAL IMPORTS
import os
import time
import threading

# external imports
from flask import Blueprint, render_template, request,redirect,url_for,flash
from flask_login import login_required, current_user
import dropbox


views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    user = User.query.filter_by(email=current_user.email).first()
    if user.fb_access_token:       
        if not fb_token_valid(user.fb_access_token):
            user.fb_access_token = None
            db.session.commit()

    selected_root_folder = request.args.get('root_folder')
    if user.dropbox_access_token:
        dbx = dropbox.Dropbox(user.dropbox_access_token) 
        rows=[]
        root_folders = []
        for entry in dbx.files_list_folder("").entries:
            root_folders.append(entry.name)
        readyfolderpaths = findReadyFolderPaths(rootFolder=selected_root_folder,access_token=user.dropbox_access_token)    
        if readyfolderpaths :
            rows = getRowsFromReadyPath(readyfolderpaths,access_token=user.dropbox_access_token)           

    return render_template("home.html", user=current_user,rows=rows,root_folders=root_folders) 


@views.route('/update_auto_launch', methods=['GET', 'POST'])
@login_required
def update_auto_launch():
    if request.method == 'POST':

        auto_launch_flag = request.form.get('auto_flag')
        auto_launch_flag = True if auto_launch_flag == '1' else False
        time_delta = request.form.get('time_delta')

        user = User.query.filter_by(email=current_user.email).first()
        user.auto_launch = auto_launch_flag
        user.time_delta = int(time_delta)
        db.session.commit()

        return redirect(url_for('views.home'))


@views.route('/launch_campaign', methods=['GET', 'POST'])
@login_required
def launch_campaign():
    if request.method == 'POST':
        user = User.query.filter_by(email=current_user.email).first()

        dropbox_ready_folder = request.form.get('path')     
        campaign_name = request.form.get('campaign')

        folder_path = os.getcwd().replace('\\','/')
        file_path = folder_path+'/website/functionality.py'
        command = f'python {file_path} {campaign_name} {user.dropbox_access_token} {dropbox_ready_folder} {user.fb_access_token}'
        print(command)

        t1 = threading.Thread(target=launch_campaign_script, args=(command,))
        t1.start()
        flash('Campaign will be launched in few seconds', category='success') 
        time.sleep(5)

        return redirect(url_for('views.home'))










    



    






    
