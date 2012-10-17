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
                average_sleep = average_sleep + sleep_duration.total_seconds()
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
        sleep_hours = (latest_sleep.end - latest_sleep.start).total_seconds() / (60.0 * 60.0)
        return {'wake_time': wake_time, 'sleep_hours': sleep_hours}
    else:
        pass
        
def get_sleeps(user):
    userid = str(user.key().id())
    sleeps = db.GqlQuery('select * from TimedActivityModel where userid = :1 and name = :2 order by end asc', userid, 'sleep')
    sleeps = list(sleeps)
    if len(sleeps) > 0:
        return sleeps
    else:
        logging.error('sleep not found')
        return None

def last_week_average_sleep(user):
    #logging.error('calculating average sleep...')
    sleeps = get_sleeps(user)
    if sleeps:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours = user.timezone)
        startday = now - datetime.timedelta(days = 7 + now.weekday())
        endday   = now - datetime.timedelta(days = now.weekday())
        total_sleep = 0.0
        for sleep in sleeps:
            endtime = sleep.end + datetime.timedelta(hours = user.timezone)
            if endtime > startday and endtime < endday:
                duration = (sleep.end - sleep.start).total_seconds() / (60.0 * 60.0)
                total_sleep = total_sleep + duration
        #logging.error('calculated average sleep!')
        return total_sleep / 7.0
    else:
        return None
        
def all_time_average_sleep(user):
    sleeps = get_sleeps(user)
    if sleeps:
        total_sleep = 0.0
        days = int((sleeps[-1].end - sleeps[0].end).total_seconds() / (60.0 * 60.0 * 24.0)) + 1
        for sleep in sleeps:
            duration = (sleep.end - sleep.start).total_seconds() / (3600.0)
            total_sleep = total_sleep + duration
        return total_sleep / days
        
def sleep_debt(user):
    last_week_average = last_week_average_sleep(user)
    sleeps = get_sleeps(user)
    if sleeps:
        now = datetime.datetime.utcnow() + datetime.timedelta(hours = user.timezone)
        startday = now - datetime.timedelta(days = now.weekday())
        total_debt = 0.0
        for sleep in sleeps:
            if sleep.end > startday:
                duration = (sleep.end - sleep.start).total_seconds() / (60.0 * 60.0)
                total_debt = total_debt + max([0.0, last_week_average - duration])
        #logging.error('calculated sleep debt!')
        return total_debt

def coffee_stats(user):
    userid = str(user.key().id())
    coffees = get_activities(user, 'coffee')
    status = {}
    if coffees:
        status['last_cup'] = (datetime.datetime.utcnow() - coffees[0].when).total_seconds() / (3600.0)
        
        status['todays_total'] = 0
        done = False
        i = 0
        today = datetime.datetime.utcnow() + datetime.timedelta(hours = user.timezone)
        while not done or i < len(coffees):
            if (coffees[i].when + datetime.timedelta(hours = user.timezone)).day < today.day:
                done = True
            else:
                logging.error(i)
                status['todays_total'] += 1
                i += 1
                
        daysince = (datetime.datetime.utcnow() + datetime.timedelta(hours = user.timezone) - coffees[-1].when).days
        if daysince > 0:
            status['alltime_average'] = len(coffees) / daysince
        else:
            status['alltime_average'] = 0
            
        return status
    else:
        return None

def coffee_status(user):
    userid = str(user.key().id())
    coffees = db.GqlQuery('select * from ActivityModel where userid = :1 and name = :2 order by when desc limit 1', userid, 'coffee')
    coffees = list(coffees)
    if len(coffees) > 0:
        latest_coffee = coffees[0]
        latest_cup = (datetime.datetime.utcnow() - latest_coffee.when).total_seconds() / (60.0 * 60.0)
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

def get_activities(user, act_name, order = 'desc', number = 0):
    userid = str(user.key().id())
    query = 'select * from ActivityModel where userid = \'%s\' and name = \'%s\' order by when %s' % (userid, act_name, order)
    if number > 0:
        query = query + ' limit %d' % number
    acts = db.GqlQuery(query)
    return list(acts)
    
def time_between_activities(user, act_name, order = 'desc', number = 0):
    activities = get_activities(user, act_name, order, number)
    timelist = []
    for i in range(len(activities) - 1):
        time_between = (activities[i+1].when - activities[i].when).total_seconds()
        timelist.append(time_between)
    return timelist
    
def average_time_between_activities(user, act_name):
    timelist = time_between_activities(user, act_name, 'asc')
    if timelist:
        return sum(timelist) / len(timelist)
    else:
        return 0
    
def get_coffees(user):
    return get_activities(user, 'coffee', 'asc')
    
def coffee_per_day(user):
    coffees = get_coffees(user)
    if coffees:
        daylist = [0]
        numdays = (coffees[-1].when - coffees[0].when).days + 1
        current = coffees[0].when
        for coffee in coffees:
            if coffee.when.day == current.day:
                daylist[-1] = daylist[-1] + 1
            else:
                daylist.append(1)
                current = coffee.when
        return (daylist, numdays)
        
def average_coffee_per_day(user):
    coffee_list, numday = coffee_per_day(user)
    if len(coffee_list) > 0:
        return 1.0 * sum(coffee_list) / numday # gotta make it float
    else:
        return 0
    
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
        timesince  = (datetime.datetime.utcnow() - latest.when).total_seconds()
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
        