
# coding: utf-8

# In[1]:


"""

CIVIL API 
 - Most commented

CREATED
 - 8/15/17
 - Rob Denton/The Register-Guard

TODO
 - Add logging

"""

import requests, json, boto3, os, sys, logging, logging.handlers


# In[2]:


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

#print(dev)


# In[3]:


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
fileLogger = logging.handlers.RotatingFileHandler(filename=("{0}civil.log".format(log_file_dir)), maxBytes=256*1024, backupCount=5) # 256 x 1024 = 256K
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
#print('logging')


# In[4]:


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
        s3.meta.client.upload_file('{0}/html/index.html'.format(here),'uploads.registerguard.com','email/civil/index.html', ExtraArgs={'ContentType': "text/html", 'ACL': "public-read"})


# In[5]:


def get_url(url):
    url = "http://{}".format(url)
    return url


# In[6]:


def get_civil():
    # See: "Feature request civil api" email from 10/10/16 with Christa Mrgan
    url = "https://app.civilcomments.com/api/v1/topics/most_commented.json"
    slug = "registerguard"
    days = 1
    payload = {"publication_slug": slug, "days_since": days}
    try:
        r = requests.get(url, params=payload)
    except:
        cv_json = None
        logger.error("REQUEST ERROR - {0}: {1}".format(url,params))
    if (len(r.text)):
        cv_json = r.json()
    return cv_json


# In[11]:


def analyze_civil(cv_json):
    # HTML
    html = u""
    # Control number of titles
    for n, i in enumerate(cv_json['topics']):
        # Get story variables
        url = get_url(i['url'])
        title = i['title']
        logger.debug(title)
        comments = i['comments_count']
        html += u"<h2>{0}) <a href='{1}' target='_blank'>{2}</a> – {3} comments</h2>\n<hr>\n".format(n+1, url, title, comments)
    return html


# In[12]:


cv = get_civil()
cv_html = analyze_civil(cv)

try:
    #logger.debug(cv_html)
    write_file(cv_html)
except:
    logger.error("WRITE ERROR - Cannot write_file")


# In[9]:


logger.debug("^^^^^^^^^^^^^^^^^^")
logger.debug(" - EXIT --- EXIT -")
logger.debug("------------------")

