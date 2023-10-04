from google.appengine.ext import ndb

class UserModel(ndb.Model):
    username   = ndb.StringProperty(required = True)
    hashedpw   = ndb.StringProperty(required = True)
    nameday    = ndb.DateTimeProperty()
    email      = ndb.StringProperty()
    timezone   = ndb.FloatProperty()
    currency   = ndb.StringProperty()
    realname   = ndb.StringProperty()
    salutation = ndb.StringProperty()
    last_seen  = ndb.DateTimeProperty(required = True)
    gender     = ndb.StringProperty()
    pos_pronoun = ndb.StringProperty() # possessive pronoun (his, hers, its)
    nom_pronoun = ndb.StringProperty() # nominative pronoun (he, she, it)
    acc_pronoun = ndb.StringProperty() # accusative pronoun (him, her, it)
    pos_determi = ndb.StringProperty() # possessive determinant (his, her, its)
    photo_key   = ndb.StringProperty()
    confstring  = ndb.TextProperty() # configuration string, a json string dump
    
class SocialMediaModel(ndb.Model):
    userid = ndb.StringProperty(required = True)
    sm_username = ndb.StringProperty(required = True)
    sm_sitename = ndb.StringProperty(required = True)
    sm_siteurl  = ndb.StringProperty()
    sm_userpage = ndb.StringProperty()
    
class ImageModel(ndb.Model):
    userid   = ndb.StringProperty(required = True)
    image    = ndb.BlobProperty()
    uploaded = ndb.DateTimeProperty()
    category = ndb.StringProperty() #profile_img, meal_img, book_img, game_img, expense_img

class ActivityModel(ndb.Model):
    userid = ndb.StringProperty(required = True)
    name   = ndb.StringProperty()
    when   = ndb.DateTimeProperty()
    timezone = ndb.FloatProperty()
    
class TimedActivityModel(ndb.Model):
    userid = ndb.StringProperty(required = True)
    name   = ndb.StringProperty()
    start  = ndb.DateTimeProperty()
    end    = ndb.DateTimeProperty()
    timezone = ndb.FloatProperty()

class ExpenseModel(ndb.Model):
    userid   = ndb.StringProperty(required = True)
    name     = ndb.StringProperty()
    category = ndb.StringProperty()
    amount   = ndb.FloatProperty()
    currency = ndb.StringProperty() # stub. Defaults to user's currency. When we can check for currency conversion online, this'd more useful
    when     = ndb.DateTimeProperty()

class TravelModel(ndb.Model):
    userid      = ndb.StringProperty(required = True)
    origin      = ndb.StringProperty()
    destination = ndb.StringProperty()
    whenstart   = ndb.DateTimeProperty()
    whenfinish  = ndb.DateTimeProperty()
    start_timezone  = ndb.FloatProperty()
    finish_timezone = ndb.FloatProperty()

class MealModel(ndb.Model):
    userid   = ndb.StringProperty(required = True)
    when     = ndb.DateTimeProperty()
    menu     = ndb.StringProperty()
    place    = ndb.StringProperty()
    category = ndb.StringProperty() # breakfast, lunch, dinner, supper, snack
    image    = ndb.StringProperty()
    timezone = ndb.FloatProperty()

class UserMessageModel(ndb.Model):
    userid  = ndb.StringProperty(required = True)
    message = ndb.TextProperty()
    when    = ndb.DateTimeProperty()

class GuestMessageModel(ndb.Model):
    userid    = ndb.StringProperty(required = True)
    guestname = ndb.StringProperty()
    message   = ndb.TextProperty()
    when      = ndb.DateTimeProperty()
    
class BookLibraryModel(ndb.Model):
    userid = ndb.StringProperty(required = True)
    title  = ndb.StringProperty()
    author = ndb.StringProperty()
    isbn   = ndb.StringProperty()
    doi    = ndb.StringProperty()
    added  = ndb.DateTimeProperty()
    start  = ndb.DateTimeProperty()
    finish = ndb.DateTimeProperty()
    active = ndb.BooleanProperty()
    image  = ndb.StringProperty()
    
class GameLibraryModel(ndb.Model):
    userid = ndb.StringProperty()
    title  = ndb.StringProperty()
    added  = ndb.DateTimeProperty()
    start  = ndb.DateTimeProperty()
    finish = ndb.DateTimeProperty()
    active = ndb.BooleanProperty()
    platform = ndb.StringProperty()
    image = ndb.StringProperty()
    
class MusicLibraryModel(ndb.Model):
    userid       = ndb.StringProperty()
    title        = ndb.StringProperty()
    artist       = ndb.StringProperty()
    album        = ndb.StringProperty()
    year         = ndb.IntegerProperty()
    url          = ndb.StringProperty()
    first_report = ndb.DateTimeProperty()
    last_report  = ndb.DateTimeProperty()
    report_count = ndb.IntegerProperty()
    
class BetaKeyModel(ndb.Model):
    keystring = ndb.StringProperty()
    used = ndb.BooleanProperty()
    whenused = ndb.DateTimeProperty()
    
class BlogPostModel(ndb.Model):
    userid = ndb.StringProperty()
    posted = ndb.DateTimeProperty()
    updated = ndb.DateTimeProperty()
    title = ndb.StringProperty()
    content = ndb.TextProperty()
    privacy = ndb.IntegerProperty()
    category = ndb.StringProperty()
    draft = ndb.BooleanProperty()