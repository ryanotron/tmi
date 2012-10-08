import datetime
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
        wake_time = latest_sleep.end + user.timezone
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
        latest_cup = (datetime.datetime.now() - latest_coffee.when).seconds / (60.0 * 60.0)
        return {'latest_cup': latest_cup}
    else:
        pass
    
def meal_status(user):
    pass
    