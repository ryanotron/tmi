import webapp2
import handlers as h
import toys as t
import constants

app = webapp2.WSGIApplication([('/', h.MainpageHandler),
                               ('/tmi/?', h.MainpageHandler),
                               ('/signup/?', h.SignupHandler),
                               ('/login/?', h.LoginHandler),
                               ('/logout/?', h.LogoutHandler),
                               ('/profile/?', h.ProfileHandler),
                               ('/img', h.ImageHandler),
                               ('/postactivity/?', h.PostActivityHandler),
                               ('/inspostactivity/?', h.InsPostActivityHandler),
                               ('/postbatchactivity/?', h.PostBatchActivityHandler),
                               ('/posttimedactivity/?', h.PostTimedActivityHandler),
                               ('/postbatchtimedactivity/?', h.PostBatchTimedActivityHandler),
                               ('/postexpense/?', h.PostExpenseHandler),
                               ('/postbatchexpense/?', h.PostBatchExpenseHandler),
                               ('/posttravel/?', h.PostTravelHandler),
                               ('/postmeal/?', h.PostMealHandler),
                               ('/postbook/?', h.PostBookHandler),
                               ('/postgame/?', h.PostGameHandler),
                               ('/postmessage/?', h.PostUserMessageHandler),
                               ('/postguestmessage/?', h.PostGuestMessageHandler),
                               ('/panel/?', h.PanelHandler),
                               ('/activities/?', h.PresentActivityHandler),
                               ('/timedactivities/?', h.PresentTimedActivityHandler),
                               ('/u/' + r'([a-zA-Z0-9_-]{4,20})/public/?', h.PublicUserpageHandler),
                               ('/u/' + r'([a-zA-Z0-9_-]{4,20})/?', h.UserpageHandler),
                               ('/toys/simplechart/?', t.SimpleChartHandler),],
                               debug = True)