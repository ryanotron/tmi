import webapp2
import jinja2, os, datetime
from google.appengine.ext import db

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
        self.render('panelpage.html')
        
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
        email    = self.request.get('verify')
        
        if username:
            ###
            
app = webapp2.WSGIApplication([('/', MainPageHandler),
                               ('/panel/?', PanelHandler),
                               ('/activity/?', ActivityHandler)],
                              debug = True)