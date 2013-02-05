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
    pos_pronoun = db.StringProperty() # possessive pronoun (his, hers, its)
    nom_pronoun = db.StringProperty() # nominative pronoun (he, she, it)
    acc_pronoun = db.StringProperty() # accusative pronoun (him, her, it)
    pos_determi = db.StringProperty() # possessive determinant (his, her, its)
    photo_key   = db.StringProperty()
    confstring  = db.TextProperty() # configuration string, a json string dump
    
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
    timezone = db.FloatProperty()
    
class TimedActivityModel(db.Model):
    userid = db.StringProperty(required = True)
    name   = db.StringProperty()
    start  = db.DateTimeProperty()
    end    = db.DateTimeProperty()
    timezone = db.FloatProperty()

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
    start_timezone  = db.FloatProperty()
    finish_timezone = db.FloatProperty()

class MealModel(db.Model):
    userid   = db.StringProperty(required = True)
    when     = db.DateTimeProperty()
    menu     = db.StringProperty()
    place    = db.StringProperty()
    category = db.StringProperty() # breakfast, lunch, dinner, supper, snack
    image    = db.StringProperty()
    timezone = db.FloatProperty()

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
    
class MusicLibraryModel(db.Model):
    userid       = db.StringProperty()
    title        = db.StringProperty()
    artist       = db.StringProperty()
    album        = db.StringProperty()
    year         = db.IntegerProperty()
    url          = db.StringProperty()
    first_report = db.DateTimeProperty()
    last_report  = db.DateTimeProperty()
    report_count = db.IntegerProperty()
    
class BetaKeyModel(db.Model):
    keystring = db.StringProperty()
    used = db.BooleanProperty()
    whenused = db.DateTimeProperty()
    
class BlogPostModel(db.Model):
    userid = db.StringProperty()
    posted = db.DateTimeProperty()
    updated = db.DateTimeProperty()
    title = db.StringProperty()
    content = db.TextProperty()
    privacy = db.IntegerProperty()
    category = db.StringProperty()
    draft = db.BooleanProperty()