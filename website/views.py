# INNER IMPORTS
from .models import User,SocialDetails
from . import db
from website.helperFunctions import findReadyFolderPaths,fb_token_valid,launch_campaign_script,getRowsFromReadyPath

# INTERNAL IMPORTS
import os
import time
import threading
import _thread

# external imports
from flask import Blueprint, render_template, request,redirect,url_for,flash
from flask_login import login_required, current_user
import dropbox


views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    fb_social_user = SocialDetails.query.filter_by(user_id=current_user.id,type='facebook',is_deleted=False).first()
    
    if fb_social_user:       
        if not fb_token_valid(fb_social_user.access_token):
            fb_social_user.access_token = None
            db.session.commit()

    rows=[]
    db_social_user = SocialDetails.query.filter_by(user_id=current_user.id,type='dropbox',is_deleted=False).first()
    if db_social_user:
        readyfolderpaths = findReadyFolderPaths(rootFolder=current_user.root_folder,access_token=db_social_user.access_token)    
        if readyfolderpaths :
            rows = getRowsFromReadyPath(readyfolderpaths,access_token=db_social_user.access_token,count=3)           
        print(rows)
    return render_template("index.html",social_user={'facebook':fb_social_user,'dropbox':db_social_user},user=current_user,rows=rows)


@views.route('/integrate_fb', methods=['GET', 'POST'])
@login_required
def integrate_fb():
    fb_social_user = SocialDetails.query.filter_by(user_id=current_user.id,type='facebook',is_deleted=False).first() 
    return render_template("integrate-fb.html",fb_social_user=fb_social_user,user=current_user)


@views.route('/integrate_db', methods=['GET', 'POST'])
@login_required
def integrate_db():

    if request.method == 'POST':
        selected_root_folder = request.form.get('root_folder')
        user = User.query.filter_by(email=current_user.email).first()
        user.root_folder = selected_root_folder
        db.session.commit()
    
    root_folders = []
    db_social_user = SocialDetails.query.filter_by(user_id=current_user.id,type='dropbox',is_deleted=False).first() 

    if db_social_user:
        dbx = dropbox.Dropbox(db_social_user.access_token)
        for entry in dbx.files_list_folder("").entries:
            root_folders.append(entry.name)

    return render_template("integrate-db.html",db_social_user=db_social_user,user=current_user,root_folders=root_folders)

@views.route('/campaigns', methods=['GET', 'POST'])
@login_required
def list_campaign():
    rows=[]
    db_social_user = SocialDetails.query.filter_by(user_id=current_user.id,type='dropbox',is_deleted=False).first()
    if db_social_user:
        readyfolderpaths = findReadyFolderPaths(rootFolder=current_user.root_folder,access_token=db_social_user.access_token)    
        if readyfolderpaths :
            rows = getRowsFromReadyPath(readyfolderpaths,access_token=db_social_user.access_token,count=0)           
        # print(rows)
    return render_template("campaign.html",user=current_user,rows=rows)


@views.route('/disconnect', methods=['GET', 'POST'])
@login_required
def disconnect_social():
    if request.method == 'POST':
        social_user_from_req = int(request.form.get('social_user'))
        social_user_from_db = SocialDetails.query.get(social_user_from_req) 
        social_user_from_db.is_deleted = True
        db.session.commit()

    return redirect(request.referrer)

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

        return redirect(url_for('views.integrate_fb'))


@views.route('/launch_campaign', methods=['GET', 'POST'])
@login_required
def launch_campaign():
    if request.method == 'POST':
        db_social_user = SocialDetails.query.filter_by(user_id=current_user.id,type='dropbox',is_deleted=False).first()
        fb_social_user = SocialDetails.query.filter_by(user_id=current_user.id,type='facebook',is_deleted=False).first() 


        dropbox_ready_folder = request.form.get('path')     
        campaign_name = request.form.get('campaign')

        folder_path = os.getcwd().replace('\\','/')
        file_path = folder_path+'/website/functionality.py'
        command = f'python {file_path} {campaign_name} {db_social_user.access_token} {dropbox_ready_folder} {fb_social_user.access_token}'
        print(command)


        _thread.start_new_thread(launch_campaign_script, (command,))
        # t1 = threading.Thread(target=launch_campaign_script, args=(command,))
        # t1.start()
        flash('Campaign will be launched in few seconds', category='success') 
        time.sleep(5)

        return redirect(url_for('views.home'))










    



    






    
