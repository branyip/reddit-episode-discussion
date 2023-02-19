# Reddit Episode Discussion

Finds Episode discussion threads on Reddit, a great companion for your tv binging sessions.

Note: This is a WIP, and the nature of user-dictated titles means pattern matching will not cover all cases.

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


## Usage
Add your Reddit application credentials to `cfg.yml` at the project root.
```yaml
# cfg.yml
reddit:
  client_id: <client_id>
  client_secret: <client_secret>
  user_agent: 'reddit-episode-discussion'
```

Running the following code will get you a list of submissions
```python
from reddit_handler import RedditHandler

reddit = RedditHandler(search_limit=200)
submissions = reddit.find_submissions('witcher')
pattern = reddit.get_title_pattern(submissions)
submissions_parsed = reddit.parse_submissions(submissions, pattern)
```

The value of `submissions_parsed`:
```
[
    {
        "season": 1,
        "episode": 1,
        "title": "Episode Discussion - S01E01: The End's Beginning",
        "created": "2019-12-20 02:31:07 UTC",
        "comment_count": 3190,
        "url": "https://www.reddit.com/r/witcher/comments/ed6wkj/episode_discussion_s01e01_the_ends_beginning/",
    },
    {
        "season": 1,
        "episode": 2,
        "title": "Episode Discussion - S01E02: Four Marks",
        "created": "2019-12-20 02:31:16 UTC",
        "comment_count": 2377,
        "url": "https://www.reddit.com/r/witcher/comments/ed6wmz/episode_discussion_s01e02_four_marks/",
    },
    {
        "season": 1,
        "episode": 3,
        "title": "Episode Discussion - S01E03: Betrayer Moon",
        "created": "2019-12-20 02:31:22 UTC",
        "comment_count": 2337,
        "url": "https://www.reddit.com/r/witcher/comments/ed6wo4/episode_discussion_s01e03_betrayer_moon/",
    },
    {...},
    {...},
    {...},
}
```