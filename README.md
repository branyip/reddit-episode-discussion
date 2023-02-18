# Reddit Episode Discussion

Finds episode discussion threads on Reddit for your current tv obsession.

## Prerequisites
- Python >= 3.8
- virtualenv Python package
- A registered application on Reddit ([guide](https://old.reddit.com/prefs/apps/)). This step will yield authentication credentials required by the [PRAW](https://praw.readthedocs.io/en/stable/index.html) client.

## Installing
```bash
virtualenv <virtual_env_name>
source <virtual_env_name>/bin/activate
pip install -r requirements.txt
```


## Running
Add your Reddit application credentials to `cfg.yml` at the project root.
```yaml
# cfg.yml
reddit:
  client_id: <client_id>
  client_secret: <client_secret>
  user_agent: 'reddit-episode-discussion'
```