import datetime, functools, hashlib, io, logging, random
from PIL import Image
from string import ascii_letters as letters

from flask import Flask, redirect, render_template, request, session, url_for
from google.appengine.api import wrap_wsgi_app
from google.appengine.ext import ndb

from calca import *
from models import *
from app_secrets import session_secret

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)
app.secret_key = session_secret

def securify_password(username, password, salt=None):
    if not salt:
        salt = ''.join([random.choice(letters) for i in range(5)])
    return hashlib.sha256((username + password + salt).encode()).hexdigest() + '|' + salt


def verify_password(username, password, hashedpw):
    [pw, salt] = hashedpw.split('|')
    return securify_password(username, password, salt) == hashedpw


def verify_user(username, password):
    users = UserModel.query(UserModel.username == username).fetch(1)
    if len(users) < 1:
        return False
    user = users[0]
    valid = verify_password(username, password, user.hashedpw)
    
    if valid:
        return user

    return False

def require_login(handler):
    @functools.wraps(handler)
    def wrap_require_login(*args, **kwargs):
        if not 'uid' in session:
            logging.error('no valid login')
            return redirect('/login')

        key = ndb.Key('UserModel', session['uid'])
        user = key.get()
        if not user:
            logging.error('user not found')
            return redirect('/login')

        return handler(user, *args, **kwargs)
    return wrap_require_login


@app.route('/')
def get_root():
    return redirect('/panel')


@app.route('/signup', methods=['GET'])
def get_signup():
    return render_template('signup.html')


@app.route('/signup', methods=['POST'])
def post_signup():
    username = request.form.get('username')
    password = request.form.get('password')
    verify = request.form.get('verify')
    betakey = request.form.get('betakey')

    # check beta key validity
    if not betakey:
        logging.error('no beta key provided')
        return render_template('signup.html')
    
    key_valid = False
    betakeys = BetaKeyModel.query(BetaKeyModel.keystring == betakey)
    for bkey in betakeys:
        if not bkey.used:
            key_valid = True
            break
    if not key_valid:
        logging.error('key is not valid')
        return render_template('signup.html')

    # validate username
    users = UserModel.query(UserModel.username == username).fetch()
    if len(users) > 0:
        logging.error('username is taken')
        return render_template('signup.html')

    # check password match
    if password != verify:
        logging.error('passwords do not match')
        return render_template('signup.html')

    # invalidate beta key
    bkey.used = True
    bkey.whenused = datetime.datetime.utcnow()
    bkey.put()

    # put new user
    new_user = UserModel(username=username,
                         hashedpw=securify_password(username, password),
                         nameday=datetime.datetime.utcnow(),
                         timezone=0.,
                         salutation='Agent',
                         last_seen=datetime.datetime.utcnow(),
                         nom_pronoun='it',
                         acc_pronoun='it',
                         pos_pronoun='its',
                         pos_determi='its')
    new_user.put()

    # invalidate session if any
    session.pop('uid', None)

    # start new session with new user
    session['uid'] = new_user.key.id()
    return redirect('/profile')


@app.route('/login', methods=['GET'])
def get_login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def post_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username and password:
        user = verify_user(username, password)
    
    if not user:
        return redirect('/')

    session['uid'] = user.key.id()
    return redirect('/panel')


@app.route('/logout', methods=['GET', 'POST'])
def any_logout():
    session.pop('uid', None)
    return redirect('/')


@app.route('/profile', methods=['GET'])
@require_login
def get_profile(user):
    return render_template('profile.html', user=user)


@app.route('/profile', methods=['POST'])
@require_login
def post_profile(user):
    # check for changed fields
    change = False
    new_salutation = request.form.get('salutation')
    if new_salutation != user.salutation:
        user.salutation = new_salutation
        change = True
    
    new_realname = request.form.get('realname')
    if new_realname != user.realname:
        user.realname = new_realname
        change = True

    new_timezone = request.form.get('timezone')
    try:
        new_timezone = float(new_timezone)
    except:
        new_timezone = 0.
    if new_timezone != user.timezone:
        user.timezone = new_timezone
        change = True

    new_nom = request.form.get("nom_pronoun")
    if new_nom != user.nom_pronoun:
        user.nom_pronoun = new_nom
        change = True
    
    new_acc = request.form.get("acc_pronoun")
    if new_acc != user.acc_pronoun:
        user.acc_pronoun = new_acc
        change = True

    new_pos = request.form.get("pos_pronoun")
    if new_pos != user.pos_pronoun:
        user.pos_pronoun = new_pos
        change = True

    new_pos = request.form.get("pos_determi")
    if new_pos != user.pos_determi:
        user.pos_determi = new_pos
        change = True

    if change:
        user.put()
    
    return redirect('/profile')


@app.route('/panel')
@require_login
def get_panel(user):
    t_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=user.timezone))\
            .strftime("%Y-%m-%dT%H:%M")
    
    return render_template('panel.html', user=user, t_str=t_str)


@app.route('/post_activity', methods=['POST'])
@require_login
def post_activity(user):
    name = request.form.get("name")
    when = request.form.get("when")
    timezone = request.form.get("timezone")
    now = int(request.form.get("now"))

    if now > 0:
        when = (datetime.datetime.utcnow() + datetime.timedelta(hours=user.timezone))\
               .strftime("%Y-%m-%dT%H:%M")
        timezone = user.timezone

    if name and when and timezone:
        pass
    else:
        logging.error("invalid input")
        return redirect('/panel')

    try:
        when_local = datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M")
    except:
        logging.error('malformed datetime')
        return redirect('/panel')

    try:
        timezone = float(timezone)
    except:
        logging.error('invalid timezone')
        return redirect('/panel')

    when_utc = when_local - datetime.timedelta(hours=timezone)
    new_act = ActivityModel(userid = str(user.key.id()),
                            name = name,
                            when = when_utc,
                            timezone = timezone)
    new_act.put()

    return redirect('/panel')


@app.route('/post_duration_activity', methods=['POST'])
@require_login
def post_duration_activity(user):
    name = request.form.get('name')
    start = request.form.get('start')
    end = request.form.get('end')
    timezone = request.form.get('timezone')

    if not (name and start and end and timezone):
        logging.error('input incomplete')
        return redirect('/panel')

    try:
        start_local = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M")
    except:
        logging.error('start time malformed')
        return redirect('/panel')

    try:
        end_local = datetime.datetime.strptime(end, "%Y-%m-%dT%H:%M")
    except:
        logging.error('end time malformed')
        return redirect('/panel')

    try:
        timezone = float(timezone)
    except:
        logging.error('invalid timezone')
        return redirect('/panel')

    start_utc = start_local - datetime.timedelta(hours=timezone)
    end_utc = end_local - datetime.timedelta(hours=timezone)

    new_act = TimedActivityModel(userid = str(user.key.id()),
                                 name = name,
                                 start = start_utc,
                                 end = end_utc,
                                 timezone = timezone)
    new_act.put()

    return redirect('/panel')


@app.route('/post_meal', methods=['POST'])
@require_login
def post_meal(user):
    category = request.form.get('category')
    menu = request.form.get('menu')
    where = request.form.get('where')
    when = request.form.get('when')
    timezone = request.form.get('timezone')

    if not (category and menu and where and when and timezone):
        return redirect('/panel')

    try:
        when_local = datetime.datetime.strptime(when, "%Y-%m-%dT%H:%M") 
    except:
        return redirect('/panel')

    try:
        timezone = float(timezone)
    except:
        return redirect('/panel')

    when_utc = when_local - datetime.timedelta(hours=timezone)
    new_meal = MealModel(userid = str(user.key.id()),
                         category = category,
                         menu = menu,
                         place = where,
                         when = when_utc,
                         timezone = timezone)
    new_meal.put()

    return redirect('/panel')


@app.route('/table', methods=['GET'])
@require_login
def get_table(user):
    messages = UserMessageModel.query(UserMessageModel.userid==str(user.key.id()))\
                               .order(-UserMessageModel.when)\
                               .fetch(4)

    messages_local = []
    for message in messages:
        t_local = message.when + datetime.timedelta(hours=user.timezone)
        messages_local.append([t_local, message.message])

    images = ImageModel.query(ImageModel.userid==str(user.key.id()),
                              ImageModel.category=="profile_img")\
                       .order(-ImageModel.uploaded)\
                       .fetch(8)

    img_keys = [img.key.id() for img in images]
    return render_template('table.html', 
        user=user, 
        messages=messages_local,
        imgs=img_keys)


@app.route('/coffee_stats', methods=['GET'])
@require_login
def get_coffee_stats(user):
    N_weeks = 26 # half a year
    now = datetime.datetime.now()
    then = now - datetime.timedelta(weeks=N_weeks)
    userid = str(user.key.id())

    coffees = ActivityModel.query(ActivityModel.userid == userid,
                                  ActivityModel.name == "coffee",
                                  ActivityModel.when >= then)\
                           .order(-ActivityModel.when)\
                           .fetch() 

    coffees = list(coffees)
    if len(coffees) == 0:
        return {}
    stats = calca_coffee(user, coffees)
    return stats


@app.route('/sleep_stats', methods=['GET'])
@require_login
def get_sleep_stats(user):
    now = datetime.datetime.utcnow()
    then = now - datetime.timedelta(weeks=26)
    sleeps = TimedActivityModel.query(TimedActivityModel.userid == str(user.key.id()),
                                      TimedActivityModel.name == 'sleep',
                                      TimedActivityModel.end >= then)\
                               .order(-TimedActivityModel.end)\
                               .fetch()

    sleeps = list(sleeps)
    if len(sleeps) == 0:
        return {}
    ret = calca_sleep(user, sleeps)
    return ret


@app.route('/meal_stats', methods=['GET'])
@require_login
def get_meal_stats(user):
    now  = datetime.datetime.utcnow()
    then = now - datetime.timedelta(weeks=26)
    meals = MealModel.query(MealModel.userid == str(user.key.id()),
                            MealModel.when >= then)\
                     .order(-MealModel.when)\
                     .fetch()
    meals = list(meals)
    if len(meals) == 0:
        return {}
    ret = calca_meal(user, meals)
    return ret


@app.route('/shower_stats', methods=['GET'])
@require_login
def get_shower_stats(user):
    now = datetime.datetime.utcnow()
    then = now - datetime.timedelta(weeks=26)
    showers = ActivityModel.query(ActivityModel.userid == str(user.key.id()),
                                  ActivityModel.when >= then,
                                  ActivityModel.name == 'shower')\
                           .order(-ActivityModel.when)\
                           .fetch()
    showers = list(showers)
    if len(showers) == 0:
        return {}
    ret = calca_shower(user, showers)
    return ret


@app.route('/post_message', methods=['POST'])
@require_login
def post_message(user):
    message = request.form.get('message')
    if len(message) <= 0:
        return redirect('/panel')

    when = datetime.datetime.utcnow()
    userid = str(user.key.id())
    new_message = UserMessageModel(userid=userid,
                                   message=message,
                                   when=when)
    new_message.put()
    return redirect('/panel')


@app.route('/img/<int:img_id>', methods=['GET'])
@require_login
def get_img(user, img_id):
    img_key = ndb.Key('ImageModel', img_id)
    img = img_key.get()
    if img:
        # check user privilege
        if not img.userid == str(user.key.id()):
            return redirect('/panel')

        return (img.image, {'Content-Type': 'image/png'})


@app.route('/post_img', methods=['POST'])
@require_login
def post_img(user):
    img_file = request.files['img_file']
    img_category = request.form.get('img_category')
    if not img_category:
        img_category = 'profile_img'
    
    if not img_file:
        logging.error('image upload failed')
        return redirect('/panel')

    # img_resize = libimg.resize(img_file.read(), height=150)
    try:
        img = Image.open(img_file)
    except:
        logging.error('failed to open image')
        return redirect('/panel')
    w, l = img.size
    w = 150 * w / l
    try:
        img_resize = img.resize((int(w), 150))
        img_bytes = io.BytesIO()
        img_resize.save(img_bytes, format='PNG')
    except:
        logging.error('failed to resize')
        return redirect('/panel')
    new_img = ImageModel(userid=str(user.key.id()),
                         image=img_bytes.getvalue(),
                         uploaded=datetime.datetime.utcnow(),
                         category=img_category)
    new_img.put()
    return redirect('/panel')


# ---- DEBUG ZONE ----

@app.route('/acts', methods=['GET'])
@require_login
def get_acts(user):
    now = datetime.datetime.utcnow()
    semester_ago = now - datetime.timedelta(weeks=26)
    acts = ActivityModel.query(ActivityModel.when >= semester_ago)\
                        .order(-ActivityModel.when)\
                        .fetch(10)
    acts_list = [(act.name, act.when) for act in acts]
    retval = {'username': user.username,
              'acts_list': acts_list}
    return retval


@app.route('/simulate_sleep', methods=['GET'])
@require_login
def get_simulate_sleep(user):
    dact_name = 'sleep'
    mean_hour_start = 0
    mean_hour_end = 8
    std_min = 15
    last_item = None
    dacts = TimedActivityModel.query(TimedActivityModel.userid == str(user.key.id()))\
                              .order(-TimedActivityModel.end)\
                              .fetch(1)
    for dact in dacts:
        last_item = dact

    now = datetime.datetime.utcnow()
    t_end = datetime.datetime(year = now.year, month=now.month, day=now.day,
        hour=mean_hour_end, minute=0, second=0)
    
    t_backstop = t_end - datetime.timedelta(weeks=26)
    if last_item:
        t_backstop = last_item.end

    t_start = datetime.datetime(year=t_end.year, month=t_end.month, day=t_end.day, 
        hour=mean_hour_start, minute=0)

    count = 0
    while t_end > t_backstop:
        t_fuzz = int(random.gauss(0, std_min))
        t_item_end = t_end + datetime.timedelta(minutes=t_fuzz)
        t_fuzz = int(random.gauss(0, std_min))
        t_item_start = t_start + datetime.timedelta(minutes=t_fuzz)

        t_end -= datetime.timedelta(days=1)
        t_start -= datetime.timedelta(days=1)

        new_item = TimedActivityModel(userid = str(user.key.id()),
            name=dact_name,
            start = t_item_start - datetime.timedelta(hours=user.timezone),
            end = t_item_end - datetime.timedelta(hours=user.timezone),
            timezone = user.timezone
            )
        
        new_item.put()
        count += 1

    return 'put {} items'.format(count)


@app.route('/simulate_meal', methods=['GET'])
@require_login
def get_simulate_meal(user):
    mean_hour_br = 8
    mean_hour_lu = 13
    mean_hour_di = 20

    std_min = 30
    now = datetime.datetime.utcnow()
    then = now - datetime.timedelta(weeks=26)

    date = now.date()
    count = 0
    userid = str(user.key.id())
    while date > then.date():
        # breakfast
        t_fuzz = int(random.gauss(0, std_min))
        when = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=mean_hour_br)
        when += datetime.timedelta(minutes=t_fuzz)
        when -= datetime.timedelta(hours=user.timezone)
        menu = "br"+str(count)
        place = "br"+str(count)
        category = "breakfast"
        new_meal = MealModel(userid=userid, when=when, menu=menu, place=place, category=category, timezone=user.timezone)
        new_meal.put()

        # lunch
        t_fuzz = int(random.gauss(0, std_min))
        when = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=mean_hour_lu)
        when += datetime.timedelta(minutes=t_fuzz)
        when -= datetime.timedelta(hours=user.timezone)
        menu = "lu"+str(count)
        place = "lu"+str(count)
        category = "lunch"
        new_meal = MealModel(userid=userid, when=when, menu=menu, place=place, category=category, timezone=user.timezone)
        new_meal.put()

        # dinner
        t_fuzz = int(random.gauss(0, std_min))
        when = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=mean_hour_di)
        when += datetime.timedelta(minutes=t_fuzz)
        when -= datetime.timedelta(hours=user.timezone)
        menu = "di"+str(count)
        place = "di"+str(count)
        category = "dinner"
        new_meal = MealModel(userid=userid, when=when, menu=menu, place=place, category=category, timezone=user.timezone)
        new_meal.put()

        count += 1
        date -= datetime.timedelta(days=1)

    return 'put {} meals'.format(count)

@app.route('/simulate_shower', methods=['GET'])
@require_login
def get_simulate_shower(user):
    mean_hour = 21
    std_min = 60
    now = datetime.datetime.utcnow()
    then = now - datetime.timedelta(weeks=26)

    date = now.date()
    count = 0
    userid = str(user.key.id())
    while date > then.date():
        t_fuzz = int(random.gauss(0, std_min))
        when = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=mean_hour)
        when += datetime.timedelta(minutes=t_fuzz)
        when -= datetime.timedelta(hours=user.timezone)
        new_shower = ActivityModel(userid=userid, name='shower', when=when, timezone=user.timezone)
        new_shower.put()
        count += 1
        date -= datetime.timedelta(days=1)

    return 'put {} showers'.format(count)