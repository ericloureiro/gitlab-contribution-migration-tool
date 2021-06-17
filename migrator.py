#!/usr/bin/python
from urllib.request import urlopen, Request
from tqdm import tqdm
import os, collections, ssl, sys, json

# States
STATE_INIT = 'Fetching GitLab events...'
STATE_EMPTY = 'Could not fetch events. Do you have commits or a public profile?'
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
    profile = Profile.build(argv)

    if not profile.events:
        print(STATE_EMPTY)
        return

    print(STATE_LOAD)
    profile.createCommits()

    print(STATE_DONE)
    os.system(GIT_STATUS)

class Profile:
    def __init__(self, user, baseEvent):
        self.user = user
        self.baseEvent = baseEvent
        self.fetchEvents()
    
    @classmethod
    def build(self, args):
        try:
            if os.path.exists(COMMIT_FILE):
                # Read data from md file
                return Profile.fromLocal()
            else:
                # Get data from arguments
                return Profile.fromArgs(args)
        except:
            print(ERROR_ARGUMENTS)
            exit()
            
    @classmethod
    def fromLocal(self):
        file = open(COMMIT_FILE, READ)
        data = json.loads(file.read())
        
        args = []
        # Parse json into list of args
        for item in data:
            args.append(item)

        return Profile.fromArgs(args)
        
    @classmethod
    def fromArgs(self, args):
        user = args[1]
        baseEvent = Event.fromArgs(args)
        
        return Profile(user, baseEvent)

    def fetchEvents(self):
        # Sign default certificate to allow https request
        ssl._create_default_https_context = ssl._create_unverified_context

        # Headers to pass GitLab validation simulating a browser
        headers = { USER_AGENT_KEY : USER_AGENT_VALUE }
            
        # URL to fetch user commits data from calendar.json
        url = f'https://gitlab.com/users/{self.user}/calendar.json'

        try:
            # Send request from URL and Headers
            request = urlopen(Request(url = url, headers = headers))
        
            # Fetch successful decoded response
            response = request.read().decode()

            # Dump response into python object
            data = json.loads(response)
        except:
            print(ERROR_FETCH_DATA.format(self.user))
            exit()
        
        events = self.parseResponse(data.items())
        
        self.events = sorted(events)
        
    def parseResponse(self, items):
        events = []
        # Parse json into list of Events
        for date, count in items:
            event = Event(date, count)
            baseEvent = self.baseEvent

            if baseEvent > event:
                # Filter events before point zero event
                continue

            if baseEvent == event:
                # Remove already commited contributions
                event.commitsCount -= baseEvent.commitsCount
                
            events.append(event)

        return events
    
    def createCommits(self):
        for event in tqdm(self.events):
            event.createCommits(self.user)
    
class Event:
    def __init__(self, date = UNIX_EPOCH, count = 0):
        self.dateString = date 
        self.commitsCount = count

    def __eq__(self, other):
        return self.dateString == other.dateString

    def __lt__(self, other):
        return self.dateString < other.dateString

    @classmethod
    def fromArgs(self, args):
        if len(args) == 4:
            return Event(args[2], args[3])
        
        if len(args) == 3:
            return Event(args[2])
        
        return Event()
    
    def createCommits(self, user):
        # Get dump path variable to hide commit messages based on OS
        dumpPath = WINDOWS_DUMP_PATH if os.name == WINDOWS_NAME else UNIX_DUMP_PATH

        for i in range(self.commitsCount):
            message = self.toMessage(user, i + 1)
        
            # Echo message into md to enable commit of modified file
            os.system(f'echo {json.dumps(message)} >> {COMMIT_FILE}')

            # Add file and do commit to GitHub
            os.system(f'git add {COMMIT_FILE}')
            os.system(f'git commit --date="{self.dateString} 12:00:00" -m "{message}" > {dumpPath}')


    def toMessage(self, user, i):
        data = {}
        data[COUNTER] = i
        data[USER] = user
        data[LAST_COMMIT] = self.dateString
        data[COMMITS_COUNT] = self.commitsCount
        
        return json.dumps(data)

if __name__ == "__main__":
   main(sys.argv)
