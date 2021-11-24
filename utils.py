import datetime
import hashlib
import json
import base64
import os
import hmac
import requests


def get_copy_notice(server_name):
    return f'©{datetime.datetime.now().year} {server_name}, All Rights Reserved.'

def get_timedelta(days):
    return datetime.timedelta(days=days)

def sql_all_to_json(objs, sort_by=None):
    if len(objs) < 1:
        return []
    values = list()
    columns = [col.name for col in objs[0].__table__.columns]
    for i in objs:
        val = dict()
        for j in columns:
            val[j] = i.__getattribute__(j)
        values.append(val)
    if sort_by:
        values.sort(key=lambda x: x[sort_by])
    return values


def read_config(config_file='env.json'):
    with open(config_file, 'r') as f:
        env = json.load(f)
    if not 'flask_secret' in env:
        env['flask_secret'] = hashlib.sha256(os.urandom(2048)).hexdigest()
        with open(config_file,'w') as f:
            json.dump(env, f, indent=4)
    return env

def mk_hashed_pwd_with_salt(password, salt, separator='$'):
    hash = hashlib.sha512(f'{salt}{password}{salt.lower()}'.encode('utf-8')).hexdigest()
    return f'{salt}{separator}{hash}'

def mk_hashed_pwd_from_plain(password, separator='$'):
    salt = base64.b64encode(os.urandom(32)).decode('utf-8')
    return mk_hashed_pwd_with_salt(password, salt, separator)

def secure_compare(str1, str2):
    return hmac.compare_digest(str1, str2)

def compare_login_password(from_db, password, separator='$'):
    salt, _ =from_db.split(separator)
    from_local = mk_hashed_pwd_with_salt(password, salt)
    return secure_compare(from_db, from_local) # prevent timing attack

def send_admin_hook(hook_url, text):
    requests.post(hook_url, json={'content': text})

class User:
    def __init__(self, student_id, authenticated=False, full_name=''):
        self.__is_authenticated = authenticated
        self.__id = student_id
        self.__full_name = full_name
    
    def is_authenticated(self):
        return self.__is_authenticated
    
    def is_anonymous(self):
        return False
    
    def is_active(self):
        return True

    def get_id(self):
        return self.__id
    
    def get_full_name(self):
        return self.__full_name

def get_user_object(student_id, authenticated=False, full_name=''):
    return User(student_id, authenticated, full_name)
