import datetime, logging, numpy
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
        #logging.error('no sleep found')
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
        lastweek_start = today - datetime.timedelta(days = (today.weekday() + 7), hours = today.hour + today.minute/60.0)
        lastweek_end   = today - datetime.timedelta(days = today.weekday(), hours = today.hour + today.minute/60.0)
        logging.error(lastweek_end)
        
        sleep_list = []
        
        for sleep in sleeps:
            duration = (sleep.end - sleep.start).total_seconds() / 3600.0
            alltime_total += duration
            if sleep.end < lastweek_end and sleep.end > lastweek_start:
                lastweek_total += duration
                #logging.error('lastweek total %2.2f' % lastweek_total)
            elif sleep.end >= lastweek_end:
                thisweek_total += duration
                
            if not sleep_list:
                # if wake up before 7 PM, assign sleep to the same day, else assign to tomorrow
                if sleep.end.hour < 19:
                    sleep_list.append([sleep.end, duration])
                else:
                    sleep_list.append([sleep.end + datetime.timedelta(days = 1), duration])
            else:
                # recall that the list of sleeps is in descending order,
                # but sleep_list always appended at the end,
                # so the current day is at the end of the list
                
                # if the current sleep elem ends at the same day as the latest record,
                # add it to the latest record
                if sleep.end.day == sleep_list[-1][0].day:
                    sleep_list[-1][1] += duration
                # but if not (can only be the previous day, provided record is done fastidiously),
                # then check if the sleep ended 5 hours or fewer before the start of the day of
                # the latest record. If it is, add to latest record, else open a new day.
                
                # for example, if latest record is for 1-Nov, and current sleep ends at 23:00 of 
                # 31-Oct, then it is recorded for 1-Nov
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
        status['debt_by_lastweek'] = max(0, status['lastweek_average'] * (today.weekday() + 1) - thisweek_total)
        status['debt_by_alltime']  = max(0, status['alltime_average'] * (today.weekday() + 1) - thisweek_total)
        #logging.error('total days this week %d' % (today.weekday() + 1))
        #logging.error('total hours of sleep this week %d' % thisweek_total)
        
        # sleep histogram
        h, b = numpy.histogram([elem[1] for elem in sleep_list], bins = numpy.ceil(numpy.sqrt(len(sleep_list))))
        sleep_histogram = zip(b[:len(h)], b[1:len(h)+1], h)
        status['sleep_histogram'] = sleep_histogram
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
        daysince = (today.date() - coffees[-1].when.date()).days
        
        daily_cups = {}
        for i in range(daysince + 1):
            day = today - datetime.timedelta(days = i)
            daily_cups[day.date()] = 0
            
        # begin looping over list, filling status along the way
        for coffee in coffees:
            day = coffee.when
            daily_cups[day.date()] += 1

        daily_cups = daily_cups.items()
        daily_cups.sort(reverse = True)
        
        # retrieve today's total
        status['todays_total'] = daily_cups[0][1]
        
        # calculate alltime average
        if daysince > 0:
            status['alltime_average'] = len(coffees) / (1.0 * daysince)
        else:
            status['alltime_average'] = 0.0
            
        # report daily cups
        status['daily_cups'] = daily_cups
        
        # calculate daily cups histogram
        #h, b = numpy.histogram([elem[1] for elem in daily_cups], bins = numpy.ceil(numpy.sqrt(len(daily_cups))))
        #coffee_histogram = zip(b[:len(h)], b[1:len(h)+1], h)
        h, b = numpy.histogram([elem[1] for elem in daily_cups], bins = range(0, max([elem[1] for elem in daily_cups]) + 2))
        coffee_histogram = zip(b, b, h)
        status['coffee_histogram'] = coffee_histogram
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
    
def get_meals(user, order = 'desc', number = 0):
    userid = str(user.key().id())
    query = 'select * from MealModel where userid = \'%s\' order by when %s' % (userid, order)
    if number > 0:
        query += ' limit %d' % number
    meals = db.GqlQuery(query)
    return list(meals)
    
def meal_stats(user):
    meals = get_meals(user, order = 'asc')
    if not meals:
        return None
        
    # pre-processing
    now = datetime.datetime.utcnow() + datetime.timedelta(hours = user.timezone)
    status = {}
    for i in range(len(meals)):
        meals[i].when += datetime.timedelta(hours = user.timezone)
        
    proper_meals = [meal for meal in meals if meal.category in ('breakfast', 'lunch', 'dinner')]
        
    status['latest_meal'] = proper_meals[-1]
    status['latest_hours_ago'] = (now - proper_meals[-1].when).total_seconds() / 3600.0

    br_to_lu = []
    lu_to_di = []
    prev_meal = None
    for meal in proper_meals:
        if not prev_meal:
            prev_meal = meal
        else:
            if prev_meal.category == 'breakfast' and meal.category == 'lunch':
                if prev_meal.when.day == meal.when.day:
                    dt = (meal.when - prev_meal.when).total_seconds() / 3600.0
                    br_to_lu.append(dt)
            elif prev_meal.category == 'lunch' and meal.category == 'dinner':
                if prev_meal.when.day == meal.when.day:
                    dt = (meal.when - prev_meal.when).total_seconds() / 3600.0
                    lu_to_di.append(dt)
            prev_meal = meal
    
    if len(br_to_lu) > 0:
        status['mu_br_to_lu'] = sum(br_to_lu) / len(br_to_lu)
        h, b = numpy.histogram(br_to_lu, bins = numpy.ceil(numpy.sqrt(len(br_to_lu))))
        status['brlu_histogram'] = zip(b, b[1:], h)
    else:
        status['mu_br_to_lu'] = 0.0
        
    if len(lu_to_di) > 0:
        status['mu_lu_to_di'] = sum(lu_to_di) / len(lu_to_di)
        h, b = numpy.histogram(lu_to_di, bins = numpy.ceil(numpy.sqrt(len(lu_to_di))))
        status['ludi_histogram'] = zip(b, b[1:], h)
    else:
        status['mu_lu_to_di'] = 0.0
        
    return status
    
def hygiene_stats(user):
    stats = {}
    stats['shower'] = {}
    stats['shave'] = {}
    stats['haircut'] = {}
    
    showers  = get_activities(user, 'shower')
    shaves   = get_activities(user, 'shave')
    haircuts = get_activities(user, 'cut hair')
    
    if len(showers) > 0:
        stats['shower']['latest'] = -1*(showers[0].when - datetime.datetime.utcnow()).total_seconds() / 3600.0
        shower_between = [(showers[i].when - showers[i+1].when).total_seconds()/3600.0 for i in range(len(showers) - 1)]
        h, b = numpy.histogram(shower_between, bins = numpy.ceil(numpy.sqrt(len(shower_between))))
        shower_histogram = zip(b[:len(h)], b[1:len(h)+1], h)
        stats['shower']['histogram'] = shower_histogram
        stats['shower']['ave_interval'] = len(shower_between) > 0 and (sum(shower_between) / len(shower_between)) or 0
        
    if len(shaves) > 0:
        stats['shave']['latest'] = -1*(shaves[0].when - datetime.datetime.utcnow()).total_seconds() / (3600.0 * 24)
        shave_between = [(shaves[i].when - shaves[i+1].when).total_seconds()/(3600.0*24) for i in range(len(shaves) - 1)]
        stats['shave']['ave_interval'] = len(shave_between) > 0 and (sum(shave_between) / len(shave_between)) or 0
        
    if len(haircuts) > 0:
        stats['haircut']['latest'] = -1*(haircuts[0].when - datetime.datetime.utcnow()).total_seconds() / (3600.0 * 24)
        haircut_between = [(haircuts[i].when - haircuts[i+1].when).total_seconds()/(3600.0*24) for i in range(len(haircuts) - 1)]
        stats['haircut']['ave_interval'] = len(haircut_between) > 0 and (sum(haircut_between) / len(haircut_between)) or 0

    return stats
    
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
        #logging.error(str(timesince))
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
        
def guest_messages(user, number = 0):
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
        