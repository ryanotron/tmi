import utils, models, constants, stats
from google.appengine.ext import db
from google.appengine.api import images
import webapp2
import datetime, logging
import json

def require_login(fn):
    def new_fn(self, *args, **kwargs):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            #logging.error('login check successful')
            fn(self, user, *args, **kwargs)
        else:
            #logging.error('not logged in!')
            self.redirect('/login')
    return new_fn
    
def require_sameuser(fn):
    @require_login
    def new_fn(self, user, username, *args, **kwargs):
        if user.username == username:
            fn(self, user, *args, **kwargs)
        else:
            logging.error('mismatch!')
            self.redirect('/login')
    return new_fn

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
        betakey  = self.request.get('betakey')
        
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
                            if not betakey:
                                error = True
                                betakey_error = 'Fill in your beta key!'
                            else:
                                dbkey = db.GqlQuery('select * from BetaKeyModel where keystring = :1 limit 1', betakey)
                                if len(list(dbkey)) > 0: 
                                    dbkey = list(dbkey)[0]
                                    if not dbkey.used:
                                        dbkey.used = True
                                        dbkey.whenused = datetime.datetime.utcnow()
                                        dbkey.put()
                                        new_user = models.UserModel(username   = username,
                                                                    hashedpw   = utils.securify_password(username, password),
                                                                    nameday    = datetime.datetime.utcnow(),
                                                                    salutation = 'Comrade',
                                                                    realname   = username,
                                                                    last_seen  = datetime.datetime.utcnow(),
                                                                    timezone   = 8.0,
                                                                    currency   = 'SGD',
                                                                    nom_pronoun = 'it',
                                                                    pos_determi = 'its',
                                                                    pos_pronoun = 'its')
                                    else:
                                        betakey_error = 'this key is already used!'
                                        error = True
                                else:
                                    betakey_error = 'invalid beta key!'
                                    error = True
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
                                           email_error = email_error,
                                           betakey_error = betakey_error)
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
            #logging.error('hit database')
            if len(user) > 0:
                #logging.error('user found')
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
                new_gender   = self.request.get('gender')
                new_photo    = self.request.get('photo')
                
                new_sm_uname = self.request.get('sm_uname')
                new_sm_site  = self.request.get('sm_site')
                new_sm_url   = self.request.get('sm_url')
                new_sm_upage = self.request.get('sm_upage')
                
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
                if new_gender != user.gender:
                    user.gender = new_gender
                    if new_gender == 'male':
                        user.pos_pronoun = 'his'
                        user.pos_determi = 'his'
                        user.nom_pronoun = 'he'
                        user.acc_pronoun = 'him'
                    elif new_gender == 'female':
                        user.pos_pronoun = 'her'
                        user.pos_determi = 'hers'
                        user.nom_pronoun = 'she'
                        user.acc_pronoun = 'her'
                    else:
                        user.pos_pronoun = 'its'
                        user.pos_determi = 'its'
                        user.nom_pronoun = 'it'
                        user.acc_pronoun = 'it'
                    updated = True

                if new_photo:
                    new_photo = images.resize(new_photo, height = 150)
                    new_photo = models.ImageModel(userid = userid,
                                                  uploaded = datetime.datetime.utcnow(),
                                                  image = db.Blob(new_photo),
                                                  category = 'profile_img')
                    new_photo.put()
                    img_key = new_photo.key()
                    user.photo_key = str(img_key)
                    updated = True
                    
                if new_sm_uname and new_sm_site:
                    new_sm = models.SocialMediaModel(userid = userid,
                                                     sm_sitename = new_sm_site,
                                                     sm_username = new_sm_uname)
                    if new_sm_url:
                        new_sm.sm_siteurl = new_sm_url
                    elif constants.social_media_dictionary.has_key(new_sm_site):
                        new_sm.sm_siteurl = constants.social_media_dictionary[new_sm_site]
                        
                    if new_sm_upage:
                        new_sm.sm_userpage = new_sm_upage
                        
                    new_sm.put()
                    updated = True
                    
                if updated:
                    user.last_seen = datetime.datetime.utcnow()
                    user.put()
                    self.redirect('/panel')
                else:
                    self.redirect('/panel')
            
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')

class ImageHandler(SuperHandler):
    def get(self):
        image = db.get(self.request.get('img_key'))
        #user = db.get(self.request.get('img_key'))
        if image.image:
            self.response.headers['Content-Type'] = 'image/png'
            self.response.out.write(image.image)
        else:
            logging.error('image not found')
            
class PostImageHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            cat = self.request.get('img_category')
            img = self.request.get('imagefile')
            if img:
                img = images.resize(img, height = 150)
                img = models.ImageModel(userid = userid,
                                        image = img,
                                        uploaded = datetime.datetime.utcnow(),
                                        category = cat)
                img.put()
                imgkey = str(img.key())
                user.photo_key = imgkey
                user.last_seen = datetime.datetime.utcnow()
                user.put()
                self.redirect('/panel')
            else:
                self.redirect('/panel')
        else:
            self.redirect('/login')
            
class ImageGalleryHandler(SuperHandler):
    def get(self, username):
        subject = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        if subject:
            subject = subject[0]
            subject_id = str(subject.key().id())
            images = list(db.GqlQuery('select * from ImageModel where userid = :1', subject_id))
            catset = set([im.category for im in images])
            imdict = {}
            imdict['unspecified'] = [im for im in images if not im.category]
            for cat in catset:
                imdict[cat] = [im for im in images if im.category == cat]
            #logging.error(str(imdict))
            self.render('imagegallerypage.html', user = subject,
                                                 imdict = imdict)
        else:
            self.redirect('/') #no such user

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
                    timezone      = self.request.get('timezone')

                    if activity_name and activity_day:
                        try:
                            h, m = activity_time.split(':')
                            h = int(h)
                            m = int(m)
                            #logging.error('split hours')

                            D, M, Y = activity_day.split('/')
                            Y = int(Y)
                            M = int(M)
                            D = int(D)
                            #logging.error('split day')

                            if timezone:
                                try:
                                    timezone = float(timezone)
                                except:
                                    timezone = user.timezone
                                    logging.error('timezone conversion error, falling back to user timezone')
                            else:
                                timezone = user.timezone
                                logging.error('timezone unspecified, falling back to user timezone')

                            new_activity = models.ActivityModel(userid = userid,
                                                                name   = activity_name,
                                                                when   = datetime.datetime(Y, M, D, h, m) - datetime.timedelta(hours = timezone),
                                                                timezone = timezone)
                                                                
                            newconf = utils.update_config(json.loads(user.confstring), 'activities', activity_name)
                            if newconf:
                                user.confstring = json.dumps(newconf)
                                                                
                            user.last_seen = datetime.datetime.utcnow()
                            user.put()
                            new_activity.put()
                            self.redirect('/panel')
                        except:
                            #logging.error('exception occured')
                            self.redirect('/panel')

                    else:
                        self.redirect('/panel')
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')

class InsPostActivityHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            act_name = self.request.get('activity_name')
            #logging.error('posted '+act_name+' from instant, with new user verification method')
            new_act = models.ActivityModel(userid = userid,
                                           name   = act_name,
                                           when   = datetime.datetime.utcnow(),
                                           timezone = user.timezone)
            new_act.put()
            user.last_seen = datetime.datetime.utcnow()
            user.put()
            self.redirect('/panel')
        else:
            self.redirect('/login')

class PostBatchActivityHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    activities = self.request.get('activities')
                    if activities:
                        activities = activities.split('\n')
                        for activity in activities:
                            activity = [elem.strip() for elem in activity.split('\t')]
                            if len(activity) >= 2:
                                name = activity[0]
                                when = activity[1]
                                #logging.error('when is ' + when)
                                try:
                                    whenmatch = constants.datetime_re.match(when)
                                    #logging.error(str(whenmatch))
                                    D,M,Y,h,m = [int(elem) for elem in whenmatch.groups()]
                                    when = datetime.datetime(Y, M, D, h, m)
                                    #logging.error(when)
                                except:
                                    #logging.error('error parsing datetime')
                                    self.redirect('/panel')

                                new_act = models.ActivityModel(userid = userid,
                                                               name = name,
                                                               when = when - datetime.timedelta(hours = user.timezone),
                                                               timezone = user.timezone)
                                new_act.put()
                                new_conf = utils.update_config(json.loads(user.confstring), 'activities', name)
                                if new_conf:
                                    user.confstring = json.dumps(new_conf)

                                user.last_seen = datetime.datetime.now()
                                user.put()
                            else:
                                #logging.error('wrong format')
                                self.redirect('/panel')
                    else:
                        self.redirect('/panel')
                else:
                    #logging.error('failed to validated user')
                    self.redirect('/login')
            else:
                #logging.error('failed to verify cookie')
                self.redirect('/login')
        else:
            #logging.error('failed to find cookie')
            self.redirect('/login')
            
class PostTimedActivityHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            act_name       = self.request.get('act_name')
            act_start_day  = self.request.get('act_start_day')
            act_start_time = self.request.get('act_start_time')
            act_end_day    = self.request.get('act_end_day')
            act_end_time   = self.request.get('act_end_time')
            act_duration   = self.request.get('act_duration')
            timezone       = self.request.get('timezone')
            error = False
            
            if act_name:
                if act_start_time:
                    try:
                        D, M, Y = [int(elem) for elem in act_start_day.split('/')]
                        h, m    = [int(elem) for elem in act_start_time.split(':')]
                        act_start_time = datetime.datetime(Y, M, D, h, m)                                
                    except:
                        error = True
                        self.redirect('/panel')
                        
                    if act_end_time:
                        try:
                            D, M, Y = [int(elem) for elem in act_end_day.split('/')]
                            h, m    = [int(elem) for elem in act_end_time.split(':')]
                            act_end_time = datetime.datetime(Y, M, D, h, m)
                        except:
                            error = True
                            self.redirect('/panel')
                    elif act_duration:
                        try:
                            act_end_time = act_start_time + datetime.timedelta(minutes = float(act_duration))
                        except:
                            error = True
                            self.redirect('/panel')
                    else:
                        self.redirect('/panel')
                elif act_end_time:
                    try:
                        D, M, Y = [int(elem) for elem in act_end_day.split('/')]
                        h, m    = [int(elem) for elem in act_end_time.split(':')]
                        act_end_time = datetime.datetime(Y, M, D, h, m)
                    except:
                        error = True
                        self.redirect('/panel')
                    
                    if act_duration:
                        try:
                            act_start_time = act_end_time - datetime.timedelta(hours = float(act_duration))
                        except:
                            error = True
                            self.redirect('/panel')
                    else:
                        error = True
                        self.redirect('/panel')
                else:
                    error = True
                    self.redirect('/panel')

                if not error:
                    if timezone:
                        try:
                            timezone = float(timezone)
                        except:
                            timezone = user.timezone
                    else:
                        timezone = user.timezone
                    new_timed_act = models.TimedActivityModel(userid = userid,
                                                              name   = act_name,
                                                              start  = act_start_time - datetime.timedelta(hours = timezone),
                                                              end    = act_end_time - datetime.timedelta(hours = timezone),
                                                              timezone = timezone)
                    new_timed_act.put()
                    
                    newconf = utils.update_config(json.loads(user.confstring), 'timed_activities', act_name)
                    if newconf:
                        user.confstring = json.dumps(newconf)
                        
                    user.last_seen = datetime.datetime.utcnow()
                    user.put()
                    self.redirect('/panel')
                else:
                    self.redirect('/panel')
            else:
                self.redirect('/panel')
        else:
            self.redirect('/login')

class PostBatchTimedActivityHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    activities = self.request.get('batchactivities')
                    if activities:
                        activities = activities.split('\n')
                        for act in activities:
                            act = [elem.strip() for elem in act.split('\t')]
                            try:
                                name = act[0]

                                #logging.error('begin parsing start time')
                                start = act[1]
                                #logging.error('start is '+ start)
                                startmatch = constants.datetime_re.match(start)
                                #logging.error(str(startmatch))
                                D,M,Y,h,m = [int(elem) for elem in startmatch.groups()]
                                start = datetime.datetime(Y, M, D, h, m)

                                #logging.error('begin parsing end time')
                                end = act[2]
                                #logging.error('end is ' + end)
                                endmatch = constants.datetime_re.match(end)
                                #logging.error(str(endmatch))
                                D,M,Y,h,m = [int(elem) for elem in endmatch.groups()]
                                #logging.error(str([D,M,Y,h,m]))
                                end = datetime.datetime(Y, M, D, h, m)
                                #logging.error(end)

                                new_act = models.TimedActivityModel(userid = userid,
                                                                name = name,
                                                                start = start - datetime.timedelta(hours = user.timezone),
                                                                end = end - datetime.timedelta(hours = user.timezone),
                                                                timezone = user.timezone)
                                new_act.put()
                                
                                new_conf = utils.update_config(json.loads(user.confstring), 'timed_activities', name)
                                if new_conf:
                                    user.confstring = json.dumps(new_conf)
                                    
                                #logging.error('put act into database')
                                user.last_seen = datetime.datetime.utcnow()
                                user.put()
                                #logging.error('updated user in database')
                            except:
                                #logging.error('error!' + str(act))
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
                                
                            ##logging.error('making new expense object')
                            new_expense = models.ExpenseModel(userid = userid,
                                                              name = exp_name,
                                                              category = exp_category,
                                                              amount = float(exp_amount),
                                                              currency = exp_currency,
                                                              when = datetime.datetime(Y, M, D))
                            #logging.error('new expense object created')
                            new_expense.put()
                            userconf = json.loads(user.confstring)
                            conf_updated = False
                            if not userconf.has_key('expense_categories'):
                                userconf['expense_categories'] = [exp_category]
                                conf_updated = True
                            else:
                                if not exp_category in userconf['expense_categories']:
                                    userconf['expense_categories'].append(exp_category)
                                    conf_updated = True
                                    
                            if conf_updated:
                                user.confstring = json.dumps(userconf)
                            
                            user.last_seen = datetime.datetime.utcnow()
                            user.put()
                            self.redirect('/panel')
                        except:
                            #logging.error('failed date conversion')
                            self.redirect('/panel')
                    else:
                        #logging.error('amount or name missing')
                        self.redirect('/panel')
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')

class PostBatchExpenseHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            expenses = self.request.get('batchexpense')
            #logging.error(expenses)
            if expenses:
                expenses = expenses.split('\n')
                for elem in expenses:
                    #logging.error(elem)
                    expense = constants.batchexpense_re.match(elem)
                    logging.error(elem)
                    logging.error(expense)
                    if expense:
                        logging.error(expense.groups())
                        new_expense = models.ExpenseModel(userid   = str(userid),
                                                          name     = expense.group('name'),
                                                          category = expense.group('cat'),
                                                          amount   = float(expense.group('amount')),
                                                          when     = utils.str_to_datetime(expense.group('when')),
                                                          currency = user.currency)
                        #logging.error(expense.groups())
                        new_expense.put()
                        new_conf = utils.update_config(json.loads(user.confstring), 'expense_categories', expense.group('cat'))
                        if new_conf:
                            user.confstring = json.dumps(new_conf)
                        user.last_seen = datetime.datetime.utcnow()
                        user.put()
                        self.redirect('/panel')
                self.redirect('/panel')
            else:
                self.redirect('/panel')
        else:
            self.redirect('login')

class CategorizeExpenseHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            public_categories = self.request.get('public_category', allow_multiple = True)
            public_categories = [cat.strip() for cat in public_categories]
            userconf = {}
            try:
                userconf = json.loads(user.confstring)
            except:
                userconf = {}
                
            userconf['public_expense_categories'] = public_categories
            user.confstring = json.dumps(userconf)
            user.last_seen = datetime.datetime.now()
            user.put()
                
            for cat in public_categories:
                logging.error(cat.strip())
            self.redirect('/panel')
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
                    start_timezone  = self.request.get('start_timezone')
                    trv_finish_day  = self.request.get('trv_finish_day')
                    trv_finish_time = self.request.get('trv_finish_time')
                    finish_timezone = self.request.get('finish_timezone')
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
                                start_timezone = float(start_timezone)
                            except:
                                self.redirect('/panel')
                            
                            if trv_finish_time:
                                try:
                                    D, M, Y = [int(elem) for elem in trv_finish_day.split('/')]
                                    h, m    = [int(elem) for elem in trv_finish_time.split(':')]
                                    trv_finish_time = datetime.datetime(Y, M, D, h, m)
                                    finish_timezone = float(finish_timezone)
                                except:
                                    self.redirect('/panel')
                            elif trv_duration:
                                trv_finish_time = trv_start_time + datetime.timedelta(minutes = float(trv_duration))
                                finish_timezone = start_timezone
                            else:
                                self.redirect('/panel')
                        elif trv_finish_time:
                            try:
                                D, M, Y = [int(elem) for elem in trv_finish_day.split('/')]
                                h, m    = [int(elem) for elem in trv_finish_time.split(':')]
                                trv_finish_time = datetime.datetime(Y, M, D, h, m)
                                finish_timezone = float(finish_timezone)
                            except:
                                self.redirect('/panel')
                            
                            if trv_duration:
                                trv_start_time = trv_finish_time - datetime.timedelta(minutes = float(trv_duration))
                                start_timezone = finish_timezone
                            else:
                                self.redirect('/panel')
                        else:
                            self.redirect('/panel')
                            
                        new_travel = models.TravelModel(userid      = userid,
                                                        origin      = trv_origin,
                                                        destination = trv_destination,
                                                        whenstart   = trv_start_time - datetime.timedelta(start_timezone),
                                                        start_timezone = start_timezone,
                                                        whenfinish  = trv_finish_time - datetime.timedelta(finish_timezone),
                                                        finish_timezone = finish_timezone)
                                                        
                        new_travel.put()
                        
                        userconf = json.loads(user.confstring)
                        config_updated = False
                        if userconf.has_key('places'):
                            if not trv_origin in userconf['places']:
                                userconf['places'].append(trv_origin)
                                config_updated = True
                            if not trv_destination in userconf['places']:
                                userconf['places'].append(trv_destination)
                                config_updated = True
                        else:
                            userconf['places'] = [trv_origin, trv_destination]
                            config_updated = True
                            
                        if config_updated:
                            user.confstring = json.dumps(userconf)
                                
                        user.last_seen = datetime.datetime.utcnow()
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
        userid, user = utils.verify_user(userid)
        if user:
            meal_menu     = self.request.get('meal_menu')
            meal_day      = self.request.get('meal_day')
            meal_time     = self.request.get('meal_time')
            meal_place    = self.request.get('meal_place')
            meal_category = self.request.get('meal_category')
            meal_cost     = self.request.get('meal_cost')
            meal_currency = self.request.get('meal_currency')
            meal_image    = self.request.get('meal_image')
            timezone      = self.request.get('timezone')

            if meal_menu and meal_time:
                error = False
                if timezone:
                    try:
                        timezone = float(timezone)
                    except:
                        timezone = user.timezone
                else:
                    timezone = user.timezone
                try:
                    D, M, Y = [int(elem) for elem in meal_day.split('/')]
                    h, m    = [int(elem) for elem in meal_time.split(':')]
                    meal_time = datetime.datetime(Y, M, D, h, m) - datetime.timedelta(hours = timezone)

                    new_meal = models.MealModel(userid   = userid,
                                                when     = meal_time,
                                                timezone = timezone,
                                                menu     = meal_menu,
                                                place    = meal_place,
                                                category = meal_category)

                    if meal_image:
                        image = images.resize(meal_image, height = constants.image_height)
                        image = models.ImageModel(userid = userid,
                                                  uploaded = datetime.datetime.utcnow(),
                                                  image = db.Blob(image),
                                                  category = 'meal_img')
                        image.put()
                        image_id = str(image.key())
                        new_meal.image = image_id
                        
                    new_meal.put()
                    if meal_cost:
                        if not meal_currency:
                            meal_currency = user.currency
                        try:
                            meal_cost = float(meal_cost)
                            new_expense = models.ExpenseModel(userid = userid,
                                                                name = meal_category,
                                                                category = 'meal',
                                                                currency = meal_currency,
                                                                amount = meal_cost,
                                                                when = meal_time)
                            new_expense.put()
                        except:
                            pass

                    user.last_seen = datetime.datetime.utcnow()
                    user.put()
                    self.redirect('/panel')
                except:
                    error = True
                    self.redirect('/panel')
                if error:
                    self.redirect('/panel')
            else:
                self.redirect('/panel')
        else:
            self.redirect('/login')
            
class PostBatchMealHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            meals = self.request.get('meals')
           #logging.error('got these:\n'+meals)
            if meals:
                meals = [m for m in meals.split('\n') if m != '']
                for meal in meals:
                    meal = [e.strip() for e in meal.split('\t')]
                    error = False
                    when = meal[0]
                    cat = meal[1]
                    menu = meal[2]
                    try:
                        #logging.error(when)
                        d, m, y, H, M = [int(elem) for elem in constants.datetime_re.match(when).groups()]
                        when = datetime.datetime(y, m, d, H, M) - datetime.timedelta(hours = user.timezone)
                    except:
                        error = True
                        
                    if not error:
                        #logging.error('new meal! '+str(when)+' '+menu)
                        new_meal = models.MealModel(userid = userid, 
                                                    when = when,
                                                    menu = menu,
                                                    category = cat)
                        new_meal.put()
                self.redirect('/panel')
            else:
                self.redirect('/panel')
        else:
            self.redirect('/login')

class PostBookHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            title = self.request.get('title')
            author = self.request.get('author')
            if not author:
                author = 'unknown'
            isbn = self.request.get('isbn')
            doi = self.request.get('doi')
            added = datetime.datetime.utcnow()
            start = self.request.get('start')
            finish = self.request.get('finish')
            active = self.request.get('active')
            image = self.request.get('image')
            if not title:
                self.redirect('/panel')
            else:
                if start:
                    try:
                        D, M, Y = [int(elem) for elem in start.split('/')]
                        start = datetime.datetime(Y, M, D)
                    except:
                       #logging.error('failed parsing datetime')
                        self.redirect('/panel')
                if finish:
                    try:
                        D, M, Y = [int(elem) for elem in finish.split('/')]
                        finish = datetime.datetime(Y, M, D)
                    except:
                       #logging.error('failed parsing datetime')
                        self.redirect('/panel')
                if not start and bool(active):
                    start = datetime.datetime.utcnow()
                        
                new_book = models.BookLibraryModel(userid = userid,
                                                   title = title,
                                                   author = author,
                                                   isbn = isbn,
                                                   doi = doi,
                                                   added = added,
                                                   start = start,
                                                   finish = finish,
                                                   active = bool(active))
                                                   
                if image:
                    image = images.resize(image, height = 150)
                    image = models.ImageModel(userid = userid,
                                              uploaded = datetime.datetime.utcnow(),
                                              image = db.Blob(image),
                                              category = 'book_img')
                    image.put()
                    image_id = str(image.key())
                    new_book.image = image_id
                
                new_book.put()
                user.last_seen = datetime.datetime.utcnow()
                user.put()
                self.redirect('/panel')
        else:
            self.redirect('/login')
            
class PostGameHandler(SuperHandler):
    def post(self):
        userid_cookie = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid_cookie)
        if user:
            title = self.request.get('title')
            platform = self.request.get('platform')
            added = datetime.datetime.utcnow()
            start = self.request.get('start')
            finish = self.request.get('finish')
            active = self.request.get('active')
            image = self.request.get('image')
            
            if not title:
                self.redirect('/panel')
            else:
                if start:
                    try:
                        D, M, Y = [int(elem) for elem in start.split('/')]
                        start = datetime.datetime(Y, M, D)
                    except:
                       #logging.error('failed parsing datetime')
                        self.redirect('/panel')
                if finish:
                    try:
                        D, M, Y = [int(elem) for elem in finish.split('/')]
                        finish = datetime.datetime(Y, M, D)
                    except:
                       #logging.error('failed parsing datetime')
                        self.redirect('/panel')
                if not start and bool(active):
                    start = datetime.datetime.utcnow()
                        
                new_game = models.GameLibraryModel(userid = userid,
                                                   title = title,
                                                   platform = platform,
                                                   added = added,
                                                   start = start,
                                                   finish = finish,
                                                   active = bool(active))
                if image:
                    image = images.resize(image, height = 150)
                    image = models.ImageModel(userid = userid,
                                              uploaded = datetime.datetime.utcnow(),
                                              image = db.Blob(image),
                                              category = 'game_img')
                    image.put()
                    image_key = str(image.key())
                    new_game.image = image_key
                
                new_game.put()
                user.last_seen = datetime.datetime.utcnow()
                user.put()
                self.redirect('/panel')
        else:
            self.redirect('/login')
            
class PostMusicHandler(SuperHandler):
    @require_login
    def post(self, user):
        title = self.request.get('title')
        if title:
            new_music = models.MusicLibraryModel(userid = str(user.key().id()),
                                                 title = title)
            artist = self.request.get('artist')
            if artist:
                new_music.artist = artist
            
            album = self.request.get('album')
            if album:
                new_music.album = album
            
            year = self.request.get('year')
            if year:
                try:
                    new_music.year = int(year)
                except:
                    pass
            
            url = self.request.get('url')
            if url:
                new_music.url = url
                
            new_music.first_report = datetime.datetime.utcnow()
            new_music.last_report = datetime.datetime.utcnow()
            new_music.report_count = 1
            new_music.put()
            
            user.last_seen = datetime.datetime.utcnow()
            user.put()
            self.redirect('/panel')
        else:
            self.redirect('/panel')

class ReportMusicHandler(SuperHandler):
    @require_login
    def post(self, user):
        song = db.get(self.request.get('key'))
        song.report_count += 1
        song.put()
        user.last_seen = datetime.datetime.utcnow()
        user.put()
        self.redirect('/panel')
        
class MusicLibraryHandler(SuperHandler):
    def get(self, username):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        sameuser = False
        if user.username == username:
            sameuser = True
            songs = list(db.GqlQuery('select * from MusicLibraryModel where userid = :1 order by last_report desc', userid))
            self.render('musiclibrarypage.html', user = user,
                                                 songs = songs,
                                                 sameuser = sameuser)
        else:
            user = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
            if len(user) > 0:
                songs = list(db.GqlQuery('select * from MusicLibraryModel where userid = :1 order by last_report desc', str(user.key().id())))
                self.render('musiclibrarypage.html', user = user[0],
                                                     songs = songs,
                                                     sameuser = sameuser)
            else:
                self.response.out.write('User %s does not exist' % username)

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
                                                              when    = datetime.datetime.utcnow())
                        new_message.put()
                        user.last_seen = datetime.datetime.utcnow()
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
                                                   when      = datetime.datetime.utcnow())
            new_message.put()
            self.redirect(self.request.referer)
        else:
            self.redirect(self.request.referer)
            
class PresentActivityHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    activities = db.GqlQuery('select * from ActivityModel where userid = :1 order by when desc', userid)
                    activities = list(activities)
                    self.render('activitylistpage.html', user = user, activities = activities)
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
class ActivityStatusHandler(SuperHandler):
    def get(self, username):
        user = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        if user:
            user = user[0]
            act_name = self.request.get('act_name')
            status = stats.general_activity_stats(user, act_name)
            userconf = json.loads(user.confstring)
            
            if not userconf.has_key('activities'):
                activities = db.GqlQuery('select * from ActivityModel where userid = :1', userid)
                activity_categories = list(set(a.name.strip() for a in activities))
                userconf['activities'] = activity_categories
                user.confstring = json.dumps(userconf)
                user.put()
                
            if status:
                self.render('activitystatuspage.html', user = user,
                                                       status = status,
                                                       act_name = act_name,
                                                       activity_categories = userconf['activities'])
            else:
                self.response.out.write('%s %s does not record such activity' % (user.salutation, user.realname))
        else:
            self.response.out.write('There is no such user')
            
class PresentTimedActivityHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    activities = db.GqlQuery('select * from TimedActivityModel order by end desc')
                    activities = list(activities)
                    self.render('timedactivitylistpage.html', user = user, activities = activities)
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
class PresentExpenseHandler(SuperHandler):
    def get(self, username):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        subject = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        # if the request is for a real person
        if subject:
            subject = subject[0]
            subject_conf = json.loads(subject.confstring)
            
            # if the requester is the same person as requested, mark it
            owner = False
            if user and user.username == username:
                owner = True
                
            # get expenses from db, then filter it if requester isn't owner
            expenses = list(db.GqlQuery('select * from ExpenseModel where userid = :1 order by when desc', str(subject.key().id())))
            if not owner:
                if subject_conf.has_key('public_expense_categories'):
                    expenses = [e for e in expenses if e.category in subject_conf['public_expense_categories']]
                else:
                    expenses = []
                    
            self.render('showexpensepage.html', user = subject,
                                                expenses = expenses)
        else:
            self.redirect('/') # requesting inexsistent user

class LibraryHandler(SuperHandler):
    def get(self, username):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        libtype = self.request.get('type')
        libmodel = 'BookLibraryModel'
        if libtype.lower() in ('game', 'games'):
            libtype = 'game'
            libmodel = 'GameLibraryModel'
        else:
            libtype = 'book'
            
        if user and user.username == username:
            books = db.GqlQuery('select * from %s where userid = :1 order by added desc' % libmodel, userid)
            books = list(books)
            self.render('librarypage.html', user = user, login = True, books = books, libtype=libtype)
        else:
            user = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
            if user[0]: 
                userid = str(user[0].key().id())
                books = list(db.GqlQuery('select * from %s where userid = :1 order by added desc' % libmodel, userid))
                self.render('librarypage.html', user = user[0], login = False, books = books, libtype=libtype)
            else:
                self.redirect('/')
                
    def post(self, username):
        book = db.get(self.request.get('key'))
        act = self.request.get('act')
        if act == 'toggle':
            book.active = not book.active
            if book.active:
                book.start = datetime.datetime.utcnow()
            else:
                book.finish = datetime.datetime.utcnow()
        elif act == 'new_img':
            image = self.request.get('new_img')
            if image:
                image = images.resize(image, height = 150)
                cat = 'book_img'
                if hasattr(book, 'platform'):
                    cat = 'game_img'
                image = models.ImageModel(userid = book.userid,
                                          image = db.Blob(image),
                                          uploaded = datetime.datetime.utcnow(),
                                          category = cat)
                image.put()
                imkey = str(image.key())
                book.image = imkey
        book.put()
        if hasattr(book, 'platform'):
            self.redirect('/u/'+username+'/library?type=game')
        else:
            self.redirect('/u/'+username+'/library?type=book')

class PanelHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            userconf = {}
            config_updated = False
            try:
                userconf = json.loads(user.confstring)
            except:
                userconf = {}
                user.confstring = json.dumps(userconf)
                user.put()
            #logging.error('user configuration')
            #for key in userconf.keys():
            #    logging.error(key + str(userconf[key]))
                
            if not userconf.has_key('activities'):
                activities = db.GqlQuery('select * from ActivityModel where userid = :1', userid)
                activity_categories = list(set(a.name.strip() for a in activities))
                userconf['activities'] = activity_categories
                config_updated = True
                
            if not userconf.has_key('timed_activities'):
                timed_activities = db.GqlQuery('select * from TimedActivityModel where userid = :1', userid)
                timed_activity_categories = list(set(ta.name for ta in timed_activities))
                userconf['timed_activities'] = timed_activity_categories
                config_updated = True
                
            if not userconf.has_key('places'):
                travels = list(db.GqlQuery('select * from TravelModel where userid = :1', userid))
                places = list(set([p.origin for p in travels] + [p.destination for p in travels]))
                #logging.error(places)
                userconf['places'] = places
                config_updated = True
                
            #logging.error('user configuration: ' + str(userconf))
            expense_categories = []
            if userconf.has_key('expense_categories'):
                expense_categories = userconf['expense_categories']
            else:
                expenses = list(db.GqlQuery('select * from ExpenseModel where userid = :1', userid))
                expense_categories = list(set(e.category.strip() for e in expenses))
                userconf['expense_categories'] = expense_categories
                config_updated = True
                
            if config_updated:
                user.confstring = json.dumps(userconf)
                user.put()
                
            songs = list(db.GqlQuery('select * from MusicLibraryModel order by last_report desc limit 10'))
                
            self.render('panelpage.html', user = user,
                                          expense_categories = expense_categories,
                                          activity_categories = userconf['activities'],
                                          timed_activity_categories = userconf['timed_activities'],
                                          places = userconf['places'],
                                          songs = songs)
        else:
            self.redirect('/login')
            
class UserpageHandler(SuperHandler):
    def get(self, username):
        users = db.GqlQuery('select * from UserModel where username = :1 limit 1', username)
        users = list(users)
        if len(users) > 0:
            user = users[0]
            coffee_stats = stats.coffee_stats(user)
            sleep_stats  = stats.sleep_stats(user)
            meal_stats = stats.meal_stats(user)
            hygiene_stats = stats.hygiene_stats(user)

            userid = str(user.key().id())
            old_photos = list(db.GqlQuery('select * from ImageModel where userid = :1 and category = :2 order by uploaded desc limit 5', userid, 'profile_img'))
            if len(old_photos) > 1:
                old_photos = old_photos[1:]
            else:
                old_photos = []
            social_media = db.GqlQuery('select * from SocialMediaModel where userid = :1', userid)
            books = list(db.GqlQuery('select * from BookLibraryModel where userid = :1 order by added desc limit 10', userid))
            active_books = [book for book in books if book.active]
            inactive_books = [book for book in books if not book.active]
            if len(inactive_books) > 4:
                inactive_books = inactive_books[0:4]
            games = list(db.GqlQuery('select * from GameLibraryModel where userid = :1 order by added desc limit 10', userid))
            active_games = [game for game in games if game.active]
            inactive_games = [game for game in games if not game.active]
            if len(inactive_games) > 4:
                inactive_games = inactive_games[0:4]
            
            user_messages = stats.user_messages(user, 5)
            guest_messages = stats.guest_messages(user)
            
            songs = db.GqlQuery('select * from MusicLibraryModel where userid = :1', userid)
            songs_top5_alltime = sorted(songs, cmp = lambda x, y: int(x.report_count - y.report_count), reverse = True)
            if len(songs_top5_alltime) > 5:
                songs_top5_alltime = songs_top5_alltime[:5]
            cutoff = datetime.datetime.utcnow() - datetime.timedelta(days = 7)
            songs_7days = [song for song in songs if song.last_report > cutoff]
            
            self.render('userpage.html', user = user,
                                         old_photos = old_photos,
                                         coffee_stats = coffee_stats,
                                         social_media = social_media,
                                         sleep_stats = sleep_stats,
                                         meal_stats = meal_stats,
                                         hygiene_stats = hygiene_stats,
                                         active_books = active_books,
                                         inactive_books = inactive_books,
                                         active_games = active_games,
                                         inactive_games = inactive_games,
                                         songs_top = songs_top5_alltime,
                                         songs_week = songs_7days,
                                         user_messages = user_messages,
                                         guest_messages = guest_messages)
        else:
            self.redirect('/') # go to user not found page

class AboutHandler(SuperHandler):
    def get(self):
        self.render('aboutpage.html')
        
class Blog_NewPostHandler(SuperHandler):
    @require_sameuser
    def get(self, user):
        userconf = json.loads(user.confstring)
        if not userconf.has_key('blog_categories'):
            blogposts = db.GqlQuery('select * from BlogPostModel where userid = :1', userid)
            blog_categories = list(set(post.category for post in blogposts))
            userconf['blog_categories'] = blog_categories
            user.confstring = json.dumps(userconf)
            user.put()
            
        self.render('blog_newpostpage.html', user = user,
                                             blog_categories = userconf['blog_categories'])
    
    @require_sameuser
    def post(self, user):
        title = self.request.get('title')
        content = self.request.get('content')
        privacy = self.request.get('privacy')
        category = self.request.get('category')
        isdraft = self.request.get('isdraft')
        logging.error('is this new post a draft? ' + isdraft)
        draft = False
        if isdraft:
            draft = True
        try:
            privacy = int(privacy)
        except:
            privacy = 3
        uploaded = datetime.datetime.utcnow()
        if title and content:
            if not privacy:
                privacy = 3 # 0: self, 1: approved, 2: logged in, 3: world
            if not category:
                category = 'unspecified'
            newpost = models.BlogPostModel(userid = str(user.key().id()),
                                           title = title,
                                           content = content,
                                           posted = uploaded,
                                           updated = uploaded,
                                           privacy = privacy,
                                           category = category,
                                           draft = draft)
            newpost.put()
            user.last_seen = datetime.datetime.utcnow()
            userconf = json.loads(user.confstring)
            if userconf.has_key('blog_categories'):
                if not category in userconf['blog_categories']:
                    userconf['blog_categories'].append(category)
                    user.confstring = json.dumps(userconf)
            else:
                userconf['blog_categories'] = [category]
                user.confstring = json.dumps(userconf)
            user.put()
            self.redirect('/u/' + user.username + '/blog')
            
class Blog_ShowPostsHandler(SuperHandler):
    def get(self, username):
        subject = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        subject_id = ''
        if subject:
            subject_id = str(subject[0].key().id())
        else:
            self.redirect('/') # user not found, must find better redirect destination
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        owner = False
        approved = False
        logged_in = False
        privilege = 3
        if user:
            if user.username == username:
                owner = True
                privilege = 0
            else:
                logged_in = True
                privilege = 2
                
        posts = list(db.GqlQuery('select * from BlogPostModel where userid = :1 order by posted desc', subject_id))
        blog_categories = list(set(['_'.join([elem for elem in post.category.split()]) for post in posts if post.category]))
        userconf = json.loads(user.confstring)
        if userconf.has_key('blog_categories'):
            if userconf['blog_categories'] != blog_categories:
                userconf['blog_categories'] = blog_categories
                user.confstring = json.dumps(userconf)
                user.put()
        else:
            userconf['blog_categories'] = blog_categories
            user.confstring = json.dumps(userconf)
            user.put()
            
        posts = [p for p in posts if p.privacy >= privilege and not p.draft]
        
        cat = self.request.get('cat')
        #logging.error('raw cat is ' + cat)
        if not cat and userconf.has_key('blog_public_categories'): #reserved for when we have default categories
            cats = userconf['blog_public_categories']
            p_cats = [e for e in cats]
            for cat in p_cats:
                if len(cat.split('_')) > 1:
                    cats.append(' '.join(cat.split('_')))
            #logging.error(cats)
            posts = [post for post in posts if post.category in cats]
        elif cat and cat != 'all':
            cats = [c.strip() for c in cat.split(' ')]
            p_cats = [e for e in cats]
            for cat in p_cats:
                if len(cat.split('_')) > 1:
                    cats.append(' '.join(cat.split('_')))
            #logging.error('cats are: ' + str(cats))
            posts = [post for post in posts if post.category in cats]
        else: # just pass everything
            pass
            
        self.render('blog_showpostspage.html', user = subject[0],
                                               posts = posts,
                                               blog_categories = blog_categories,
                                               userconf = json.loads(subject[0].confstring))
                                               
class Blog_PanelHandler(SuperHandler):
    def get(self, username):
        subject = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        subject_id = ''
        if subject:
            subject_id = str(subject[0].key().id())
        else:
            self.redirect('/') # user not found, must find better redirect destination
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user and user.username == username:
            userconf = json.loads(user.confstring)
            if not userconf.has_key('blog_headline'):
                userconf['blog_headline'] = '%s %s\'s Blog' % (user.salutation, user.realname)
                user.confstring = json.dumps(userconf)
                user.put()
            posts = list(db.GqlQuery('select * from BlogPostModel where userid = :1 order by posted desc', subject_id))
            blog_categories = ''
            if userconf.has_key('blog_categories'):
                blog_categories = userconf['blog_categories']
            else:
                blog_categories = list(set([p.category for p in posts]))
                userconf['blog_categories'] = blog_categories
                user.confstring = json.dumps(userconf)
                user.put()
                
            public_categories = ''
            if userconf.has_key('blog_public_categories'):
                public_categories = userconf['blog_public_categories']
            else:
                public_categories = blog_categories
                userconf['blog_public_categories'] = public_categories
                user.confstring = json.dumps(userconf)
                user.put()
            private_categories = [cat for cat in blog_categories if not cat in public_categories]
                
            self.render('blog_panelpage.html', user = user,
                                               userconf = userconf,
                                               posts = posts,
                                               blog_categories = blog_categories,
                                               public_categories = public_categories,
                                               private_categories = private_categories)
        else:
            self.redirect('/login') # logged in as different person than requested page
            
    def post(self, username):
        subject = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        subject_id = ''
        if subject:
            subject_id = str(subject[0].key().id())
        else:
            self.redirect('/') # user not found, must find better redirect destination
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user and user.username == username:
            new_headline = self.request.get('blog_headline')
            userconf = json.loads(user.confstring)
            if new_headline != userconf['blog_headline']:
                userconf['blog_headline'] = new_headline
                user.confstring = json.dumps(userconf)
                user.put()
            self.redirect('/u/' + username + '/blog/panel')
        else:
            self.redirect('/login')
            
class Blog_ShuffleCategoriesHandler(SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            to_private = self.request.get('to_private', allow_multiple = True)
            to_public = self.request.get('to_public', allow_multiple = True)
            #logging.error(to_private)
            #logging.error(to_public)
            userconf = json.loads(user.confstring)
            public_categories = userconf['blog_public_categories']
            #logging.error(public_categories)
            public_categories = [cat for cat in public_categories if not cat in to_private]
            public_categories += to_public
            #logging.error(public_categories)
            userconf['blog_public_categories'] = public_categories
            user.confstring = json.dumps(userconf)
            user.last_seen = datetime.datetime.utcnow()
            user.put()
            #logging.error(user.confstring)
            self.redirect('/u/%s/blog/panel' % user.username)
        else:
            self.redirect('/login')
            
class Blog_ShowSinglePostHandler(SuperHandler):
    def get(self, username, postid):
        subject = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        subject_id = ''
        if subject:
            subject_id = str(subject[0].key().id())
        else:
            self.redirect('/') # user not found, must find better redirect destination
        
        postkey = db.Key.from_path('BlogPostModel', int(postid))
        post = db.get(postkey)
        self.render('blog_showsinglepostpage.html', user = subject[0],
                                                    userconf = json.loads(subject[0].confstring),
                                                    post = post)
                                               
class Blog_EditPostHandler(SuperHandler):
    def get(self, username, postid):
        subject = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        subject_id = ''
        if subject:
            subject_id = str(subject[0].key().id())
        else:
            self.redirect('/') # user not found, must find better redirect destination
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user and user.username == username:
            userconf = json.loads(user.confstring)
            postkey = db.Key.from_path('BlogPostModel', int(postid))
            post = db.get(postkey)
            if post:
                self.render('blog_newpostpage.html', user = user,
                                                     post = post,
                                                     blog_categories = userconf['blog_categories'])
            else:
                self.redirect('/u/' + username + '/blog/newpost')
        else:
            self.redirect('/login')
            
    def post(self, username, postid):
        subject = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
        subject_id = ''
        if subject:
            subject_id = str(subject[0].key().id())
        else:
            self.redirect('/') # user not found, must find better redirect destination
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user and user.username == username:
            title = self.request.get('title')
            content = self.request.get('content')
            category = self.request.get('category')
            privacy = self.request.get('privacy')
            isdraft = self.request.get('isdraft')
            draft = False
            if isdraft:
                draft = True
            try:
                privacy = int(privacy)
            except:
                privacy = 0
            postkey = db.Key.from_path('BlogPostModel', int(postid))
            post = db.get(postkey)
            wasdraft = post.draft
            
            changed = False
            if title != post.title:
                post.title = title
                changed = True
            if content != post.content:
                post.content = content
                changed = True
            if privacy != post.privacy:
                post.privacy = post.privacy
                changed = True
            if category != post.category:
                post.category = category
                changed = True
            if draft != post.draft:
                post.draft = draft
                post.posted = datetime.datetime.utcnow()
                changed = True
                
            if changed:
                if not wasdraft:
                    post.updated = datetime.datetime.utcnow()
                post.put()
                user.last_seen = datetime.datetime.utcnow()
                user.put()
                
            self.redirect('/u/' + username + '/blog/' + postid)

class PublicUserpageHandler(SuperHandler):
    def get(self, username):
        users = db.GqlQuery('select * from UserModel where username = :1 limit 1', username)
        users = list(users)
        if len(users) > 0:
            user = users[0]
            self.render('publicuserpage.html', user = user)
        else:
            self.redirect('/')
            
class HackHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user and user.username == 'ryanotron':
            betakeys = list(db.GqlQuery('select * from BetaKeyModel'))
            self.render('hackpage.html', user = user)
        else:
            self.redirect('/login')
            
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user and user.username == 'ryanotron':
            keystring = self.request.get('betakey')
            betakey = models.BetaKeyModel(keystring = keystring, used = False)
            betakey.put()
            # meals = db.GqlQuery('select * from MealModel where userid = :1', userid)
            # meals = list(meals)
            # for meal in meals:
                # if meal.when < datetime.datetime(2012, 10, 31):
                    # meal.when = meal.when + datetime.timedelta(days = 8, hours = -8)
                    # meal.put()
            # self.redirect('/panel')
        else:
            self.redirect('/login')