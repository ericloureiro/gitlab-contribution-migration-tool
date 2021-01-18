#!/usr/bin/python
from urllib.request import urlopen, Request
from datetime import datetime
from tqdm import tqdm
import os, collections, ssl, sys, json

# States
STATE_INIT = 'Fetching GitLab events...'
STATE_LOAD = 'Creating commits...'
STATE_DONE = 'Done!\nGitHub status:'
GIT_STATUS = 'git status --ahead-behind'

# Values
COUNTER = 'i'
COMMITS_COUNT = 'commitsCount'
COMMIT_FILE = 'commit.md'
DATE_FORMAT = '%Y-%m-%d'
LAST_COMMIT = 'lastCommit'
READ = 'r'
UNIX_EPOCH = '1970-01-01'
USER = 'user'
USER_AGENT_KEY = 'User-Agent'
USER_AGENT_VALUE = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.3'

# OS
WINDOWS_NAME = 'nt'
WINDOWS_DUMP_PATH = 'NUL'
WINDOWS_SETTER = 'set'
UNIX_DUMP_PATH = '/dev/null'
UNIX_SETTER = 'export'

# Errors
ERROR_FETCH_DATA = '''Could not fetch data from user {}
Are you sure that your user is correct and profile is public?'''
ERROR_ARGUMENTS = '''Arguments are wrong! Try running:
migrator.py <username> [initialDate]
username: GitLab public username profile
initialDate(optional): Start commit date in YYYY-MM-DD format'''

def main(argv):
    print(STATE_INIT)
    events = getEvents(argv)

    print(STATE_LOAD)
    for event in tqdm(events):
        createCommits(event),

    print(STATE_DONE)
    os.system(GIT_STATUS)

def getEvents(argv):
    try:
        if os.path.exists(COMMIT_FILE):
            # Read data from md file
            baseEvent = Event.fromLocal(COMMIT_FILE)
        else:
            # Get data from arguments
            baseEvent = Event.fromArgs(argv)
    except:
        print(ERROR_ARGUMENTS)
        exit()

    # Request events from GitLab
    response = requestEvents(baseEvent.user)

    return parsedEvents(response, baseEvent)

def createCommits(event):
    # Get dump path variable to hide commit messages based on OS
    dumpPath = WINDOWS_DUMP_PATH if os.name == WINDOWS_NAME else UNIX_DUMP_PATH

    for i in range(event.commitsCount):
        message = event.toMessage(i + 1)
        
        # Echo message into md to enable commit of modified file
        os.system(f'echo {json.dumps(message)} > {COMMIT_FILE}')

        # Add file and do commit to GitHub
        os.system(f'git add {COMMIT_FILE}')
        os.system(f'git commit --date="{event.dateString} 12:00:00" -m "{message}" > {dumpPath}')

def requestEvents(user):
    try:
        # Sign default certificate to allow https request
        ssl._create_default_https_context = ssl._create_unverified_context

        # Headers to pass GitLab validation simulating a browser
        headers = { USER_AGENT_KEY : USER_AGENT_VALUE }
        
        # URL to fetch user commits data from calendar.json
        url = f'https://gitlab.com/users/{user}/calendar.json'

        # Send request from URL and Headers
        request = urlopen(Request(url = url, headers = headers))
        
        # Fetch succesful decoded response
        response = request.read().decode()
    except:
        print(ERROR_FETCH_DATA.format(user))
        exit()

    return json.loads(response)

def parsedEvents(response, baseEvent):
    eventsDict = response.items()
    
    if baseEvent.dateString in eventsDict:
        # Remove already commited contributions
        eventsDict[baseEvent.dateString] -= baseEvent.commitsCount

    # Filter days since 'baseEvent.dateString' and Parse dictionary into [Event]
    events = [Event(baseEvent.user, k, v) for k, v in eventsDict if baseEvent.isBefore(k)]    

    return sorted(events)

def formatDateString(date):
    return datetime.strptime(date, DATE_FORMAT)

class Event:
    def __init__(self, user = '', date = UNIX_EPOCH, count = 0):
        self.user = user
        self.dateString = date 
        self.commitsCount = count

    def __lt__(self, other):
        return self.dateString < other.dateString

    @classmethod
    def fromArgs(self, args):
        if len(args) > 2:
            print(args)
            return Event(args[1], args[2])
        
        if len(args) > 1:
            return Event(args[1])

        raise Exception()

    @classmethod
    def fromLocal(self, path):
        file = open(path, READ)
        
        data = json.loads(file.read())
        
        return Event(data[USER], data[LAST_COMMIT], data[COMMITS_COUNT])

    def toMessage(self, i):
        data = {}
        data[USER] = self.user
        data[LAST_COMMIT] = self.dateString
        data[COMMITS_COUNT] = self.commitsCount
        data[COUNTER] = i

        return json.dumps(data)

    def isBefore(self, date):
        return formatDateString(self.dateString) < formatDateString(date)

if __name__ == "__main__":
   main(sys.argv)
