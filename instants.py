from google.appengine.ext import db
import webapp2
import utils, handlers, models
import datetime

class InsPostActivityHandler(handlers.SuperHandler):
    def post(self):
        userid = self.request.cookies.get('userid')
        if userid:
            userid = utils.verify_cookie(userid)
            if userid:
                user = utils.validate_user(userid)
                if user:
                    act_name = self.request.get('activity_name')
                    new_act = models.ActivityModel(userid = userid,
                                                   name   = activity_name,
                                                   when   = datetime.datetime.now())
                    new_act.put()
                    user.last_seen = datetime.datetime.now()
                    user.put()
                    self.redirect('/panel')
                else:
                    self.redirect('login')
            else:
                self.redirect('login')
        else:
            self.redirect('login')