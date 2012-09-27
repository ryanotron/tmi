import webapp2
import handlers as h

app = webapp2.WSGIApplication([('/', h.MainpageHandler),
                               ('/signup/?', h.SignupHandler),
                               ('/login/?', h.LoginHandler),
                               ('/logout/?', h.LogoutHandler),
                               ('/profile/?', h.ProfileHandler),
                               ('/postactivity/?', h.PostActivityHandler)],
                               debug = True)