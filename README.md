# The Camp
The Camp is a Discord game bot. Your aim is to survive as long as possible, either through teamwork or selfish actions.

## Setup

Install the required packages with `pip install -r requirements.txt` and create a valid `config.py` file.
You will need to run a PostgreSQL database and (optionally) Redis as well. Create a Discord server with the correct
text channels and roles, and finally run `!updatecampstatus reset`.

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