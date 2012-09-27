import utils, models, constants
from google.appengine.ext import db
import webapp2
import datetime, logging

class SuperHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return utils.render_str(template, **params)

    def render(self, template, **params):
        self.write(self.render_str(template, **params))

class MainpageHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        username = 'Anon'
        salutation = 'Comrade'
        
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = validate_user(userid)
                if user:
                    username = user.realname
                    salutation = user.salutation
                    
        self.render('mainpage.html', username = username,
                                     salutation = salutation)

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
        
        new_user = ''
        
        # Check mandatory stuffs
        if username:
            valid = constants.username_re.match(username)
            if valid:
                names = db.GqlQuery('select * from UserModel where username = :1 limit 1', username)
                names = list(names)
                if len(names) > 0:
                    username_error = 'This username is taken!'
                    error = True
                else:
                    valid_pw = constants.password_re.match(password)
                    if valid_pw:
                        if password == verify:
                            new_user = models.UserModel(username   = username,
                                                        hashedpw   = utils.securify_password(username, password),
                                                        nameday    = datetime.datetime.now(),
                                                        salutation = 'Comrade',
                                                        realname   = username,
                                                        last_seen  = datetime.datetime.now(),
                                                        timezone   = 8.0,
                                                        currency   = 'SGD')
                        else:
                            verification_error = 'Passwords do not match!'
                            error = True
                    else:
                        password_error = 'This is an invalid password!'
                        error = True
            else:
                username_error = 'This is an invalid username!'
                error = True
            
            # Check optional stuffs
            if not error and new_user:
                if email:
                    valid_email = constants.email_re.match(email)
                    if valid_email:
                        new_user.email = email
                    else:
                        email_error = 'This is an invalid email!'
                        error = True

        if error:
            self.render('signuppage.html', username = username,
                                           email = email,
                                           username_error = username_error,
                                           password_error = password_error,
                                           verification_error = verification_error,
                                           email_error = email_error)
        else:
            new_user.put()
            userid = str(new_user.key().id())
            self.response.headers.add_header('Set-Cookie', 'userid=%s; Path=/' % utils.securify_cookie(userid))
            self.redirect('/') ### move to profile (or panel)
            
class LoginHandler(SuperHandler):
    def get(self):
        self.render('loginpage.html')
        
    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        error = False
        
        if username and password:
            user = db.GqlQuery('select * from UserModel where username = :1 limit 1', username)
            user = list(user)
            logging.error('hit database')
            if len(user) > 0:
                logging.error('user found')
                user = user[0]
                if utils.verify_password(username, password, user.hashedpw):
                    userid = str(user.key().id())
                    self.response.headers.add_header('Set-Cookie', 'userid=%s; Path=/' % utils.securify_cookie(userid))
                    self.redirect('/')
                else:
                    error = True
                    error_message = 'Invalid username or password'
            else:
                error = True
                error_message = 'No such user, create one?'
        else:
            error = True
            error_message = 'You must fill both fields!'
            
        if error:
            self.render('loginpage.html', error_message = error_message)
            
class LogoutHandler(SuperHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'userid=; Path=/')
        self.redirect('/login')
        
class ProfileHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            user = utils.validate_user(userid)
            if user:
                self.render('profilepage.html', user = user)
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            user = utils.validate_user(userid)
            if user:
                new_salutation = self.request.get('salutation')
                new_realname = self.request.get('realname')
                new_timezone = self.request.get('timezone')
                new_currency = self.request.get('currency')
                new_email    = self.request.get('email')
                
                updated = False
                
                if new_salutation != user.salutation:
                    user.salutation = new_salutation
                    updated = True
                if new_realname != user.realname:
                    user.realname = new_realname
                    updated = True
                if new_timezone != user.timezone:
                    user.timezone = float(new_timezone)
                    updated = True
                if new_currency != user.currency:
                    user.currency = new_currency
                    updated = True
                if new_email != user.email and constants.email_re.match(new_email):
                    user.email = new_email
                    updated = True
                    
                if updated:
                    user.last_seen = datetime.datetime.now()
                    user.put()
                    self.redirect('/') ### move to panel
                else:
                    self.redirect('/') ### move to panel
            
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')

class PostActivityModel(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    activity_name = self.request.get('activity_name')
                    activity_day  = self.request.get('activity_date')
                    activity_time = self.request.get('activity_time')

                    if activity_name and activity_day and activity_name:
                        try:
                            h, m = activity_time.split(':')
                            h = int(h)
                            m = int(m)

                            Y, M, D = activity_day.split('/')
                            Y = int(Y)
                            M = int(M)
                            D = int(D)

                            new_activity = models.ActivityModel(userid = userid,
                                                                name   = activity_name,
                                                                when   = datetime.datetime(Y, M, D, h, m) - datetime.timedelta(hours = user.timezone),
                            user.last_seen = datetime.datetime.now()
                            new_activity.put()
                        except:
                            self.redirect('/panel')

                    else:
                        self.redirect('/panel')
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')