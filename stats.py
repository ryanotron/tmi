import datetime, logging
from google.appengine.ext import db

def get_average_sleep(user):
    userid = str(user.key().id())
    if userid:
        sleeps = db.GqlQuery('select * from TimedActivityModel where userid = :1 and name = \'sleep\'', userid)
        sleeps = list(sleep)
        if sleeps:
            average_sleep = 0.0
            for sleep in sleeps:
                sleep_duration = sleep.end - sleep.start
                average_sleep = average_sleep + sleep_duration.seconds
            average_sleep = average_sleep / (1.0 * len(sleeps))
        else:
            return None
    else:
        return None
        
def sleep_status(user):
    userid = str(user.key().id())
    sleeps = db.GqlQuery('select * from TimedActivityModel where userid = :1 and name = :2 order by end desc limit 1', userid, 'sleep')
    sleeps = list(sleeps)
    if len(sleeps) > 0:
        latest_sleep = sleeps[0]
        wake_time = latest_sleep.end + datetime.timedelta(hours = user.timezone)
        sleep_hours = (latest_sleep.end - latest_sleep.start).seconds / (60.0 * 60.0)
        return {'wake_time': wake_time, 'sleep_hours': sleep_hours}
    else:
        pass
    
def coffee_status(user):
    userid = str(user.key().id())
    coffees = db.GqlQuery('select * from ActivityModel where userid = :1 and name = :2 order by when desc limit 1', userid, 'coffee')
    coffees = list(coffees)
    if len(coffees) > 0:
        latest_coffee = coffees[0]
        latest_cup = (datetime.datetime.utcnow() - latest_coffee.when).seconds / (60.0 * 60.0)
        return {'latest_cup': latest_cup}
    else:
        pass
    
def meal_status(user):
    userid = str(user.key().id())
    meals = db.GqlQuery('select * from MealModel where userid = :1 order by when desc', userid)
    meals = list(meals)
    if len(meals) > 0:
        latest_meal = meals[0]
        latest_category = latest_meal.category
        meal_time = latest_meal.when + datetime.timedelta(user.timezone)
        latest_menu = latest_meal.menu
        return {'latest_category': latest_category,
                'meal_time': meal_time,
                'latest_menu': latest_menu}
    else:
        pass

def activity_status(user, act_name, number):
    userid = str(user.key().id())
    query = 'select * from ActivityModel where userid = \'%s\' and name = \'%s\' order by when desc' % (userid, act_name)
    if number > 0:
        query += ' limit %d' % number
        
    acts = db.GqlQuery(query)
    acts = list(acts)
    if len(acts) > 0:
        latest = acts[0]
        timelatest = latest.when + datetime.timedelta(hours = user.timezone)
        timesince  = (datetime.datetime.utcnow() - latest.when).seconds
        logging.error(str(timesince))
        return {'timelatest': timelatest, 'timesince': timesince}
    else:
        pass
        
def user_messages(user, number):
    userid = str(user.key().id())
    query = 'select * from UserMessageModel where userid = \'%s\' order by when desc' % userid
    if number > 0:
        query += ' limit %d' % number
        
    messages = db.GqlQuery(query)
    messages = list(messages)
    if len(messages) > 0:
        return messages
    else:
        pass
        
def guest_messages(user, number):
    userid = str(user.key().id())
    query = 'select * from GuestMessageModel where userid = \'%s\' order by when desc' % userid
    if number > 0:
        query += ' limit %d' % number
        
    messages = db.GqlQuery(query)
    messages = list(messages)
    if len(messages) > 0:
        return messages
    else:
        pass
        