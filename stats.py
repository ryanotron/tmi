import datetime, logging
from google.appengine.ext import db

def get_timed_activities(user, act_name, orderby = 'end', order = 'desc', number = 0):
    userid = str(user.key().id())
    query = 'select * from TimedActivityModel where userid = \'%s\' and name = \'%s\' order by %s %s' % (userid, act_name, orderby, order)
    if number > 0:
        query += ' limit %d' % number
    activities = db.GqlQuery(query)
    return list(activities)
    
def sleep_stats(user):
    sleeps = get_timed_activities(user, 'sleep')
    status = {}
    
    if not sleeps:
        logging.error('no sleep found')
        return None
    else:
        # pre-processing
        status = {}
        timeshift = datetime.timedelta(hours = user.timezone)
        today = datetime.datetime.utcnow() + timeshift
        
        for i in range(len(sleeps)):
            sleeps[i].end   = sleeps[i].end + timeshift
            sleeps[i].start = sleeps[i].start + timeshift # from now on, sleeps are in user's timezone
        
        # latest sleep
        status['latest_waketime'] = sleeps[0].end
        status['latest_duration'] = (sleeps[0].end - sleeps[0].start).total_seconds() / 3600.0
        
        # last week's average and all time average and this week's total
        lastweek_total = 0.0
        thisweek_total = 0.0
        alltime_total  = 0.0
        lastweek_start = today - datetime.timedelta(today.weekday() + 7)
        lastweek_end   = today - datetime.timedelta(today.weekday())
        
        sleep_list = []
        
        for sleep in sleeps:
            duration = (sleep.end - sleep.start).total_seconds() / 3600.0
            alltime_total += duration
            if sleep.end < lastweek_end and sleep.end > lastweek_start:
                lastweek_total += duration
                logging.error('lastweek total %2.2f' % lastweek_total)
            elif sleep.end > lastweek_end:
                thisweek_total += duration
                
            if not sleep_list:
                # if wake up before 7 PM, assign sleep to the same day, else assign to tomorrow
                if sleep.end.hour < 19:
                    sleep_list.append([sleep.end, duration])
                else:
                    sleep_list.append([sleep.end + datetime.timedelta(days = 1), duration])
            else:
                # recall that the list of sleeps is in descending order
                if sleep.end.day == sleep_list[-1][0].day:
                    sleep_list[-1][1] += duration
                else:
                    forward = sleep.end + datetime.timedelta(hours = 5)
                    if forward.day == sleep_list[-1][0].day:
                        sleep_list[-1][1] += duration
                    else:
                        sleep_list.append([sleep.end, duration])
        status['sleep_list'] = sleep_list
                
        totalday = (today - sleeps[-1].end).days
        if totalday > 0:
            status['alltime_average'] = alltime_total / totalday
        else:
            status['alltime_average'] = 0
            
        if (today - sleeps[-1].end).days < 7:
            status['lastweek_average'] = 0
        else:
            status['lastweek_average'] = lastweek_total / 7.0
        
        # sleep debts
        status['debt_by_lastweek'] = status['lastweek_average'] * today.weekday() - thisweek_total
        status['debt_by_alltime']  = status['alltime_average'] * today.weekday() - thisweek_total
        return status

def coffee_stats(user):
    userid = str(user.key().id())
    coffees = get_activities(user, 'coffee')
    status = {}
    
    if coffees:
        # hours since last cup
        status['last_cup'] = (datetime.datetime.utcnow() - coffees[0].when).total_seconds() / 3600.0
        
        # preprocessing
        timeshift = datetime.timedelta(hours = user.timezone)
        today = datetime.datetime.utcnow() + timeshift
        for i in range(len(coffees)):
            coffees[i].when = coffees[i].when + timeshift
            
        # begin looping over list, filling status along the way
        cups_per_day = []
        for coffee in coffees:
            if not cups_per_day:
                cups_per_day.append([coffee.when, 1])
            else:
                if coffee.when.day == cups_per_day[-1][0].day:
                    cups_per_day[-1][1] += 1
                else:
                    cups_per_day.append([coffee.when, 1])
        
        # retrieve today's total
        status['todays_total'] = cups_per_day[0][1]
        
        # calculate alltime average
        daysince = (today - coffees[-1].when).days
        if daysince > 0:
            status['alltime_average'] = len(coffees) / (1.0 * daysince)
        else:
            status['alltime_average'] = 0.0
            
        # report daily cups
        status['daily_cups'] = cups_per_day
        return status
    else:
        return None
    
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
        