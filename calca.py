import datetime, logging, math
from models import *

def frange(start, stop, step=1.):
    val = start
    while True:
        yield val

        val += step
        if step < 0 and val <= stop:
            break
        elif step > 0 and val >= stop:
            break


def histo(data, bins):
    counts = [0] * (len(bins)-1)
    for datum in data:
        for i in range(1, len(bins)):
            if datum >= bins[i-1] and datum < bins[i]:
                counts[i-1] += 1
                break
    return counts

def draw_histo(bins, counts, n=20):
    c_min = min(counts)
    c_max = max(counts)
    delta = (c_max - c_min) / n

    stars = []
    for i, count in enumerate(counts):
        star_count = int(math.floor(count/delta))
        star = '{:03.0f} '.format(bins[i])
        star += '*' * star_count
        stars.append(star)

    return stars


def calca_coffee(user, coffees):
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=user.timezone)
    then = coffees[-1].when + datetime.timedelta(hours=user.timezone)
    
    counts = {}
    day = then.date()
    while day <= now.date():
        counts[day] = 0
        day += datetime.timedelta(days=1)

    N = 0
    tods = []
    mean_tod = 0.
    for coffee in coffees:
        # get time of day
        tee = coffee.when + datetime.timedelta(hours=coffee.timezone)
        counts[tee.date()] += 1
        N += 1
        tod = tee.hour + tee.minute/60.
        tods.append(tod)
        mean_tod += tod

    mean_tod /= N
    tod_bins = list(frange(0, 25, 0.5))
    tod_histo = histo(tods, tod_bins)

    mean_daily_count = 0
    max_daily_count = 0
    for count in counts.values():
        mean_daily_count += count
        if count > max_daily_count:
            max_daily_count = count
    mean_daily_count /= len(counts.keys())
    daily_count_bins = range(0, max_daily_count+2, 1)
    daily_count_histo = histo(counts.values(), daily_count_bins)

    daily_count_timeline = [[k, v] for k, v in counts.items()]
    daily_count_timeline = sorted(daily_count_timeline, key=lambda x: x[0])

    latest = coffees[0].when + datetime.timedelta(hours=coffees[0].timezone)
    dt_latest = (datetime.datetime.utcnow() - coffees[0].when).total_seconds() / 3600.

    latest_str = '{:.2f} hours ago, {} UTC{:+.0f}'.format(
        dt_latest,
        latest.strftime('%H:%M %d-%b-%Y'),
        coffees[0].timezone
    )

    cups_today = counts[now.date()]
    a = math.floor(mean_tod)
    b = mean_tod - a
    mean_tod_str = '{:.0f}:{:.0f}'.format(a, b*60)

    res = {'latest_str': latest_str,
           'cups_today': cups_today, 
           'mean_tod': mean_tod_str,
           'mean_daily_count': mean_daily_count,
           'max_daily_count': max_daily_count,
           'tod_histo': tod_histo,
           'tod_bins': tod_bins,
           'daily_count_histo': daily_count_histo,
           'daily_count_bins': daily_count_bins,
           'daily_count_timeline': daily_count_timeline
          }

    return res


def calca_sleep(user, sleeps):
    # prep duration timeline
    dur_timeline = {}
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=user.timezone)
    then = sleeps[-1].end + datetime.timedelta(hours=user.timezone)
    day = now.date()
    while day >= then.date():
        dur_timeline[day] = 0
        day -= datetime.timedelta(days=1)

    # prep wake timeofday
    wake_series = []

    # prep sleep timeofday
    sleep_series = []

    # process series
    for sleep in sleeps:
        dur = (sleep.end - sleep.start).total_seconds() / 3600.
        date_key = sleep.end + datetime.timedelta(hours=user.timezone)
        if date_key.date() in dur_timeline:
            dur_timeline[date_key.date()] += dur
        else:
            dur_timeline[date_key.date()] = 0.

        start = sleep.start + datetime.timedelta(hours=sleep.timezone)
        end = sleep.end + datetime.timedelta(hours=sleep.timezone)

        wake_series.append((end.hour + end.minute/60.) % 24)
        sleep_series.append((start.hour + start.minute/60.) % 24 )

    # flatten duration
    dur_series = [[k, v, 0] for k, v in dur_timeline.items()]
    dur_series = sorted(dur_series, key=lambda x: x[0])

    # half-year mean
    semester_mean = sum([row[1] for row in dur_series]) / 1. / len(dur_series)

    # daily deficit, mav7, mav28
    mavs7 = []
    mavs28 = []
    for i in range(len(dur_series)):
        dur_series[i][2] = semester_mean - dur_series[i][1]
        if i < 7:
            mav7 = sum([dur[1] for dur in dur_series[:i+1]]) / (i+1.)
        else:
            mav7 = sum([dur[1] for dur in dur_series[i-7+1:i+1]]) / 7.
        mavs7.append(mav7)

        if i < 28:
            mav28 = sum([dur[1] for dur in dur_series[:i+1]]) / (i+1.)
        else:
            mav28 = sum([dur[1] for dur in dur_series[i-28+1:i+1]]) / 28.

        mavs28.append(mav28)
    
    # last week mean
    idx_last_monday = len(dur_series)-1 - now.weekday() - 7
    n = 7.
    if idx_last_monday < 0:
        idx_last_monday = 0
        n = len(dur_series)
    last_week_mean = sum([dur[1] for dur in dur_series[idx_last_monday:idx_last_monday+7]]) / n

    idx_this_monday = len(dur_series)-1 - now.weekday()
    idx_this_monday = max(0, idx_this_monday)
    week_deficit = sum(dur[2] for dur in dur_series[idx_this_monday:])
    
    # duration histo
    dur_bins = list(frange(0, 24.5, 0.5))
    dur_histo = histo([row[1] for row in dur_series], dur_bins)

    dur_bins_str = []
    for i in range(len(dur_bins)-1):
        dur_bin_str = '[{:.1f}, {:.1f})'.format(dur_bins[i], dur_bins[i+1])
        dur_bins_str.append(dur_bin_str)

    # wake/bedtime histo
    wake_bins = list(frange(0, 24.5, 0.5))
    wake_histo = histo(wake_series, wake_bins)
    sleep_histo = histo(sleep_series, wake_bins)

    wake_bins_str = []
    for i in range(len(wake_bins)-1):
        wake_bin_str = '[{:.1f}, {:.1f})'.format(wake_bins[i], wake_bins[i+1])
        wake_bins_str.append(wake_bin_str)

    latest = sleeps[0]
    dt_latest = (datetime.datetime.utcnow() - latest.end).total_seconds() / 3600.
    latest_str = '{} UTC{:+.0f}, {:.2f} hours ago'.format(
        (latest.end + datetime.timedelta(hours=latest.timezone)).strftime('%H:%M, %d-%b-%Y'),
        latest.timezone,
        dt_latest
    )

    res = {'semester_mean': semester_mean,
           'last_week_mean': last_week_mean,
           'week_deficit': week_deficit,
           'dur_series': dur_series,
           'mavs7': mavs7,
           'mavs28': mavs28,
           'dur_bins': dur_bins_str,
           'dur_histo': dur_histo,
           'wake_bins': wake_bins_str,
           'wake_histo': wake_histo,
           'sleep_histo': sleep_histo,
           'latest_str': latest_str,
          }

    return res


def calca_meal(user, meals):
    breakfast_times = []
    lunch_times = []
    dinner_times = []

    # collect meal time of day
    for meal in meals:
        mealtime_local = meal.when + datetime.timedelta(hours=meal.timezone)
        meal_tod = mealtime_local.hour + mealtime_local.minute/60.
        if meal.category == 'breakfast':
            breakfast_times.append(meal_tod)
        elif meal.category == 'lunch':
            lunch_times.append(meal_tod)
        elif meal.category == 'dinner':
            dinner_times.append(meal_tod)

    # compute histograms
    bins = list(frange(0, 24.5, 0.5))
    breakfast_histo = histo(breakfast_times, bins)
    lunch_histo = histo(lunch_times, bins)
    dinner_histo = histo(dinner_times, bins)

    # convert bins to string
    bins_str = []
    for i in range(len(bins)-1):
        bin_str = '[{:4.1f}, {:4.1f})'.format(bins[i], bins[i+1])
        bins_str.append(bin_str)

    # repackage latest
    latests = []
    latest_string = '<ul>'
    for meal in meals[:3]:
        latests.append({'when': meal.when + datetime.timedelta(hours=meal.timezone),
                        'category': meal.category,
                        'menu': meal.menu,
                        'place': meal.place})
        latest_string += '<li>{}, {}, {} at {}</li>'.format(
            latests[-1]['when'].strftime('%Y-%b-%d, %H:%M'),
            meal.category,
            meal.menu,
            meal.place
        )
    latest_string += '</ul>'

    # prep return value
    res = {'latest': latests,
           'latest_str': latest_string, 
           'time_bins': bins_str,
           'breakfast_histo': breakfast_histo,
           'lunch_histo': lunch_histo,
           'dinner_histo': dinner_histo}

    return res


def calca_shower(user, showers):
    t_showers = []
    dt_showers = []

    mean_dt = 0.
    for i, shower in enumerate(showers):
        t_local = shower.when + datetime.timedelta(hours=shower.timezone)
        tod = t_local.hour + t_local.minute/60.
        t_showers.append(tod)

        if i >= 1:
            t_prev_local = showers[i-1].when + datetime.timedelta(hours=showers[i-1].timezone)
            dt = (t_prev_local - t_local).total_seconds() / 3600.
            dt_showers.append(dt)
            mean_dt += dt
    mean_dt = mean_dt / (len(showers)-1)

    t_bins = list(frange(0, 24.5, 0.5))
    dt_bins = list(range(6, 55, 1))

    t_histo = histo(t_showers, t_bins)
    dt_histo = histo(dt_showers, dt_bins)

    t_bins_str = []
    for i in range(len(t_bins)-1):
        t_str = '[{:.1f}, {:.1f})'.format(t_bins[i], t_bins[i+1])
        t_bins_str.append(t_str)

    dt_bins_str = []
    for i in range(len(dt_bins)-1):
        dt_str = '[{:.0f}, {:.0f})'.format(dt_bins[i], dt_bins[i+1])
        dt_bins_str.append(dt_str)

    latest_dt = (datetime.datetime.utcnow() - showers[0].when).total_seconds() / 3600.
    latest_str = '{:.2f} hours ago, '.format(latest_dt)
    
    latest_str += (showers[0].when + datetime.timedelta(hours=showers[0].timezone))\
                 .strftime('%H:%M, %d-%b-%Y')
    latest_str += ' UTC{:+.1f}'.format(showers[0].timezone)

    res = {'latest': latest_str,
           'mean_dt': '{:.2f}'.format(mean_dt),
           't_bins': t_bins_str,
           't_histo': t_histo,
           'dt_bins': dt_bins_str,
           'dt_histo': dt_histo}

    return res