import constants
import random, datetime, hashlib, logging
from string import letters
from google.appengine.ext import db

def render_str(template, **params):
    t = constants.jinjaenv.get_template(template)
    return t.render(params)
    
def securify_cookie(s):
    s = str(s)
    return s + '|' + hashlib.sha256(s + constants.COOKIESECRET).hexdigest()
    
def verify_cookie(s):
    #logging.error('cookie string is %s' % s)
    if not s:
        return None
    value, vhash = s.split('|')
    if s == securify_cookie(value):
        return value
    else:
        return None
    
def securify_password(username, password, salt = None):
    if not salt:
        salt = ''.join([random.choice(letters) for i in range(5)])
    return hashlib.sha256(username + password + salt).hexdigest() + '|' + salt
    
def verify_password(username, password, hashedpw):
    [pw, salt] = hashedpw.split('|')
    return securify_password(username, password, salt) == hashedpw
    
def validate_user(userid):
    user = db.Key.from_path('UserModel', int(userid))
    if user:
        return db.get(user)
    else:
        return None
        
def verify_user(userid_cookie):
    userid = verify_cookie(userid_cookie)
    if userid:
        user = validate_user(userid)
        if user:
            return userid, user
        else:
            return None
    else:
        return None, None
        
def str_to_datetime(datestr):
    d,m,y = [int(elem) for elem in datestr.split('/')]
    return datetime.datetime(y, m, d)
    
def update_config(userconfig, key, data):
    #logging.error(str(userconfig) + str(key) + str(data))
    if not userconfig.has_key(key):
        userconfig[key] = [data]
    else:
        if not data in userconfig[key]:
            userconfig[key].append(data)
        else:
            return False
    #logging.error(userconfig)
    return userconfig