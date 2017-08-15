
# coding: utf-8

# In[188]:


from datetime import datetime
import boto3, requests, os, sys, json, pprint, re
pp = pprint.PrettyPrinter(indent=4)


# In[189]:


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


# In[190]:


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


# In[191]:


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
    f.write(contents)
    f.close()
    # Write to s3 (Comment out when testing)
    #"""
    # See: https://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.upload_file
    s3 = boto3.resource('s3')
    # *** COMMENT OUT FOR DEV ***
    s3.meta.client.upload_file('{0}/html/index.html'.format(here),'uploads.registerguard.com','email/popular/index.html', ExtraArgs={'ContentType': "text/html", 'ACL': "public-read"})
    #"""


# In[ ]:





# In[192]:


# Get clean datetime object from timestamp string
def clean_time(timestamp):
    # See: https://docs.python.org/2/library/datetime.html#datetime.datetime.strptime
    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return timestamp


# In[193]:


# Build dictionary of stories with CMS ID as key & dictionary of other data (like timestamp) as value
def id_stories(j):
    # Create empty dictionary
    stories = {}
    # Loop over stories
    for story in j['stories']:
        # Get CMS ID
        sid = story['id']
        # Get rid of extra values we don't need
        story.pop('id')
        story.pop('total')
        # Parse timestamp as datetime
        story['timestamp'] = clean_time(story['timestamp'])
        # Create dictionary
        stories[sid] = story
    return stories


# In[194]:


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
    r = requests.get(url, params = payload)
    d = r.text
    j = json.loads(d)
    #print(json.dumps(j, sort_keys=True, indent=4, separators=(',', ': ')))
    # Go build dictionary
    stories = id_stories(j)
    return stories

local = get_stories('local','Top Stories,Updates')
sports = get_stories('sports','Top Updates')

# Create combined DT dictionary from stories out of the system
dt = {}
dt.update(local)
dt.update(sports)


# In[ ]:





# In[195]:


# Make sure URL is clean and does not have protocol
def get_url(url):
    url = "http://{}".format(url)
    return url


# In[196]:


"""
 --- NOT NEEDED BECAUSE WE'LL GET HEADLINE FROM UPDATES ---
"""
# Clean headlines
#  - Chartbeat will trim headlines at 100 characters
def check_length(title):
    if (len(title) == 100):
        # Split on spaces and remove last word fragment
        t = title.split(" ")[:-1]
        # Put humpty dumpty back together
        t = " ".join(t)
        # Add ellipsis
        title = u"{} \u2026".format(t)
        return title


# In[197]:


"""
 --- NOT NEEDED BECAUSE WE'LL GET HEADLINE FROM UPDATES ---
"""
# Clean headlines
#  - Chartbeat pulls page titles so headlines need to have pipes removed
def clean_title(title):
    title = title.split(" | ")
    title = title[0]
    check_length(title)
    return title


# In[198]:


# Get CMS ID from URL
def get_id(url):
    # Take this:
    # //registerguard.com/rg/news/local/35849120-75/forest-fire-east-of-eugene-springfield-nears-1000-acres-burned.html.csp
    # and get:
    # 35849120
    m = re.search('\/([\d]+)\-[\d]+\/', url)
    cms_id = m.group(1)
    return cms_id


# In[199]:


# Get Chartbeat stories
#  - Create dictionary where keys are CMS IDs and values are dictionaries of data
def get_cb_stories(cb_json, count=30):
    # Create empty dictionary
    most = {}
    # Create counter
    c = 0
    # Loop over stories in Chartbeat JSON response
    for i in cb_json['pages']:
        # Check on our count
        if (c <= count):
            # Check to see if it's an article (not alwasy perfect)
            if (i['stats']['type'] == 'Article'):
                # Get clean URL
                url = get_url(i['path'])
                # Check to see if the domain is RG.com
                if (url.split("/")[2] == "registerguard.com"):
                    # Try to get CMS ID
                    try:
                        cms_id = get_id(url)
                    except:
                        print("ERROR: Not a proper registerguard.com url\n --- URL: {}".format(url))
                    # Check to see if you could get the CMS ID
                    if (len(cms_id)):
                        # Set CMS ID to URL
                        most[cms_id] = url
                        c = c + 1
    return most


# In[200]:


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
    r = requests.get(url, params=payload)
    cb_text = r.text
    cb_json = json.loads(cb_text)
    most = get_cb_stories(cb_json)
    return most


# In[201]:


# Set cb to Chartbeat dictionary
cb = get_chartbeat()


# In[ ]:





# In[202]:


# See what stories are both recent and popular
def get_recent_popular(pop_cb, pop_dt):
    # Current datetime
    now = datetime.now()
    # Get datetime for 6 a.m. today
    then = datetime(now.year, now.month, now.day, 6, 0, 0)
    # Create empty list
    pop = []
    # Loop over Chartbeat stories (so that this is the order)
    for s in pop_cb:
        # Check to see if the story is in the DT list
        if s in pop_dt:
            # Set story timestamp
            timestamp = pop_dt[s]['timestamp']
            # Check to see if that story was published after 6 a.m. today
            if timestamp > then:
                # Add that story's CMS ID to the pop list
                pop.append(s)
    return pop
            


# In[203]:


# Get the list of CMS IDs of the most popular stories that were published after 6 a.m. today
popular = get_recent_popular(cb, dt)


# In[ ]:





# In[204]:


# Need to add in some logic if there aren't enough stories!!!


# In[ ]:





# In[205]:


# Create AP style time format
def get_pubtime(pubtime):
    # See: https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
    pt = pubtime.strftime('%I:%M')
    apm = pubtime.strftime('%p')
    if (apm == "AM"):
        apm = "a.m."
    elif (apm == "PM"):
        apm = "p.m."
    pubtime = u"{0} {1}".format(pt, apm)
    return pubtime


# In[206]:


#DoSomething with the list
# Maybe write_file()?
html = u""
for p in popular:
    # Get clean data
    cat = dt[p]['category']
    pubtime = get_pubtime(dt[p]['timestamp'])
    url = cb[p]
    ymd = u"{0}{1}{2}".format(datetime.now().year,datetime.now().month,datetime.now().day)
    head = dt[p]['headline']
    # Do string concatenation (YUCK!)
    html += u"<h4>{}</h4>\n".format(cat)
    html += u"<h2><a href='{0}?utm_source=afternoon&utm_medium=email&utm_campaign=afternoon_{1}&utm_content=headline'>{2}</a></h2>".format(url,ymd,head)
    html += u"<p>Published today at: {}\n".format(pubtime)
    html += u"<hr style='clear:both'>\n\n"


# In[207]:


out = html
out = out.replace( u'\u2018', u"'")
out = out.replace( u'\u2019', u"'")
out = out.replace( u'\u201c', u'"')
out = out.replace( u'\u201d', u'"')
out.encode('utf-8')
try:
    write_file(out)
except UnicodeEncodeError as err:
    print("ERROR: {}\n----------------------------\n".format(err))
    print(out)


# In[ ]:




