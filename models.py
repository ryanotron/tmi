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
    gender     = db.StringProperty()
    pos_pronoun = db.StringProperty() # possessive pronoun
    nom_pronoun = db.StringProperty() # nominative pronoun
    pos_determi = db.StringProperty() # possessive determinant
    photo       = db.BlobProperty()

class ActivityModel(db.Model):
    userid = db.StringProperty(required = True)
    name   = db.StringProperty()
    when   = db.DateTimeProperty()
    
class TimedActivityModel(db.Model):
    userid = db.StringProperty(required = True)
    name   = db.StringProperty()
    start  = db.DateTimeProperty()
    end    = db.DateTimeProperty()

class ExpenseModel(db.Model):
    userid   = db.StringProperty(required = True)
    name     = db.StringProperty()
    category = db.StringProperty()
    amount   = db.FloatProperty()
    currency = db.StringProperty() # stub. Defaults to user's currency. When we can check for currency conversion online, this'd more useful
    when     = db.DateTimeProperty()

class TravelModel(db.Model):
    userid      = db.StringProperty(required = True)
    origin      = db.StringProperty()
    destination = db.StringProperty()
    whenstart   = db.DateTimeProperty()
    whenfinish  = db.DateTimeProperty()

class MealModel(db.Model):
    userid   = db.StringProperty(required = True)
    when     = db.DateTimeProperty()
    menu     = db.StringProperty()
    place    = db.StringProperty()
    category = db.StringProperty() # breakfast, lunch, dinner, supper, snack

class UserMessageModel(db.Model):
    userid  = db.StringProperty(required = True)
    message = db.TextProperty()
    when    = db.DateTimeProperty()

class GuestMessageModel(db.Model):
    userid    = db.StringProperty(required = True)
    guestname = db.StringProperty()
    message   = db.TextProperty()
    when      = db.DateTimeProperty()
    
    
