import webapp2
import handlers as h
import constants

app = webapp2.WSGIApplication([('/', h.MainpageHandler),
                               ('/tmi/?', h.MainpageHandler),
                               ('/signup/?', h.SignupHandler),
                               ('/login/?', h.LoginHandler),
                               ('/logout/?', h.LogoutHandler),
                               ('/profile/?', h.ProfileHandler),
                               ('/postactivity/?', h.PostActivityHandler),
                               ('/inspostactivity/?', h.InsPostActivityHandler),
                               ('/posttimedactivity/?', h.PostTimedActivityHandler),
                               ('/postexpense/?', h.PostExpenseHandler),
                               ('/posttravel/?', h.PostTravelHandler),
                               ('/postmeal/?', h.PostMealHandler),
                               ('/postmessage/?', h.PostUserMessageHandler),
                               ('/postguestmessage/?', h.PostGuestMessageHandler),
                               ('/panel/?', h.PanelHandler),
                               ('/u/' + r'([a-zA-Z0-9_-]{4,20})/?', h.UserpageHandler),],
                               debug = True)