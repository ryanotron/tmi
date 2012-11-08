import utils, models, constants, stats
from google.appengine.ext import db
from google.appengine.api import images
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
                                                                    currency   = 'SGD')
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
                    elif new_gender == 'female':
                        user.pos_pronoun = 'her'
                        user.pos_determi = 'hers'
                        user.nom_pronoun = 'she'
                    else:
                        user.pos_pronoun = 'its'
                        user.pos_determi = 'its'
                        user.nom_pronoun = 'it'
                    updated = True

                if new_photo:
                    new_photo = images.resize(new_photo, height = 150)
                    new_photo = models.ImageModel(userid = userid,
                                                  uploaded = datetime.datetime.utcnow(),
                                                  image = db.Blob(new_photo))
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
                            #logging.error('split hours')

                            D, M, Y = activity_day.split('/')
                            Y = int(Y)
                            M = int(M)
                            D = int(D)
                            #logging.error('split day')

                            new_activity = models.ActivityModel(userid = userid,
                                                                name   = activity_name,
                                                                when   = datetime.datetime(Y, M, D, h, m) - datetime.timedelta(hours = user.timezone))
                                                                
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
            logging.error('posted '+act_name+' from instant, with new user verification method')
            new_act = models.ActivityModel(userid = userid,
                                           name   = act_name,
                                           when   = datetime.datetime.utcnow())
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
                                                               when = when - datetime.timedelta(hours = user.timezone))
                                new_act.put()

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
                                                                end = end - datetime.timedelta(hours = user.timezone))
                                new_act.put()
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
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    expenses = self.request.get('batchexpense')
                    if expenses:
                        expenses = expenses.split('\n')
                        for elem in expenses:
                            expense = constants.batchexpense_re.match(elem)
                            if expense:
                                new_expense = models.ExpenseModel(userid   = str(userid),
                                                                  name     = expense.group('name'),
                                                                  category = expense.group('cat'),
                                                                  amount   = float(expense.group('amount')),
                                                                  when     = utils.str_to_datetime(expense.group('when')),
                                                                  currency = user.currency)
                                logging.error(expense.groups())
                                new_expense.put()
                                user.last_seen = datetime.datetime.utcnow()
                                user.put()
                                self.redirect('/panel')
                        self.redirect('/panel')
                    else:
                        self.redirect('/panel')
                else:
                    self.redirect('login')
            else:
                self.redirect('login')
        else:
            self.redirect('login')
            
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
                                trv_start_time = trv_finish_time - datetime.timedelta(minutes = float(trv_duration))
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

            if meal_menu and meal_time:
                try:
                    D, M, Y = [int(elem) for elem in meal_day.split('/')]
                    h, m    = [int(elem) for elem in meal_time.split(':')]
                    meal_time = datetime.datetime(Y, M, D, h, m) - datetime.timedelta(hours = user.timezone)

                    new_meal = models.MealModel(userid   = userid,
                                                when     = meal_time,
                                                menu     = meal_menu,
                                                place    = meal_place,
                                                category = meal_category)

                    if meal_image:
                        image = images.resize(meal_image, height = constants.image_height)
                        image = models.ImageModel(userid = userid,
                                                  uploaded = datetime.datetime.utcnow(),
                                                  image = db.Blob(image))
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
                        logging.error('failed parsing datetime')
                        self.redirect('/panel')
                if finish:
                    try:
                        D, M, Y = [int(elem) for elem in finish.split('/')]
                        finish = datetime.datetime(Y, M, D)
                    except:
                        logging.error('failed parsing datetime')
                        self.redirect('/panel')
                        
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
                                              image = db.Blob(image))
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
                        logging.error('failed parsing datetime')
                        self.redirect('/panel')
                if finish:
                    try:
                        D, M, Y = [int(elem) for elem in finish.split('/')]
                        finish = datetime.datetime(Y, M, D)
                    except:
                        logging.error('failed parsing datetime')
                        self.redirect('/panel')
                        
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
                                              image = db.Blob(image))
                    image.put()
                    image_key = str(image.key())
                    new_game.image = image_key
                
                new_game.put()
                user.last_seen = datetime.datetime.utcnow()
                user.put()
                self.redirect('/panel')
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
                    activities = db.GqlQuery('select * from ActivityModel order by when desc')
                    activities = list(activities)
                    self.render('activitylistpage.html', user = user, activities = activities)
                else:
                    self.redirect('/login')
            else:
                self.redirect('/login')
        else:
            self.redirect('/login')
            
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

class LibraryHandler(SuperHandler):
    def get(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        libtype = self.request.get('type')
        libmodel = 'BookLibraryModel'
        if libtype.lower() in ('game', 'games'):
            libtype = 'game'
            libmodel = 'GameLibraryModel'
        else:
            libtype = 'book'
            
        if user:
            books = db.GqlQuery('select * from %s where userid = :1 order by added desc' % libmodel, userid)
            books = list(books)
            self.render('librarypage.html', user = user, login = True, books = books, libtype=libtype)
        else:
            username = self.request.get('user')
            user = list(db.GqlQuery('select * from UserModel where username = :1 limit 1', username))
            if user[0]: 
                userid = str(user[0].key().id())
                books = list(db.GqlQuery('select * from %s where userid = :1 order by added desc' % libmodel, userid))
                self.render('librarypage.html', user = user[0], login = False, books = books, libtype=libtype)
            else:
                self.redirect('/')
                
    def post(self):
        book = db.get(self.request.get('key'))
        book.active = not book.active
        if book.active:
            book.start = datetime.datetime.utcnow()
        else:
            book.finish = datetime.datetime.utcnow()
        book.put()
        if hasattr(book, 'platform'):
            self.redirect('/library?type=game')
        else:
            self.redirect('/library?type=book')

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
            social_media = db.GqlQuery('select * from SocialMediaModel where userid = :1', userid)
            books = list(db.GqlQuery('select * from BookLibraryModel where userid = :1 order by added desc limit 5', userid))
            active_books = [book for book in books if book.active]
            inactive_books = [book for book in books if not book.active]
            games = list(db.GqlQuery('select * from GameLibraryModel where userid = :1 order by added desc limit 5', userid))
            active_games = [game for game in games if game.active]
            inactive_games = [game for game in games if not game.active]
            
            user_messages = stats.user_messages(user, 5)
            guest_messages = stats.guest_messages(user)
            
            self.render('userpage.html', user = user,
                                         coffee_stats = coffee_stats,
                                         social_media = social_media,
                                         sleep_stats = sleep_stats,
                                         meal_stats = meal_stats,
                                         hygiene_stats = hygiene_stats,
                                         active_books = active_books,
                                         inactive_books = inactive_books,
                                         active_games = active_games,
                                         inactive_games = inactive_games,
                                         user_messages = user_messages,
                                         guest_messages = guest_messages)
        else:
            self.redirect('/') # go to user not found page
            
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
        if user:
            self.render('hackpage.html', user = user)
        else:
            self.redirect('/login')
            
    def post(self):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            betakey = models.BetaKeyModel(keystring = 'humpty dumpty',
                                          used = False)
            betakey.put()
            # meals = db.GqlQuery('select * from MealModel where userid = :1', userid)
            # meals = list(meals)
            # for meal in meals:
                # if meal.when < datetime.datetime(2012, 10, 31):
                    # meal.when = meal.when + datetime.timedelta(days = 8, hours = -8)
                    # meal.put()
            self.redirect('/panel')
        else:
            self.redirect('/login')