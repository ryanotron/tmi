import re, os
import stats
import jinja2, datetime

username_re = re.compile(r'^[a-zA-Z_-]{4,20}$')
password_re = re.compile(r'^.{4,20}$')
email_re    = re.compile(r'^[\S]+@[\S]+.[\S]+$')
batchexpense_re = re.compile(r'[^\d]+(?P<when>\d{1,2}/\d{1,2}/\d{4})\t(?P<name>[^\t]+)\t(?P<amount>\d+.\d+)\t(?P<cat>[^\t]+)')
datetime_re = re.compile(r'\s*(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})')

COOKIESECRET = 'Fire and Blood!'

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinjaenv = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)
jinjaenv.globals['datetime'] = datetime
jinjaenv.globals['stats'] = stats