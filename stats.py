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