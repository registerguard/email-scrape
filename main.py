
# coding: utf-8

"""

COMBINED
 - Chartbeat API - Top pages
 - Civil API - Most commented

CREATED
 - 8/8/17
 - Rob Denton/The Register-Guard

TODO
 - Put up on Wave
 - Scrape into Cache

"""

import requests, json, boto3, os, sys

# Get absolute path
# *** THIS DIFFERS FROM JUPYTER ***
#here = os.path.abspath('.')
here = sys.argv[0].split('/')
here.pop()
here = "/".join(here)

def getSecret(service, token='null'):
    secrets_path = here
    #print "Service: {}".format(service)
    #print "Token: {}".format(token)
    with open("{}/secrets.json".format(secrets_path)) as data:
        s = json.load(data)
        #print s
        #print s['{}'.format(service)]['{}'.format(token)]
        # If there is no token, return whole parent object
        if token == 'null':
            secret = s['{}'.format(service)]
        else:
            secret = s['{}'.format(service)]['{}'.format(token)]
        return secret


# write file locally and on S3
def write_file(c, h):
    f = open('{0}/html/index.html'.format(h), 'w+')
    f.write(c)
    f.close()
    # See: https://boto3.readthedocs.io/en/latest/reference/services/s3.html#S3.Client.upload_file
    s3 = boto3.resource('s3')
    # *** COMMENT OUT FOR DEV ***
    s3.meta.client.upload_file('{0}/html/index.html'.format(h),'uploads.registerguard.com','email/index.html', ExtraArgs={'ContentType': "text/html", 'ACL': "public-read"})


def get_url(url):
    url = "//{}".format(url)
    return url


def get_chartbeat():
    # See: See: http://support.chartbeat.com/docs/api.html#toppages
    url = 'http://api.chartbeat.com/live/toppages/v3/'
    apikey = getSecret('chartbeat','apikey')
    domain = 'registerguard.com'
    types = 1
    limit = 30
    payload = { 'apikey': apikey, 'host': domain, 'types': types, 'limit': limit }
    r = requests.get(url, params=payload)
    cb_json = r.json()
    #print(cb_json)
    return cb_json


def analyze_chartbeat(cb_json):
    # HTML
    html = "<section>\n"
    html += "\t<h1>Most popular stories</h1>\n"
    # Control number of titles
    count = 0
    for i in cb_json['pages']:
        # Limit to ten
        if (count < 10):
            # Control Article vs. LandingPage
            if (i['stats']['type'] == 'Article'):
                # Get story variables
                url = get_url(i['path'])
                # Get rid of extraneous title info
                title = i['title']
                #title = title.decode()
                title = title.split(" | ")
                title = title[0]
                # Check for length
                if (len(title) == 100):
                    # Split on spaces and remove last word fragment
                    t = title.split(" ")[:-1]
                    # Put humpty dumpty back together
                    t = " ".join(t)
                    # Add ellipsis
                    title = u"{} \u2026".format(t)
                html += u"\t<h3><a href='{0}' target='_blank'>{1}</a></h3>\n".format(url, title)
                count = count + 1
    html += "</section>\n"
    return html


def get_civil():
    # See: "Feature request civil api" email from 10/10/16 with Christa Mrgan
    url = "https://app.civilcomments.com/api/v1/topics/most_commented.json"
    slug = "registerguard"
    days = 1
    payload = {"publication_slug": slug, "days_since": days}
    r = requests.get(url, params=payload)
    cv_json = r.json()
    #print cv_json
    return cv_json


def analyze_civil(cv_json):
    # HTML
    html = "<section>\n"
    html += "\t<h1>Most commented stories</h1>\n"
    # Control number of titles
    for i in cv_json['topics']:
        # Get story variables
        url = get_url(i['url'])
        title = i['title']
        comments = i['comments_count']
        html += u"\t<h3><a href='{0}' target='_blank'>{1} ({2} comments)</a></h3>\n".format(url, title, comments)
    html += "</section>\n"
    return html


cb = get_chartbeat()
cb_html = analyze_chartbeat(cb)

cv = get_civil()
cv_html = analyze_civil(cv)

utf = "<meta charset='utf-8'>"

code = u"{0}\n{1}\n{2}".format(utf, cb_html, cv_html)
code = code.encode('utf-8')

write_file(code,here)
