import webapp2

from models import *
from handlers import *
            
userpage_re = r'([a-zA-Z_-]+)/?'
app = webapp2.WSGIApplication([('/', MainPageHandler),
                               ('/panel/?', PanelHandler),
                               ('/activity/?', ActivityHandler),
                               ('/commute/?', CommuteHandler),
                               ('/expense/?', ExpenseHandler),
                               ('/signup/?', SignupHandler),
                               ('/login/?', LoginHandler),
                               ('/logout/?', LogoutHandler),
                               ('/event/?', EventHandler),
                               ('/selfmessage/?', SelfMessageHandler),
                               ('/comment/?', VisitorMessageHandler),
                               ('/comrade/' + userpage_re + 'profile/?', ProfileHandler),
                               ('/comrade/' + userpage_re, UserpageHandler)],
                              debug = True)