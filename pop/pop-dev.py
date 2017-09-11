
# coding: utf-8

# In[1]:


"""

GET RECENT, POPULAR STORIES
 - Get DT
  > Build dict w/ only updates (published after 6 a.m today)
  > Merge local & sports (or not?)
 - Get CB
  > Create list of IDs (because order matters!) 
 - Loop over list and do lookups on merged dict to build HTML
 - Write file

UPDATED
 - 8/16/17
 - Rob Denton/The Register-Guard

TODO
 - Fix shit

"""


# In[30]:


from datetime import datetime, date
import boto3, requests, os, sys, json, pprint, re, logging, logging.handlers, copy
pp = pprint.PrettyPrinter(indent=4)


# In[3]:


"""
 --- SET TO TRUE IF TESTING, FALSE BEFORE YOU PUSH TO GITHUB/WAVE ---
"""

dev = False

if (dev == True):
    here = os.path.abspath('.')
else:
    here = sys.argv[0].split('/')
    here.pop()
    here = "/".join(here)


# In[4]:


# ----------------------------------------------------------------------------------------
# LOGGING INITIALIZATION
# ----------------------------------------------------------------------------------------

logger = logging.getLogger('logger')
# set level
if (dev == True):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.ERROR)

# set vars
log_file_dir = "{}/".format(here)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fileLogger = logging.handlers.RotatingFileHandler(filename=("{0}pop.log".format(log_file_dir)), maxBytes=256*1024, backupCount=5) # 256 x 1024 = 256K
fileLogger.setFormatter(formatter)
logger.addHandler(fileLogger)

"""
if (dev == True):
    # Uncomment below to print to console
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
"""

logger.debug("------------------")
logger.debug(" - ENTER - ENTER -")
logger.debug("vvvvvvvvvvvvvvvvvv")


# In[5]:


"""

get_secret() - Get secrets from secrets.json file

Requirements:
 - Global `here` variable that knows where project root is.

Arguments:
 - service: Name of service you need credentials for, should correspond to upper-level key
 - token: Name of token you need, should correspond to lower-level key

Example:
 - api_key = get_secret('twitter', 'secret')

"""
def get_secret(service, token='null'):
    secrets_path = here
    with open("{}/secrets.json".format(secrets_path)) as data:
        s = json.load(data)
        # If there is no token, return whole parent object
        if token == 'null':
            secret = s['{}'.format(service)]
        else:
            secret = s['{}'.format(service)]['{}'.format(token)]
        return secret


# In[6]:


"""

write_file() - Write file locally and to S3

Requirements:
 - Global `here` variable that knows where project root is.

Arguments:
 - contents: The long string you want to insert as the contents of the file

Example: 
 - write_file(html)

"""

def write_file(contents):
    f = open('{0}/html/index.html'.format(here), 'w+')
    f.write(contents.encode('ascii', 'xmlcharrefreplace'))
    f.close()
    if (dev == False):
        # Write to s3 (Comment out when testing)
        # See: https://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.upload_file
        s3 = boto3.resource('s3')
        # *** COMMENT OUT FOR DEV ***
        s3.meta.client.upload_file('{0}/html/index.html'.format(here),'uploads.registerguard.com','email/popular/index.html', ExtraArgs={'ContentType': "text/html", 'ACL': "public-read"})


# In[ ]:





# In[7]:


# Get clean datetime object from timestamp string
def clean_time(timestamp):
    # See: https://docs.python.org/2/library/datetime.html#datetime.datetime.strptime
    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return timestamp


# In[8]:


# Build dictionary of stories with CMS ID as key & dictionary of other data (like timestamp) as value
def id_stories(j):
    # Create empty dictionary
    stories = {}
    # Loop over stories
    for story in j['stories']:
        # Parse timestamp as datetime
        story['timestamp'] = clean_time(story['timestamp'])
        # Get CMS ID
        sid = story['id']
        # Get rid of extra values we don't need
        story.pop('id')
        story.pop('total')
        # Create dictionary
        stories[sid] = story
    return stories


# In[46]:


"""

get_stories() --- Go get stories from the RG's JSON feed

Arguments:
 - section (default: 'local'): This can be any valid section
 - area (default: 'Updates'): This can be any valide area
 - publication (default: 'rg'): This should always be 'rg'
 - items (default: None [API default: 50]): This is not necessary unless there is more than 50 (unlikely) or you want to limit the number returned
 - callback (default: None [API default: None]): This is only necessary if you want JSONP

Examples:
 - stories = get_stories()
 - stories = get_stories('sports','Top%20Updates')

"""
def get_stories(section='local',area='Updates',publication='rg',items=None,callback=None):
    # Set base URL
    url = 'http://registerguard.com/csp/cms/sites/rg/feeds/json02.csp'
    # Create params payload
    payload = {'publication': publication, 'section': section, 'area': area}
    if (items):
        payload['items'] = items
    if (callback):
        payload['callback'] = callback
    # Make request
    try:
        r = requests.get(url, params = payload)
    except:
        stories = None
        logger.error("REQUEST FAILED - {0}: {1}".format(url, payload))
    if (len(r.text)):
        d = r.text
        j = json.loads(d)
        #print(json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')))
        # Go build dictionary
        stories = id_stories(j)
    return stories

local = get_stories('local','Top Stories,Updates')
sports = get_stories('sports','Top Updates,Top Stories')

# Create combined DT dictionary from stories out of the system
dt = {}
dt.update(local)
dt.update(sports)
#logger.debug("dt set:\n{}".format(dt))


# In[ ]:





# In[40]:


def get_updates(d):
    # So you don't delete from dt
    #print(type(d))
    u = copy.copy(d)
    # Current datetime
    now = datetime.now()
    # Get datetime for 6 a.m. today
    logger.debug('now.year: {}'.format(now.year))
    logger.debug('now.month: {}'.format(now.month))
    logger.debug('now.day: {}'.format(now.day))
    then = datetime(now.year, now.month, now.day, 6, 0, 0)
    logger.debug("then: {}".format(then))
    for i in u.keys():
        logger.debug("{0}: {1}".format(u[i], u[i]['timestamp']))
        if u[i]['timestamp'] < then:
            logger.debug("old: {}".format(u[i]['headline']))
            del(u[i])
        else:
            logger.debug("new: {}".format(u[i]['headline']))
    return u

updates = get_updates(dt)
#print(len(updates))
#print("\n")
#print("dt")
#for i in dt:
#    print(dt[i]['timestamp'])
#print("updates")
#for i in updates:
#    print(updates[i]['timestamp'])"""


# In[41]:


logger.debug(len(updates))


# In[11]:


# Get CMS ID from URL
def get_id(url):
    # Take this:
    # //registerguard.com/rg/news/local/35849120-75/forest-fire-east-of-eugene-springfield-nears-1000-acres-burned.html.csp
    # and get:
    # 35849120
    m = re.search('\/([\d]+)\-[\d]+\/', url)
    cms_id = m.group(1)
    return cms_id


# In[12]:


# Get Chartbeat stories
#  - Create dictionary where keys are CMS IDs and values are dictionaries of data
def get_cb_stories(cb_json, count=20):
    # Create empty dictionary
    most = []
    # Create counter
    c = 0
    # Loop over stories in Chartbeat JSON response
    for i in cb_json['pages']:
        # Check on our count
        if (c <= count):
            # Check to see if it's an article (not alwasy perfect)
            if (i['stats']['type'] == 'Article'):
                # Get clean URL
                url = i['path']
                # Check to see if the domain is RG.com
                if (url.split("/")[0] == "registerguard.com"):
                    # Try to get CMS ID
                    try:
                        cms_id = get_id(url)
                    except:
                        logger.error("ERROR: BAD URL\n --- URL: {}".format(url))
                    # Check to see if you could get the CMS ID
                    if (cms_id != None):
                        # Add id to most
                        most.append(cms_id)
                        c = c + 1
    return most


# In[13]:


# Go out to Chartbeat API and get most popular stories right now
def get_chartbeat():
    # See: See: http://support.chartbeat.com/docs/api.html#toppages
    url = 'http://api.chartbeat.com/live/toppages/v3/'
    apikey = get_secret('chartbeat','apikey')
    domain = 'registerguard.com'
    types = 1
    limit = 50
    payload = { 'apikey': apikey, 'host': domain, 'types': types, 'limit': limit }
    # Make request
    try:
        r = requests.get(url, params=payload)
    except:
        most = None
        logger.error("REQUEST FAILED - {0}: {1}".format(url, payload))
    if (len(r.text)):
        cb_text = r.text
        cb_json = json.loads(cb_text)
        most = get_cb_stories(cb_json)
    return most


# In[47]:


# Set cb to Chartbeat dictionary
cb = get_chartbeat()
logger.debug("cb set:\n{}".format(cb))


# In[ ]:





# In[48]:


#print(len(updates))
#print(len(dt))

# Test to see if there are a few updates
# If fewer than 5 updates, then just pass all the dt stories to chartbeat
if (len(updates) < 5):
    system_stories = dt
# Otherwise, pass the updates to chartbeat
else:
    system_stories = updates

# Compare Chartbeat with stories from the system (either updates or all)
def get_pop(c, s):
    pop = []
    for i in c:
        if (i in s.keys()):
            one = {}
            one = s[i]
            one['id'] = i
            pop.append(one)
    logger.debug("length: {}".format(len(pop)))
    return pop

popular = get_pop(cb, system_stories)
#pp.pprint(popular)
#print(len(popular))
logger.debug("popular set:\n{}".format(popular))


# In[ ]:





# In[16]:


# Need to add in some logic if there aren't enough stories!!!


# In[ ]:





# In[35]:


# Create AP style time format
def get_datetime(pubdatetime):
    # Deal with date
    pubdate = date(pubdatetime.year, pubdatetime.month, pubdatetime.day)
    if (pubdate == date.today()):
        pubdate = "today"
    else:
        pubdate = pubdate.strftime('%b. %-d')
    # Deal with time
    # See: https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
    pubtime = pubdatetime.strftime('%I:%M')
    # Deal with a.m./p.m.
    ampm = pubdatetime.strftime('%p')
    if (ampm == "AM"):
        ampm = "a.m."
    elif (ampm == "PM"):
        ampm = "p.m."
    pubtime = u"{0} {1}".format(pubtime, ampm)
    return pubdate, pubtime


# In[49]:


#DoSomething with the list
# Maybe write_file()?
html = u""
for n, p in enumerate(popular):
    # Get clean data
    cat = p['category']
    pubdate, pubtime = get_datetime(p['timestamp'])
    logger.debug("{0} {1}".format(pubdate, pubtime))
    url = p['url']
    ymd = date.today().strftime('%Y%m%d')
    head = p['headline']
    if (n == 0):
        #img = p['image-medium']
        # In the future I'd like the lead visual to be stronger but don't have time now
        img = p['image-small']
    else:
        img = p['image-small']
    if len(img):
        html += u"<div class='img'>\n<a href='{0}'><img src='{1}' alt='Story img'></a></div>".format(url,img)
    # Do string concatenation (YUCK!)
    html += u"<h4>{}</h4>\n".format(cat)
    html += u"<h2><a href='{0}?utm_source=afternoon&utm_medium=email&utm_campaign=afternoon_{1}&utm_content=headline'>{2}</a></h2>".format(url,ymd,head)
    html += u"<p class='italic'>Published {0} at {1}</p>\n".format(pubdate, pubtime)
    html += u"<hr style='clear:both'>\n\n"


# In[50]:


logger.debug(html)
out = html
try:
    write_file(out)
except UnicodeEncodeError as err:
    logger.error("ERROR: {}\n----------------------------\n".format(err))
    logger.error(out)


# In[20]:


logger.debug("^^^^^^^^^^^^^^^^^^")
logger.debug("- EXIT ---- EXIT -")
logger.debug("------------------")


# In[ ]:




