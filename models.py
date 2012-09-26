from google.appengine.ext import db

class UserModel(db.Model):
    username   = db.StringProperty(required = True)
    hashedpw   = db.StringProperty(required = True)
    nameday    = db.DateTimeProperty()
    email      = db.StringProperty()
    timezone   = db.FloatProperty()
    currency   = db.StringProperty()
    realname   = db.StringProperty()
    salutation = db.StringProperty()
    last_seen  = db.DateTimeProperty(required = True)
    
    