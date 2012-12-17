from handlers import SuperHandler
import logging, utils

def require_login(fn):
    def new_fn(self, *args, **kwargs):
        userid = self.request.cookies.get('userid')
        userid, user = utils.verify_user(userid)
        if user:
            fn(self, user, *args, **kwargs)
        else:
            logging.error('not logged in!')
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

class SimpleChartHandler(SuperHandler):
    def get(self):
        datax = range(10)
        datay = [elem ** 2 for elem in datax]
        
        self.render('simplechart.html', datax = datax, datay = datay)
        
class ToypageHandler(SuperHandler):
    @require_login
    def get(self, user):
        self.response.out.write('Hello, you are currently logged in as %s %s' % (user.salutation, user.realname))
        
class ToyUserHandler(SuperHandler):
    @require_sameuser
    def get(self, user):
        self.response.out.write('Hello, you are currently logged in as %s %s' % (user.salutation, user.realname))