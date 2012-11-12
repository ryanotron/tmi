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
    photo_key   = db.StringProperty()
    
class SocialMediaModel(db.Model):
    userid = db.StringProperty(required = True)
    sm_username = db.StringProperty(required = True)
    sm_sitename = db.StringProperty(required = True)
    sm_siteurl  = db.LinkProperty()
    sm_userpage = db.LinkProperty()
    
class ImageModel(db.Model):
    userid   = db.StringProperty(required = True)
    image    = db.BlobProperty()
    uploaded = db.DateTimeProperty()
    category = db.StringProperty() #profile_img, meal_img, book_img, game_img, expense_img

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
    image    = db.StringProperty()

class UserMessageModel(db.Model):
    userid  = db.StringProperty(required = True)
    message = db.TextProperty()
    when    = db.DateTimeProperty()

class GuestMessageModel(db.Model):
    userid    = db.StringProperty(required = True)
    guestname = db.StringProperty()
    message   = db.TextProperty()
    when      = db.DateTimeProperty()
    
class BookLibraryModel(db.Model):
    userid = db.StringProperty(required = True)
    title  = db.StringProperty()
    author = db.StringProperty()
    isbn   = db.StringProperty()
    doi    = db.StringProperty()
    added  = db.DateTimeProperty()
    start  = db.DateTimeProperty()
    finish = db.DateTimeProperty()
    active = db.BooleanProperty()
    image  = db.StringProperty()
    
class GameLibraryModel(db.Model):
    userid = db.StringProperty()
    title  = db.StringProperty()
    added  = db.DateTimeProperty()
    start  = db.DateTimeProperty()
    finish = db.DateTimeProperty()
    active = db.BooleanProperty()
    platform = db.StringProperty()
    image = db.StringProperty()
    
class BetaKeyModel(db.Model):
    keystring = db.StringProperty()
    used = db.BooleanProperty()
    whenused = db.DateTimeProperty()