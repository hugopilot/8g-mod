# So you want to host this bot yourself eh?
That's good! Setting this up is really easy.

# Prerequisites
For the bot to run smoothly you'll need the following programs:
- [Python 3.7 or higher](https://python.org)
- [pip](https://pypi.org/project/pip/) (this usually comes with Python)
- A SQLite DB browser like [DB Browser for SQLite](https://sqlitebrowser.org/)

We do recommend installing [Git](https://git-scm.com/) as this makes updating the bot easy, but it's not critical.

# Installation with Git installed
1. Start your favorite terminal and move it to the directory you want the bot to be installed in
1. Clone the git repo with `git clone https://github.com/hugopilot/pluto-mod.git`
  
  _This will create a new folder called 'pluto-mod' with all the source code_
  
3. Go to the src folder in the repo: `cd pluto-mod/src`
4. Create a new file called `config.py`
5. Add and edit the following contents to `config.py`:

```py
# General info
token = "Discord Bot Token here"
version = "0.5.0" 
prefix = '?' # Command prefix. Set a custom character if you wish
botname = "Pluto's Shitty Mod Bot" # You can set a custom name for the bot here

# File locations (I would recommend leaving these settings alone unless you know what you're doing)
databaseloc = '../data/main.db' 
logloc = '../data/logs/main.log'
errloc = '../data/logs/err.log'

# Server bindings
# All ID's should be int! 
guild = # Put your guild/server ID here
logch = # Put your log channel ID here (this is the channel where all logs will be dumped)
infrepch = # Put your infraction report channel ID here (this is the channel where all infraction reports will be send)

# Server roles
mutedrole = # Put the muted role ID here. This role will be assigned when the mute command is used
autoroles = () # Put any roles in here that need to be auto-assigned when a member joins, you can leave this empty if you don't want this
invincibleroles = () # Invincible roles are roles that are exempt from antispam and cannot be warned, muted, kicked or banned by the bot.

# Owners
owners = () # Put your Discord ID in here, can be left empty

# Antispam configurations
emojitolerance = 5 # When a message exceeds has this number of emojis the message gets deleted 
spamtolerance = 2 # This value represents all messages sent by the same user in a certain timeframe (in seconds) 
spamthreshold = 2 # This value represents the maximum number of messages that may be sent in the time defined in spamtolerance
mentiontolerance = 5 # The maximum amount of mentions a message may have before getting deleted

# Sensitive logs expiry times
sensitive_expiry:float = 43200 # The amount of seconds when log entries that contain deleted messages get deleted 
```
6. Start your DB browser and create a new database. Call this `main.db` and save this in the `data` folder (unless you defined a different location in the config file)
7. Execute the `data/createdb.sql` file on the database. ([Demo](https://i.imgur.com/8TNsM0g.mp4))
8. Create a directory called `logs` in `data`

Your file hierarchy should look like this now

```
pluto_mod
|
|
src ---
      |
      models
           |
           colors.py
           elevatedperms.py
           errors.py
           measure.py
      modules
           |
           db.py
           log.py
           markdown.py
           spam.py
           update.py
      bot.py
      config.py
data ----
        |
        logs (empty folder)
        main.db
        createdb.sql
        
.gitignore
LICENSE
READING.md
README.md
HOSTING.md
requirements.txt
```



# Running the bot
With everything set up we're ready to start the bot.
Start your terminal and go to the main folder.

Run `pip install -r requirements.txt`. This should download all the libraries needed.

Then run `cd src` and then finally `python3 bot.py`. The bot should now run perfectly.

