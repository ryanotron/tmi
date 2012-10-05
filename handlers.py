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
                user = utils.validate_user(userid)
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
            self.redirect('/panel')
            
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
                    self.redirect('/panel')
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
                    self.redirect('/panel')
                else:
                    self.redirect('/panel')
            
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')

class PostActivityHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    activity_name = self.request.get('activity_name')
                    activity_day  = self.request.get('activity_day')
                    activity_time = self.request.get('activity_time')

                    if activity_name and activity_day:
                        try:
                            h, m = activity_time.split(':')
                            h = int(h)
                            m = int(m)
                            logging.error('split hours')

                            D, M, Y = activity_day.split('/')
                            Y = int(Y)
                            M = int(M)
                            D = int(D)
                            logging.error('split day')

                            new_activity = models.ActivityModel(userid = userid,
                                                                name   = activity_name,
                                                                when   = datetime.datetime(Y, M, D, h, m) - datetime.timedelta(hours = user.timezone))
                                                                
                            user.last_seen = datetime.datetime.now()
                            user.put()
                            new_activity.put()
                            self.redirect('/panel')
                        except:
                            logging.error('exception occured')
                            self.redirect('/panel')

                    else:
                        self.redirect('/panel')
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')

class PostTimedActivityHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    act_name       = self.request.get('act_name')
                    act_start_day  = self.request.get('act_start_day')
                    act_start_time = self.request.get('act_start_time')
                    act_end_day    = self.request.get('act_end_day')
                    act_end_time   = self.request.get('act_end_time')
                    act_duration   = self.request.get('act_duration')
                    
                    if act_name:
                        if act_start_time:
                            try:
                                D, M, Y = [int(elem) for elem in act_start_day.split('/')]
                                h, m    = [int(elem) for elem in act_start_time.split(':')]
                                act_start_time = datetime.datetime(Y, M, D, h, m)                                
                            except:
                                self.redirect('/panel')
                                
                            if act_end_time:
                                try:
                                    D, M, Y = [int(elem) for elem in act_end_day.split('/')]
                                    h, m    = [int(elem) for elem in act_end_time.split(':')]
                                    act_end_time = datetime.datetime(Y, M, D, h, m)
                                except:
                                    self.redirect('/panel')
                                
                            elif act_duration:
                                try:
                                    act_end_time = act_start_time + datetime.timedelta(minutes = float(act_duration))
                                except:
                                    self.redirect('/panel')
                                    
                            else:
                                self.redirect('/panel')
                        elif act_end_time:
                            try:
                                D, M, Y = [int(elem) for elem in act_end_day.split('/')]
                                h, m    = [int(elem) for elem in act_end_time.split(':')]
                                act_end_time = datetime.datetime(Y, M, D, h, m)
                            except:
                                self.redirect('/panel')
                            
                            if act_duration:
                                try:
                                    act_start_time = act_end_time - datetime.timedelta(hours = float(act_duration))
                                except:
                                    self.redirect('/panel')
                            else:
                                self.redirect('/panel')
                                
                        else:
                            self.redirect('/panel')
                            
                        new_timed_act = models.TimedActivityModel(userid = userid,
                                                                  name   = act_name,
                                                                  start  = act_start_time - datetime.timedelta(hours = user.timezone),
                                                                  end    = act_end_time - datetime.timedelta(hours = user.timezone))
                        new_timed_act.put()
                        user.last_seen = datetime.datetime.now()
                        user.put()
                        self.redirect('/panel')
                    else:
                        self.redirect('/panel')
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
class PostExpenseHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    exp_name     = self.request.get('exp_name')
                    exp_category = self.request.get('exp_category')
                    exp_amount   = self.request.get('exp_amount')
                    exp_currency = self.request.get('exp_currency')
                    exp_when     = self.request.get('exp_when')
                    
                    if exp_name and exp_amount:
                        try:
                            if not exp_when:
                                exp_when = datetime.datetime.today()
                            D, M, Y = [int(elem) for elem in exp_when.split('/')]
                            
                            if not exp_currency:
                                exp_currency = user.currency
                                
                            new_expense = models.ExpenseModel(userid = userid,
                                                              name = exp_name,
                                                              category = exp_category,
                                                              amount = exp_amount,
                                                              currency = exp_currency,
                                                              when = datetime.datetime(Y, M, D))
                                                              
                            new_expense.put()
                            user.last_seen = datetime.datetime.now()
                            user.put()
                            self.redirect('/panel')
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
            
class PostTravelHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    trv_origin      = self.request.get('trv_origin')
                    trv_destination = self.request.get('trv_destination')
                    trv_start_day   = self.request.get('trv_start_day')
                    trv_start_time  = self.request.get('trv_start_time')
                    trv_finish_day  = self.request.get('trv_finish_day')
                    trv_finish_time = self.request.get('trv_finish_time')
                    trv_duration    = self.request.get('trv_duration') # how granular should we be? I usually use minutes in my manual log
                    
                    if trv_origin and trv_destination:
                        # two out of three are needed from trv_start_time, trv_finish_time, and trv_duration.
                        # *_time will be left blank in the form, while *_day will default to today (user's timezone),
                        # so it makes sense to check *_time instead of *_day
                        if trv_start_time:
                            try:
                                D, M, Y = [int(elem) for elem in trv_start_day.split('/')]
                                h, m    = [int(elem) for elem in trv_start_time.split(':')]
                                trv_start_time = datetime.datetime(Y, M, D, h, m)
                            except:
                                self.redirect('/panel')
                            
                            if trv_finish_time:
                                try:
                                    D, M, Y = [int(elem) for elem in trv_finish_day.split('/')]
                                    h, m    = [int(elem) for elem in trv_finish_time.split(':')]
                                    trv_finish_time = datetime.datetime(Y, M, D, h, m)
                                except:
                                    self.redirect('/panel')
                            elif trv_duration:
                                trv_finish_time = trv_start_time + datetime.timedelta(minutes = float(trv_duration))
                            else:
                                self.redirect('/panel')
                        elif trv_finish_time:
                            try:
                                D, M, Y = [int(elem) for elem in trv_finish_day.split('/')]
                                h, m    = [int(elem) for elem in trv_finish_time.split(':')]
                                trv_finish_time = datetime.datetime(Y, M, D, h, m)
                            except:
                                self.redirect('/panel')
                            
                            if trv_duration:
                                trv_start_time = trc_finish_time - datetime.timedelta(minutes = float(trv_duration))
                            else:
                                self.redirect('/panel')
                        else:
                            self.redirect('/panel')
                            
                        new_travel = models.TravelModel(userid      = userid,
                                                        origin      = trv_origin,
                                                        destination = trv_destination,
                                                        whenstart   = trv_start_time - datetime.timedelta(user.timezone),
                                                        whenfinish  = trv_finish_time - datetime.timedelta(user.timezone))
                                                        
                        new_travel.put()
                        user.last_seen = datetime.datetime.now()
                        user.put()
                        self.redirect('/panel')
                    else:
                        self.redirect('/panel')
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
class PostMealHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    meal_menu     = self.request.get('meal_menu')
                    meal_day      = self.request.get('meal_day')
                    meal_time     = self.request.get('meal_time')
                    meal_place    = self.request.get('meal_place')
                    meal_category = self.request.get('meal_category')
                    
                    if meal_menu and meal_time:
                        try:
                            D, M, Y = [int(elem) for elem in meal_day.split('/')]
                            h, m    = [int(elem) for elem in meal_time.split(':')]
                            meal_time = datetime.datetime(Y, M, D, h, m) - datetime.timedelta(user.timezone)
                            
                            new_meal = models.MealModel(userid   = userid,
                                                        when     = meal_time,
                                                        menu     = meal_menu,
                                                        place    = meal_place,
                                                        category = meal_category)
                            new_meal.put()
                            user.last_seen = datetime.datetime.now()
                            user.put()
                            self.redirect('/panel')
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
            
class PostUserMessageHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    message = self.request.get('user_message')
                    if message:
                        new_message = models.UserMessageModel(userid  = userid,
                                                              message = message,
                                                              when    = datetime.datetime.now())
                        new_message.put()
                        user.last_seen = datetime.datetime.now()
                        user.put()
                        self.redirect('/panel')
                    else:
                        self.redirect('/panel')
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
class PostGuestMessageHandler(SuperHandler):
    def post(self):
        guest_name = self.request.get('guest_name')
        message    = self.request.get('guest_message')
        userid     = self.request.get('userid')
        
        if not guest_name:
            guest_name = 'anon'
        
        if guest_name and message and userid:
            new_message = models.GuestMessageModel(userid    = userid,
                                                   guestname = guest_name,
                                                   message   = message,
                                                   when      = datetime.datetime.now())
            new_message.put()
            self.redirect(self.request.referer)
        else:
            self.redirect(self.request.referer)
            
class PanelHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    self.render('panelpage.html', user = user)
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            