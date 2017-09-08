
# coding: utf-8

# In[135]:


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


# In[136]:


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


# In[137]:


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


# In[138]:


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


# In[139]:


def get_url(url):
    url = "http://{}".format(url)
    return url


# In[140]:


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


# In[141]:


def analyze_civil(cv_json):
    # HTML
    html = u"<table class='ol'>\n"
    # Control number of titles
    for n, i in enumerate(cv_json['topics']):
        # Get story variables
        url = get_url(i['url'])
        title = i['title']
        logger.debug(title)
        comments = i['comments_count']
        # Concatenate some HTML
        html += u"\t<tr>\n"
        html += u"\t\t<td align='left' valign='top' class='title'>{0}.</td>\n".format(n+1)
        html += u"\t\t<td align='left' valign='top' class='title'><a href='{0}' target='_blank'>{1}</a> – {2} comments</td>\n".format(url, title, comments)
        html += u"\t</tr>\n"
    html += u"</table>"
    return html


# In[142]:


cv = get_civil()
cv_html = analyze_civil(cv)

try:
    #logger.debug(cv_html)
    write_file(cv_html)
except:
    logger.error("WRITE ERROR - Cannot write_file")


# In[143]:


logger.debug("^^^^^^^^^^^^^^^^^^")
logger.debug(" - EXIT --- EXIT -")
logger.debug("------------------")

