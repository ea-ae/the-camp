# The Camp
The Camp is a Discord game bot. Your aim is to survive as long as possible, either through teamwork or selfish actions.

## Setup

1. Install the required packages with `pip install -r requirements.txt`.
2. Create the config file
3. Create the required tables in PostgreSQL (TODO: auto-create them).
4. Then add the needed text channels to your server and launch the bot.
5. Create all the necessary roles and give yourself the 'Developer' role.
6. Run the command `!updatecampstatus reset` to fill the configuration table.

More information on the required text channels and roles will be added later.

## Configuration file

You must create a file named `config.py` in the root path. It should look something like this:

```python
TOKEN = 'abcdefghijklmnopqrstuvwxyz1234567890abcdefghijklmnopqrstuvwxyz1234567890'
SERVER_ID = '12345678901234567890'

DB_NAME = 'camp'
DB_USER = 'camp'
DB_PASSWORD = 'hunter2'
DB_HOST = '127.0.0.1'

JOBSTORE = 'redis'  # 'redis' / 'sqlalchemy' (pip install sqlalchemy)
```