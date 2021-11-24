from flask import Flask, render_template, redirect
from flask import request as f_req
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_minify import minify
import functools

import utils
from dbms import DBMS
from class_videos_handler import CVHandler
from api_manager import API

env = utils.read_config()

app = Flask(__name__, template_folder='pug')
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')
minify(app=app,html=True)
app.config['SECRET_KEY'] = env['flask_secret']

dbms = DBMS()
cvh = CVHandler(dbms)
api = API(dbms)

login_manager = LoginManager(app)

common_items = {
    'ftp_url': env.get('ftp_url', '#'),
    'copy_notice': utils.get_copy_notice(env.get('server_name', 'WeRockzz')),
    'server_name': env.get('server_name', 'WeRockzz')
}

def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            pass #do nothing
        else:
            return f(*args, **kwargs)
    return wrapped

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect('/login?auth_required=1')

@login_manager.user_loader
def load_user(user_id):
    return dbms.get_user_object(student_id=user_id)

@app.get('/')
@login_required
def home():
    data = cvh.get42data()
    data.update(common_items)
    data['user_full_name'] = dbms.get_user_object(current_user.get_id()).get_full_name()
    return render_template('class_videos.pug', data=data)

@app.get('/41-videos')
@login_required
def video41():
    data = cvh.get41data()
    data.update(common_items)
    data['user_full_name'] = dbms.get_user_object(current_user.get_id()).get_full_name()
    return render_template('class_videos.pug', data=data)

@app.get('/login')
def login():
    user = dbms.get_user_object(current_user.get_id())
    if user and user.is_authenticated():
        return redirect('/')
    
    data = {
        'email_placeholder': 'Enter Student ID',
        'login_failed' : False
    }
    data.update(common_items)

    if f_req.args.get('auth_required') == '1':
        data['welcome_text'] = 'You must login to continue.'
    elif f_req.args.get('attemp'):
        data['login_failed'] = True
        data['welcome_text'] = 'Invalid Student ID or Password.'
    else:
        data['welcome_text'] = 'Welcome Back!'
    
    return render_template('login.pug', data=data)

@app.post('/login')
def login_post():
    sid = f_req.form.get('sid')
    password = f_req.form.get('password')
    remember = f_req.form.get('remember') == 'on'

    if not dbms.check_login(sid, password):
        return redirect('/login?attemp=1')
    
    dbms.change_login_status(sid, 'in')
    login_user(dbms.get_user_object(sid), remember=remember, duration=utils.get_timedelta(days=30))
    return redirect('/')

@app.get('/logout')
@login_required
def logout():
    student_id = current_user.get_id()
    dbms.change_login_status(student_id, 'out')
    logout_user()
    return redirect('/login')

@app.get('/forgot-password')
def forgot_pass():
    if f_req.args.get('success','').lower() == 'yes':
        data = {'forgot_password_text': 'Password reset request submitted successfully. You will be contacted by the admin.'}
    elif f_req.args.get('success','').lower() == 'no':
        data = {'forgot_password_text': 'Invalid Student ID or no account was found.'}
    else:
        data = {'forgot_password_text': 'We get it, stuff happens. Just enter your Student ID below and we will reset your password!'}
    
    data.update(common_items)
    return render_template('forgot-password.pug', data=data)

@app.post('/forgot-password')
def forgot_pass_post():
    sid = f_req.form.get('sid')
    if dbms.get_user_object(sid) is None:
        return redirect('/forgot-password?success=no')
    utils.send_admin_hook(env['admin_webhook'], text=f'{sid} want\'s to reset password.')
    return redirect('/forgot-password?success=yes')

@app.get('/change-password')
@login_required
def change_pass():
    if f_req.args.get('status') == '1':
        data = {'change_password_text': 'Incorrect present password!'}
    elif f_req.args.get('status') == '2':
        data = {'change_password_text': 'Confirm-password doesn\'t match!'}
    elif f_req.args.get('status') == '3':
        data = {'change_password_text': 'Minimum 8 character password requred.'}
    elif f_req.args.get('status') == '0':
        data = {'change_password_text': 'Password successfully changed!'}
    else:
        data = {'change_password_text': 'Change your password (8 character minimum).'}
    data.update(common_items)
    return render_template('change-password.pug', data=data)

@app.post('/change-password')
@login_required
def change_pass_post():
    password = f_req.form.get('password','')
    password1 = f_req.form.get('password1','')
    password2 = f_req.form.get('password2','')
    if not dbms.check_login(current_user.get_id(), password):
        return redirect('/change-password?status=1')
    if password1 != password2:
        return redirect('/change-password?status=2')
    if len(password1) < 8:
        return redirect('/change-password?status=3')
    
    full_name = dbms.get_user_object(current_user.get_id()).get_full_name()
    dbms.update_user(current_user.get_id(), password1, full_name)
    return redirect('/change-password?status=0')

@app.post('/api')
def handle_api_post():
    auth_header = f_req.headers.get('Authorization')
    if not (auth_header and utils.secure_compare(auth_header.lower(), f'bearer {env["api_token"]}')):
        return 'Forbidden!', 403
    return api.handle_request(f_req.json)

def main():
    app.run(port=65005)

if __name__ == '__main__':
    main()
