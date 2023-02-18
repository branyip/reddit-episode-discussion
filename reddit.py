import re
from datetime import datetime
import praw
from cfg import logger, REDDIT_CONFIG


class RedditHandler:
    def __init__(self, search_limit: int = 100):
        """
        :param search_limit: Max number of submissions to retrieve when querying subreddits, higher limits generally
        increase search time. (default: 100, max: 1000)
        """
        self.client = praw.Reddit(
            client_id=REDDIT_CONFIG['client_id'],
            client_secret=REDDIT_CONFIG['client_secret'],
            user_agent=REDDIT_CONFIG['user_agent']
        )
        self.search_limit = search_limit

    def search_subreddit(self, subreddit_name: str):
        logger.info(f'Searching r/{subreddit_name}')
        subreddit = self.client.subreddit(subreddit_name)
        submissions = [s for s in subreddit.search(query='episode discussion', limit=self.search_limit)]
        logger.info(f'Found {len(submissions)} submissions ({self.search_limit=})')
        return submissions

    def parse_submissions(self, submissions: list):
        """
        {
            meta: {
                subreddit: x
                submission_count: x
                season_count: x
            }
            submissions: [
                {
                    season: x
                    episode: x
                    title: x
                    submission_datetime: x
                    comment_count: x
                    url: x
                }
            ]
        }
        """
        discussions = []
        for submission in submissions:
            matches = re.match(r'.*S(?P<season>\d+)E(?P<episode>\d+).*', submission.title)
            if matches:
                logger.info(f'Matched `{submission.title}`')
                season = matches.group('season')
                episode = matches.group('episode')
                discussions .append({
                    'season': int(season),
                    'episode': int(episode),
                    'title': submission.title,
                    'created': str(datetime.fromtimestamp(submission.created_utc)),
                    'comment_count': submission.num_comments,
                    'url': submission.url
                })
        discussions = sorted(discussions, key=lambda k: (k['season'], k['episode'], k['title']))
        return discussions


reddit = RedditHandler(search_limit=1000)
submissions = reddit.search_subreddit('youonlifetime')
parsed_submissions = reddit.parse_submissions(submissions)
print(parsed_submissions)