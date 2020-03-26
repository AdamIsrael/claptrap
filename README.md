# Claptrap

An experimental slack bot.

## Usage

To generate the claptrap database:
```bash
python3 resetdb.py
```

To run the claptrap slack bot:
```bash
export SLACK_BOT_TOKEN='your bot user access token here'
export SLACK_SIGNING_SECRET='your signing secret here'
python3 claptrap.py
```
