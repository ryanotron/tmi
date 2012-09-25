import jinja2
import os, re, random, datetime, hashlib, logging
from string import letters

username_re = re.compile(r'^[a-zA-Z_-]{4,20}$')
password_re = re.compile(r'^.{4,20}$')
email_re    = re.compile(r'^[\S]+@[\S]+.[\S]+$')

COOKIESECRET = 'Fire and Blood!'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinjaenv = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def render_str(template, **params):
    t = jinjaenv.get_template(template)
    return t.render(params)
    
def securify_cookie(s):
    s = str(s)
    return s + '|' + hashlib.sha256(s + COOKIESECRET).hexdigest()
    
def verify_cookie(s):
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