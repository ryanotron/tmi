import webapp2, jinja2
import os, re, random, datetime, hashlib
from google.appengine.ext import db
from string import letters

COOKIESECRET = 'Fire and Blood!'

username_re = re.compile(r'^[a-zA-Z_-]{4,20}$')
password_re = re.compile(r'^.{4,20}$')
email_re    = re.compile(r'^[\S]+@[\S]+.[\S]+$')

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinjaenv = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class UserModel(db.Model):
    username = db.StringProperty(required = True)
    hashedpw = db.StringProperty(required = True)
    nameday  = db.DateTimeProperty(auto_now_add = True)
    email    = db.EmailProperty()

class ActivityModel(db.Model):
    name = db.StringProperty(required = True)
    start = db.DateTimeProperty(required = True)
    end = db.DateTimeProperty(required = True)
    
class CommuteModel(db.Model):
    origin = db.StringProperty(required = True)
    destination = db.StringProperty(required = True)
    start = db.DateTimeProperty(required = True)
    end = db.DateTimeProperty(required = True)

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

class SuperHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **params):
        self.write(self.render_str(template, **params))

class MainPageHandler(SuperHandler):
    def get(self):
        name = self.request.get('name')
        if not name:
            name = 'anon'
        self.render('mainpage.html', name = name)
        
class PanelHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = verify_cookie(userid)
            if userid:
                key = db.Key.from_path('UserModel', int(userid))
                user = db.get(key)
                self.render('panelpage.html', username = user.username)
            else:
                self.redirect('/signup')
        else:
            self.redirect('/signup')
        
class ActivityHandler(SuperHandler):
    def post(self):
        act_name = self.request.get('act_name')
        act_start_h = self.request.get('act_start_h')
        act_start_m = self.request.get('act_start_m')
        act_finish_h = self.request.get('act_finish_h')
        act_finish_m = self.request.get('act_finish_m')
        act_duration = self.request.get('act_duration')
        
        activity = ActivityModel(name  = act_name,
                                 start = datetime.datetime.now(),
                                 end   = datetime.datetime.now())
        
        today = datetime.datetime.today()
        if act_start_h:
            activity.start = datetime.datetime(today.year, today.month, today.day, int(act_start_h), int(act_start_m))
            if act_duration:
                duration = datetime.timedelta(minutes = float(act_duration))
                activity.end = activity.start + duration
            else:
                activity.end = datetime.datetime(today.year, today.month, today.day, int(act_finish_h), int(act_finish_m))
        else:
            activity.end = datetime.datetime(today.year, today.month, today.day, int(act_finish_h), int(act_finish_m))
            duration = datetime.timedelta(minutes = float(act_duration))
            activity.start = activity.end - duration
            
        activity.put()
        self.redirect('/panel')
        
class SignupHandler(SuperHandler):
    def get(self):
        self.render('signuppage.html')
        
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify   = self.request.get('verify')
        email    = self.request.get('email')
        
        error = False
        username_error = ''
        password_error = ''
        verification_error = ''
        email_error = ''
        
        if username:
            valid = username_re.match(username)
            if valid:
                names = db.GqlQuery('select * from UserModel where username = \'%s\' limit 1' % username)
                names = list(names)
                if names:
                    username_error = 'This username is taken!'
                    error = True
                else:
                    valid_pw = password_re.match(password)
                    if valid_pw:
                        if password == verify:
                            new_user = UserModel(username = username, hashedpw = securify_password(username, password))
                        else:
                            verification_error = 'Passwords do not match!'
                            error = True
                    else:
                        password_error = 'This is an invalid password!'
                        error = True
            else:
                username_error = 'This is an invalid username!'
                error = True
                
            if not error and new_user:
                if email:
                    valid_email = email_re.match(email)
                    if valid_email:
                        new_user.email = email
                        new_user.put()
                    else:
                        email_error = 'This is an invalid email!'
                        error = True
                else:
                    new_user.put()
        if error:
            self.render('signuppage.html', username = username,
                                           email = email,
                                           username_error = username_error,
                                           password_error = password_error,
                                           verification_error = verification_error,
                                           email_error = email_error)
        else:
            userid = str(new_user.key().id())
            self.response.headers.add_header('Set-Cookie', 'userid=%s; Path=/' % securify_cookie(userid))
            self.redirect('/panel')
            
class LogoutHandler(SuperHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'userid=; Path=/')
        self.redirect('/signup')
            
app = webapp2.WSGIApplication([('/', MainPageHandler),
                               ('/panel/?', PanelHandler),
                               ('/activity/?', ActivityHandler),
                               ('/signup/?', SignupHandler),
                               ('/logout/?', LogoutHandler)],
                              debug = True)