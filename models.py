from google.appengine.ext import db

class UserModel(db.Model):
    username = db.StringProperty(required = True)
    hashedpw = db.StringProperty(required = True)
    nameday  = db.DateTimeProperty(auto_now_add = True)
    email    = db.EmailProperty()
    last_seen = db.DateTimeProperty()
    timezone  = db.FloatProperty()
    currency  = db.StringProperty()

class ActivityModel(db.Model):
    name = db.StringProperty(required = True)
    start = db.DateTimeProperty(required = True)
    end = db.DateTimeProperty(required = True)
    userid = db.StringProperty(required = True)
    
class EventModel(db.Model):
    name = db.StringProperty(required = True)
    when = db.DateTimeProperty(required = True)
    userid = db.StringProperty(required = True)
    
class CommuteModel(db.Model):
    origin = db.StringProperty(required = True)
    destination = db.StringProperty(required = True)
    start = db.DateTimeProperty(required = True)
    end = db.DateTimeProperty(required = True)
    userid = db.StringProperty(required = True)
    
class ExpenseModel(db.Model):
    name = db.StringProperty(required = True)
    category = db.StringProperty()
    amount = db.FloatProperty()
    when = db.DateTimeProperty()
    userid = db.StringProperty(required = True)
    
class SelfMessageModel(db.Model):
    userid = db.StringProperty(required = True)
    message = db.StringProperty(required = True)
    when = db.DateTimeProperty(auto_now_add = True)
    
class VisitorMessageModel(db.Model):
    pagename = db.StringProperty(required = True)
    guestname = db.StringProperty()
    message = db.StringProperty()
    when = db.DateTimeProperty()