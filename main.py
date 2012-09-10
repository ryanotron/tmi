import webapp2
import jinja2, os
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinjaenv = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class ActivityModel(db.Model):
    name = db.StringProperty(required = True)
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
        
    def post(self):
        self.render('panelpage.html')

app = webapp2.WSGIApplication([('/', MainPageHandler),
                               ('/panel/?', PanelHandler)],
                              debug = True)