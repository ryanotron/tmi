import webapp2, jinja2
import os, re, random, datetime, hashlib, logging
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
    last_seen = db.DateTimeProperty()
    timezone  = db.FloatProperty()
    currency  = db.StringProperty()

class ActivityModel(db.Model):
    name = db.StringProperty(required = True)
    start = db.DateTimeProperty(required = True)
    end = db.DateTimeProperty(required = True)
    userid = db.StringProperty(required = True)
    
class EventModel(db.Model):
    name = db.StringProperty(required = True)
    when = db.DateTimeProperty(required = True)
    userid = db.StringProperty(required = True)
    
class CommuteModel(db.Model):
    origin = db.StringProperty(required = True)
    destination = db.StringProperty(required = True)
    start = db.DateTimeProperty(required = True)
    end = db.DateTimeProperty(required = True)
    userid = db.StringProperty(required = True)
    
class ExpenseModel(db.Model):
    name = db.StringProperty(required = True)
    category = db.StringProperty()
    amount = db.FloatProperty()
    when = db.DateTimeProperty()
    userid = db.StringProperty(required = True)

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
                self.redirect('/login')
        else:
            self.redirect('/login')
            
class ProfileHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = verify_cookie(userid)
            if userid:
                key = db.Key.from_path('UserModel', int(userid))
                user = db.get(key)
                self.render('profilepage.html', username = user.username,
                                                timezone = user.timezone,
                                                currency = user.currency,
                                                email    = user.email)
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = verify_cookie(userid)
            if userid:
                key = db.Key.from_path('UserModel', int(userid))
                user = db.get(key)
                new_timezone = self.request.get('timezone')
                new_currency = self.request.get('currency')
                
                changed = False
                
                if new_timezone and new_timezone != user.timezone:
                    user.timezone = new_timezone
                    changed = True
                    
                if new_currency and new_currency != user.currency:
                    user.currency = new_currency
                    changed = True
                    
                if changed:
                    user.put()
                    
                self.render('profilepage.html', username = user.username,
                                                timezone = user.timezone,
                                                currency = user.currency,
                                                email    = user.email)
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
        
class ActivityHandler(SuperHandler):
    def post(self):
        act_name = self.request.get('act_name')
        act_start_h = self.request.get('act_start_h')
        act_start_m = self.request.get('act_start_m')
        act_finish_h = self.request.get('act_finish_h')
        act_finish_m = self.request.get('act_finish_m')
        act_duration = self.request.get('act_duration')
        
        userid = self.request.cookies.get('userid')
        if userid:
            userid = verify_cookie(userid)
        else:
            self.redirect('/login')
        
        activity = ActivityModel(name   = act_name,
                                 start  = datetime.datetime.now(),
                                 end    = datetime.datetime.now(),
                                 userid = userid)
        
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
        
class CommuteHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = verify_cookie(userid)
        else:
            self.redirect('/login')
            
        user = db.Key.from_path('UserModel', int(userid))
        user = db.get(user)
        origin = self.request.get('origin')
        destination = self.request.get('destination')
        com_start_h = self.request.get('com_start_h')
        com_start_m = self.request.get('com_start_m')
        com_finish_h = self.request.get('com_finish_h')
        com_finish_m = self.request.get('com_finish_m')
        com_duration = self.request.get('com_duration')
        
        error = False
        
        if not origin or not destination:
            error = True
            self.redirect('/panel')
        
        now = datetime.datetime.now()
        if com_start_h:
            com_start = datetime.datetime(now.year, now.month, now.day, int(com_start_h), int(com_start_m))
            if com_finish_h:
                com_finish = datetime.datetime(now.year, now.month, now.day, int(com_finish_h), int(com_finish_m))
            elif com_duration:
                com_finish = com_start + datetime.timedelta(minutes = float(com_duration))
            else:
                error = True
        elif com_finish_h:
            com_finish = datetime.datetime(now.year, now.month, now.day, int(com_finish_h), int(com_finish_m))
            if com_start_h:
                com_start = datetime.datetime(now.year, now.month, now.day, int(com_start_h), int(com_start_m))
            elif com_duration:
                com_start = com_finish - datetime.timedelta(minutes = float(com_duration))
            else:
                error = True
        else:
            error = True
            
        if not error:
            commute = CommuteModel(userid = userid,
                                   origin = origin,
                                   destination = destination,
                                   start = com_start,
                                   end = com_finish)
            commute.put()
            user.last_seen = datetime.datetime.now()
            user.put()
            self.redirect('/panel')
        else:
            self.redirect('/panel')
            
class EventHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = verify_cookie(userid)
            if not userid:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
        event_name = self.request.get('event_name')
        event_when_h = self.request.get('event_when_h')
        event_when_m = self.request.get('event_when_m')
        
        if not event_name or not event_when_h or not event_when_m:
            self.redirect('/panel')
        else:
            user = db.Key.from_path('UserModel', int(userid))
            if user:
                user = db.get(user)
                now = datetime.datetime.now()
                event_when = datetime.datetime(now.year, now.month, now.day, int(event_when_h), int(event_when_m))
                new_event = EventModel(name = event_name,
                                       when = event_when,
                                       userid = userid)
                new_event.put()
                user.last_seen = datetime.datetime.now()
                user.put()
                self.redirect('/panel')
            else:
                self.redirect('/login')

class UserpageHandler(SuperHandler):
    def get(self, username):
        users = db.GqlQuery('select * from UserModel where username = \'%s\' limit 1' % username)
        if users:
            user = list(users)[0]
            inactivity = (datetime.datetime.now() - user.last_seen).seconds / 60
            
            alive_message = ''
            if inactivity < 10: #ten minutes
                alive_message = 'Most probably'
            elif inactivity < 60: #one hour
                alive_message = 'Assume yes'
            elif inactivity < 60 * 24: #one day
                alive_message = 'Little reason to think otherwise'
            elif inactivity < 60 * 24 * 7: #one week
                alive_message = 'Perhaps'
            elif inactivity < 60 * 24 * 7 * 2: #two weeks
                alive_message = 'Let\'s hope so'
            else:
                alive_message = 'Unknown. Did Comrade %s left a goodbye note to anyone?' % user.username
            userid = str(user.key().id())
            commutes = db.GqlQuery('select * from CommuteModel where userid = \'%s\'' % userid)
            events   = db.GqlQuery('select * from EventModel where userid = \'%s\'' % userid)
            
            commute = list(commutes)[0]
            event   = list(events)[0]
            
            self.render('userpage.html', username = username,
                                         origin = commute.origin,
                                         destination = commute.destination,
                                         travel_start = commute.start,
                                         travel_finish = commute.end,
                                         travel_duration = (commute.end - commute.start).seconds / 60,
                                         event_name = event.name,
                                         event_time = event.when,
                                         alive_message = alive_message)
        else:
            self.redirect('/signup')
            
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
            
class LoginHandler(SuperHandler):
    def get(self):
        self.render('loginpage.html')
        
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        
        error = False
        error_message = 'Invalid login, try again!'
        
        if username:
            users = db.GqlQuery('select * from UserModel where username = \'%s\' limit 1' % username)
            user = list(users)[0]
            
            if verify_password(username, password, user.hashedpw):
                userid = str(user.key().id())
                self.response.headers.add_header('Set-Cookie', 'userid=%s; Path=/' % securify_cookie(userid))
                self.redirect('/panel')
            else:
                error = True
        else:
            error = True
            
        if error:
            self.render('loginpage.html', error_message = error_message)
            
class LogoutHandler(SuperHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'userid=; Path=/')
        self.redirect('/login')
            
userpage_re = r'([a-zA-Z_-]+)/?'
app = webapp2.WSGIApplication([('/', MainPageHandler),
                               ('/panel/?', PanelHandler),
                               ('/activity/?', ActivityHandler),
                               ('/commute/?', CommuteHandler),
                               ('/signup/?', SignupHandler),
                               ('/login/?', LoginHandler),
                               ('/logout/?', LogoutHandler),
                               ('/event/?', EventHandler),
                               ('/comrade/' + userpage_re + '/?profile/?', ProfileHandler),
                               ('/comrade/' + userpage_re, UserpageHandler)],
                              debug = True)