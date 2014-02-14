import datetime, logging, numpy
from google.appengine.ext import db

gethours = lambda x: '%02d:%02d' % (abs(x), abs(60*(x - int(x))))
weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

def filter_outliers(data, min_pct, max_pct):
    min_val = numpy.percentile(data, min_pct)
    max_val = numpy.percentile(data, max_pct)
    return [d for d in data if d < max_val and d > min_val]
    
def get_timed_activities(user, act_name, orderby = 'end', order = 'desc', number = 0):
    userid = str(user.key().id())
    query = 'select * from TimedActivityModel where userid = \'%s\' and name = \'%s\' order by %s %s' % (userid, act_name, orderby, order)
    if number > 0:
        query += ' limit %d' % number
    activities = db.GqlQuery(query)
    return list(activities)
    
def timebetween_histogram(activities, unit = 'hours'):
    # activities are sorted in descending order!
    unit_scale = {'seconds':1, 'minutes':60, 'hours':(60*60), 'days':(60*60*24), 'weeks':(60*60*24*7)}
    activities = list(reversed(activities))
    timelist = []
    prev_act = activities[0]
    for act in activities[1:]:
        interval = (act.when - prev_act.when).total_seconds()
        timelist.append(interval)
        prev_act = act
    if unit == 'auto':
        mu_interval = numpy.mean(timelist)
        if mu_interval >= 60 and mu_interval < 3600:
            unit = 'minutes'
        elif mu_interval >= 3600 and mu_interval < (3600*24):
            unit = 'hours'
        elif mu_interval >= (3600*24) and mu_interval < (3600*24*7):
            unit = 'days'
        elif mu_interval >= (3600*24*7):
            unit = 'weeks'
    if not unit_scale.has_key(unit):
        unit = 'seconds'
    timelist = [t/unit_scale[unit] for t in timelist]
    # for a, b in zip(activities, timelist):
        # logging.error(a.when.strftime('%d/%m/%Y %H:%M') + '\t' + str(b))
    h, b = numpy.histogram(timelist, bins = numpy.ceil(numpy.sqrt(len(timelist))))
    return h, b, unit
    
def timeofday_histogram(activities):
    times = [act.when.hour + act.when.minute/60.0 for act in activities]
    h, b = numpy.histogram(times, bins = numpy.ceil(numpy.sqrt(len(times))))
    return h, b
    
def dayofweek_histogram(activities):
    days = [act.when.weekday() for act in activities]
    h, b = numpy.histogram(days, bins = range(0, 8))
    b = [weekdays[e] for e in b[0:-1]]
    return h, b
    
def dayofmonth_histogram(activities):
    days = [act.when.day for act in activities]
    h, b = numpy.histogram(days, bins = range(1, 32))
    return h, b
    
def general_activity_stats(user, actname):
    userid = str(user.key().id())
    activities = list(db.GqlQuery('select * from ActivityModel where userid = :1 order by when desc', userid))
    activities = [act for act in activities if act.name == actname]
    timeshift = datetime.timedelta(hours = user.timezone)
    for i in range(len(activities)):
        try:
            activities[i].when = activities[i].when + datetime.timedelta(hours = activities[i].timezone)
        except:
            activities[i].when = activities[i].when + timeshift
    status = {}
    if not activities:
        return status
        
    h, b = timeofday_histogram(activities)
    b = [gethours(e) for e in b]
    status['timeofday_histogram'] = zip(b, b[1:], h)
     
    h, b = dayofweek_histogram(activities)
    status['dayofweek_histogram'] = zip(b, b, h)
     
    h, b = dayofmonth_histogram(activities)
    status['dayofmonth_histogram'] = zip(b, b, h)
     
    h, b, u = timebetween_histogram(activities, unit='auto')
    status['timebetween_histogram'] = {'data': zip(b, b[1:], h), 'unit': u}
    return status

def sleep_stats(user):
    sleeps = get_timed_activities(user, 'sleep', number = 100)
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
            try:
                sleeps[i].end   = sleeps[i].end   + datetime.timedelta(hours = sleep[i].timezone)
                sleeps[i].start = sleeps[i].start + datetime.timedelta(hours = sleep[i].timezone)
            except:
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
        #logging.error(lastweek_end)
        
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
                
        totalday = (sleep_list[0][0] - sleep_list[-1][0]).days + 1
        alltime_average = 0
        if totalday > 0:
            alltime_average = alltime_total / totalday
            #logging.error('alltime_average is %2.2f' % alltime_average)
            status['alltime_average'] = alltime_average
        else:
            status['alltime_average'] = alltime_average
            
        if (today - sleeps[-1].end).days < 7:
            status['lastweek_average'] = 0
        else:
            status['lastweek_average'] = lastweek_total / 7.0
            
        # 7-day moving average
        r_sleep_list = list(reversed(sleep_list))
        mav7 = []
        if len(r_sleep_list) > 7:
            for i in  range(7, len(r_sleep_list)):
                mav7.append([r_sleep_list[i-1][0], sum([e[1] for e in r_sleep_list[(i-7):i]])/7.0])
        status['mav7'] = mav7
        # 30-day moving average
        mav30 = []
        if len(r_sleep_list) > 30:
            for i in range(30, len(r_sleep_list)):
                mav30.append([r_sleep_list[i-1][0], sum([e[1] for e in r_sleep_list[(i-30):i]])/30.0])
        status['mav30'] = mav30
        mav = []
        if len(mav7) > 10 and len(mav30) > 10:
            mav = [[a[0], a[1], b[1]] for a, b in zip(reversed(mav7), reversed(mav30))]
        status['mav'] = mav
        
        # sleep debts
        status['debt_by_lastweek'] = max(0, status['lastweek_average'] * (today.weekday() + 1) - thisweek_total)
        status['debt_by_alltime']  = max(0, status['alltime_average'] * (today.weekday() + 1) - thisweek_total)
        
        debt_list = []
        if alltime_average > 0:
            prev_debt = 0.0
            for sleep in reversed(sleep_list):
                if not debt_list:
                    debt_list.append([sleep[0], max(0.0, alltime_average - sleep[1])])
                else:
                    debt_list.append([sleep[0], max(0.0, prev_debt + alltime_average - sleep[1])])
                prev_debt = debt_list[-1][1]
                #logging.error('at date ' + sleep[0].strftime('%d/%m/%Y') + ' duration: %2.2f' %sleep[1] +' accumulated debt: %2.2f' % prev_debt)
                
        debt_list.reverse()
        status['debt_list'] = debt_list
        #logging.error('total days this week %d' % (today.weekday() + 1))
        #logging.error('total hours of sleep this week %d' % thisweek_total)
        
        sleep_list = [[a[0], a[1], b[1]] for a, b in zip(sleep_list, debt_list)]
        status['sleep_list'] = sleep_list
        sleep_hours_list = [elem[1] for elem in sleep_list]
        
        # sleep histogram
        sleep_hours_list = filter_outliers(sleep_hours_list, 5, 95)
        h, b = numpy.histogram(sleep_hours_list, bins = numpy.ceil(numpy.sqrt(len(sleep_list))))
        sleep_histogram = zip(b[:len(h)], b[1:len(h)+1], h)
        status['sleep_histogram'] = sleep_histogram
        return status

def coffee_stats(user):
    userid = str(user.key().id())
    coffees = get_activities(user, 'coffee', number = 500)
    status = {}
    
    if coffees:
        # hours since last cup
        status['last_cup'] = (datetime.datetime.utcnow() - coffees[0].when).total_seconds() / 3600.0
        
        # preprocessing
        timeshift = datetime.timedelta(hours = user.timezone)
        today = datetime.datetime.utcnow() + timeshift
        for i in range(len(coffees)):
            try:
                coffees[i].when = coffees[i].when + datetime.timedelta(hours = coffees[i].timezone)
            except:
                coffees[i].when = coffees[i].when + timeshift
        daysince = (today.date() - coffees[-1].when.date()).days
        
        coffee_times = [c.when.hour + c.when.minute/60.0 for c in coffees]
        h, b = numpy.histogram(coffee_times, bins = numpy.ceil(numpy.sqrt(len(coffee_times))))
        b = [gethours(e) for e in b]
        status['coffee_times_histogram'] = zip(b, b[1:], h)
        
        h, b = dayofweek_histogram(coffees)
        status['coffee_dayofweek_histogram'] = zip(b, b, h)
        
        h, b = dayofmonth_histogram(coffees)
        status['coffee_dayofmonth_histogram'] = zip(b, b, h)
        
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
    meals = get_meals(user, order = 'desc', number = 300)
    if not meals:
        return None
    meals.reverse()
        
    # pre-processing
    now = datetime.datetime.utcnow() + datetime.timedelta(hours = user.timezone)
    status = {}
    for i in range(len(meals)):
        try:
            meals[i].when += datetime.timedelta(hours = meals[i].timezone)
        except:
            meals[i].when += datetime.timedelta(hours = user.timezone)
        
    proper_meals = [meal for meal in meals if meal.category in ('breakfast', 'lunch', 'dinner')]
        
    status['latest_meal'] = proper_meals[-1]
    status['latest_hours_ago'] = (now - proper_meals[-1].when).total_seconds() / 3600.0
    
    getminutes = lambda meal: meal.when.hour + meal.when.minute/60.0
    brlist = filter_outliers([getminutes(meal) for meal in proper_meals if meal.category == 'breakfast'], 5, 95)
    lulist = filter_outliers([getminutes(meal) for meal in proper_meals if meal.category == 'lunch'], 5, 95)
    dilist = filter_outliers([getminutes(meal) for meal in proper_meals if meal.category == 'dinner'], 5, 95)
    
    gethours = lambda x: '%02d:%02d' % (abs(x), abs(60*(x - int(x))))
    h, b = numpy.histogram(brlist, bins = numpy.ceil(numpy.sqrt(len(brlist))))
    b = [gethours(e) for e in b]
    status['br_histogram'] = zip(b, b[1:], h)
    
    h, b = numpy.histogram(lulist, bins = numpy.ceil(numpy.sqrt(len(lulist))))
    b = [gethours(e) for e in b]
    status['lu_histogram'] = zip(b, b[1:], h)
    
    h, b = numpy.histogram(dilist, bins = numpy.ceil(numpy.sqrt(len(dilist))))
    b = [gethours(e) for e in b]
    status['di_histogram'] = zip(b, b[1:], h)

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
    
    showers  = get_activities(user, 'shower', number = 100)
    shaves   = get_activities(user, 'shave', number = 100)
    haircuts = get_activities(user, 'cut hair', number = 100)
    
    if len(showers) > 0:
        stats['shower']['latest'] = -1*(showers[0].when - datetime.datetime.utcnow()).total_seconds() / 3600.0
        shower_between = [(showers[i].when - showers[i+1].when).total_seconds()/3600.0 for i in range(len(showers) - 1)]
        shower_between = filter_outliers(shower_between, 5, 95)
        h, b = numpy.histogram(shower_between, bins = numpy.ceil(numpy.sqrt(len(shower_between))))
        shower_histogram = zip(b[:len(h)], b[1:len(h)+1], h)
        stats['shower']['histogram'] = shower_histogram
        stats['shower']['ave_interval'] = len(shower_between) > 0 and (sum(shower_between) / len(shower_between)) or 0
        try:
            shower_times = [(s.when.hour + s.when.minute/60.0 + s.timezone)%24 for s in showers]
        except:
            shower_times = [(s.when.hour + s.when.minute/60.0 + user.timezone)%24 for s in showers]
        h, b = numpy.histogram(shower_times, bins = numpy.ceil(numpy.sqrt(len(shower_times))))
        b = [gethours(e) for e in b]
        stats['shower']['times_histogram'] = zip(b, b[1:], h)
        
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
        
