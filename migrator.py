#!/usr/bin/python
from urllib.request import urlopen, Request
from tqdm import tqdm
from datetime import datetime
from os import system, path, name
import collections, ssl, sys, json

# States
STATE_INIT = 'Fetching GitLab events...'
STATE_LOAD = 'Creating commits...'
STATE_DONE = 'Done!\nGitHub status:'

# Values
CONTRIBUTIONS_COUNT = 'contributionsCount'
COMMIT_FILE = 'commit.md'
COMMIT_MESSAGE = '{{ "lastCommit" :  "{}", "contributionsCount" : {} }}'
DATE_FORMAT = '%Y-%m-%d'
ECHO_COMMIT = 'echo {} > commit.md'
GITLAB_URL = 'https://gitlab.com/users/{}/calendar.json'
LAST_COMMIT = 'lastCommit'
UNIX_EPOCH = '1970-01-01'
STRING_DATETIME = '{} 12:00:00'
USER_AGENT_KEY = 'User-Agent'
USER_AGENT_VALUE = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'

# OS
WINDOWS_NAME = 'nt'
WINDOWS_SETTER = 'set'
WINDOWS_DUMP_PATH = ''
UNIX_SETTER = 'export'
UNIX_DUMP_PATH = '> /dev/null'

# Commands
READ = 'r'
GIT_ADD_ALL = 'git add --all {}'
GIT_AUTHOR_DATE = '{} GIT_AUTHOR_DATE="{}"'
GIT_COMMITTER_DATE = '{} GIT_COMMITTER_DATE="{}"'
GIT_COMMIT_ALL = 'git commit --date="{}" -m "{}" {}'
GIT_STATUS = 'git status --ahead-behind'

# Errors
ERROR_FETCH_DATA = '''Could not fetch data from user {}
Are you sure that your user is correct and profile is public?'''
ERROR_ARGUMENTS = '''Arguments are wrong! Try running:
gitlab-migrator.py <username> [initialDate]
username: GitLab public username profile
initialDate(optional): Start commit date in YYYY-MM-DD format'''

def main(argv):
    print(STATE_INIT)
    events = getEvents(argv)

    print(STATE_LOAD)
    for stringDate, contributionsCount in tqdm(events.items()):
        createCommits(stringDate, contributionsCount),

    print(STATE_DONE)
    system(GIT_STATUS)

def getEvents(argv):
    try:
        if (len(argv) < 2):
            raise Exception()

        if path.exists(COMMIT_FILE):
            # Read data from previously md file
            cacheFile = open(COMMIT_FILE, READ)
            cacheData = json.loads(cacheFile.read())
        
            initialDateString = cacheData[LAST_COMMIT]
            contributionsCount = cacheData[CONTRIBUTIONS_COUNT]
        else:
            # Get initial commit date as an argument or fetch all commits
            initialDateString = argv[2] if len(argv) > 2 else UNIX_EPOCH
            contributionsCount = 0
    except:
        print(ERROR_ARGUMENTS)
        exit()

    # Request calendar from GitLab
    response = requestCalendar(argv)

    # Load response into python object
    calendar = json.loads(response)

    # Filter and order events
    events = parseCalendar(calendar, initialDateString, contributionsCount)

    return events

def createCommits(stringDate, contributionsCount):
    stringDateTime = STRING_DATETIME.format(stringDate)

    # Get variables based on OS
    if name != WINDOWS_NAME:
        # UNIX
        setter = UNIX_SETTER
        dumpPath = UNIX_DUMP_PATH
    else:
        # Windows
        setter = WINDOWS_SETTER
        dumpPath = WINDOWS_DUMP_PATH

    # Echo message into md and commit it for every contribution
    for i in range(contributionsCount):
        message = COMMIT_MESSAGE.format(stringDate, i + 1)

        # Echo message into md to enable commit of modified file
        system(ECHO_COMMIT.format(json.dumps(message)))
        
        # Set enviroment variables to allow past date commit
        system(GIT_COMMITTER_DATE.format(setter, stringDateTime))
        system(GIT_AUTHOR_DATE.format(setter, stringDateTime))

        # Add file and do commit to GitHub
        system(GIT_ADD_ALL.format(path))
        system(GIT_COMMIT_ALL.format(stringDateTime, message, dumpPath))

def requestCalendar(argv):
    try:
        # Sign default certificate to allow https request
        ssl._create_default_https_context = ssl._create_unverified_context

        # Headers to pass GitLab validation simulating a browser
        headers = { USER_AGENT_KEY : USER_AGENT_VALUE }
        
        # URL to fetch user commits data from calendar.json
        url = GITLAB_URL.format(argv[1])

        # Send request from URL and Headers
        request = urlopen(Request(url = url, headers = headers))
        
        # Fetch succesful decoded response
        response = request.read().decode()
    except:
        print(ERROR_FETCH_DATA.format(argv[1]))
        exit()

    return response

def parseCalendar(calendar, initialDateString, contributionsCount):
    # Filter days since 'initialDateString'
    calendarFiltered = { k: v for k, v in calendar.items() if isFirstDateStringBeforeSecond(k, initialDateString) }

    # Sort dictionary chronologically
    calendarOrdered = dict(sorted(calendarFiltered.items(), key=lambda item: item[0]))
    
    if initialDateString in calendarOrdered:
        # Remove already commited contributions
        calendarOrdered[initialDateString] -= contributionsCount

    # Return parsed dictionary
    return calendarOrdered

def isFirstDateStringBeforeSecond(date1, date2):
    return formatDateString(date1) >= formatDateString(date2)

def formatDateString(dateString):
    return datetime.strptime(dateString, DATE_FORMAT)

if __name__ == "__main__":
   main(sys.argv)
