
# coding: utf-8

# In[1]:


# This is a script to get recent stories from multiple DT sections and sort based on timestamp
# Rob Denton/The Register-Guard
# 9/12/17


# In[2]:


from datetime import datetime, date
import boto3, requests, os, sys, json, re, logging, logging.handlers, copy


# In[ ]:





# In[ ]:





# In[ ]:





# In[3]:


# Set path & dev, will succeed if run on cron
try:
    here = os.path.dirname(os.path.abspath(__file__))
    dev = False
except:
    here = os.path.abspath('.')
    dev = True
#print(here, dev)


# In[4]:


# Logging

logger = logging.getLogger('logger')

if (dev == True):
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.ERROR)

# set vars
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fileLogger = logging.handlers.RotatingFileHandler(filename=("{0}/rec.log".format(here)), maxBytes=256*1024, backupCount=5) # 256 x 1024 = 256K
fileLogger.setFormatter(formatter)
logger.addHandler(fileLogger)


# In[ ]:





# In[ ]:





# In[ ]:





# In[5]:


# Get clean datetime object from timestamp string
def clean_time(timestamp):
    # See: https://docs.python.org/2/library/datetime.html#datetime.datetime.strptime
    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return timestamp


# In[6]:


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


# In[7]:


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
        r = None
        logger.error(u"REQUEST FAILED - {0}: {1}".format(url, payload))
    if (len(r.text)):
        d = r.text
        j = json.loads(d)
        #print(json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')))
        # Go build dictionary
        stories = id_stories(j)
    return stories


# In[ ]:





# In[ ]:





# In[ ]:





# In[8]:


# Filter for only stories from today
def get_updates(d):
    # So you don't delete from dt, possibly needed later
    u = copy.copy(d)
    # Current datetime
    now = datetime.now()
    # Get datetime for 6 a.m. today
    #logger.debug('now.year: {}'.format(now.year))
    #logger.debug('now.month: {}'.format(now.month))
    #logger.debug('now.day: {}'.format(now.day))
    then = datetime(now.year, now.month, now.day, 6, 0, 0)
    #logger.debug("then: {}".format(then))
    for i in u.keys():
        logger.debug(u"{0}: {1}".format(i, u[i]['headline']))
        if u[i]['timestamp'] < then:
            logger.debug(u"old: {}".format(u[i]['timestamp']))
            del(u[i])
        else:
            logger.debug(u"new: {}".format(u[i]['timestamp']))
    return u


# In[ ]:





# In[ ]:





# In[ ]:





# In[20]:


# Get sorted list
def sort_updates(u):
    sort = []
    # Sort on timestamp
    #for k,v in sorted(u.iteritems(), key=lambda (k,v): (v['timestamp'],k), reverse=True):
    # Sort on popular
    for k,v in sorted(u.iteritems(), key=lambda (k,v): (v['popular'],k), reverse=True):
        logger.debug("{0}: {1}".format(k,v['timestamp']))
        sort.append(k)
    return sort


# In[ ]:





# In[ ]:





# In[ ]:





# In[10]:


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


# In[11]:


# Create HTML for file
def create_html(sorted_list, updates_dict):
    html = u""
    for i in sorted_list:
        # Get vars
        cat = updates_dict[i]['category']
        img = updates_dict[i]['image-small']
        url = updates_dict[i]['url']
        head = updates_dict[i]['headline']
        pubdate, pubtime = get_datetime(updates_dict[i]['timestamp'])
        ymd = date.today().strftime('%Y%m%d')
        # Do HTML
        if len(img):
            html += u"<div class='img'>\n<a href='{0}'><img src='{1}' alt='Story img'></a></div>".format(url,img)
        html += u"<h4>{}</h4>\n".format(cat)
        html += u"<h2><a href='{0}?utm_source=afternoon&utm_medium=email&utm_campaign=afternoon_{1}&utm_content=headline'>{2}</a></h2>".format(url,ymd,head)
        html += u"<p class='italic'>Published {0} at {1}</p>\n".format(pubdate, pubtime)
        html += u"<hr style='clear:both'>\n\n"
    return html


# In[ ]:





# In[ ]:





# In[ ]:





# In[12]:


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





# In[ ]:





# In[ ]:





# In[21]:


logger.debug("------------------")
logger.debug(" - ENTER - ENTER -")
logger.debug("vvvvvvvvvvvvvvvvvv")


# In[22]:


# Make request and sort stories into piles
local = get_stories('local','Breaking,Updates,Top Stories,Stories')
sports = get_stories('sports','Top Updates,Top Stories')
news = get_stories('news', 'Breaking,Top Updates')


# In[23]:


# Create combined dt dictionary from stories out of the system
dt = {}
dt.update(news)
dt.update(local)
dt.update(sports)
#logger.debug("dt set:\n{}".format(dt))


# In[24]:


updates = get_updates(dt)
logger.debug("len(updates): {}\n\n".format(len(updates)))


# In[25]:


sorted_updates = sort_updates(updates)


# In[26]:


my_html = create_html(sorted_updates, updates)

try:
    write_file(my_html)
except UnicodeEncodeError as err:
    logger.error("ERROR: {}\n----------------------------\n".format(err))
    logger.error(out)


# In[27]:


logger.debug("^^^^^^^^^^^^^^^^^^")
logger.debug(" - EXIT --- EXIT -")
logger.debug("------------------")


# In[ ]:




