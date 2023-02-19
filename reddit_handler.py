import math
import re
import statistics
from datetime import datetime

import praw
from fuzzywuzzy import fuzz

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
        self.title_regexes = [
            r'.*S(?P<season>\d+)E(?P<episode>\d+).*',  # "S01E01 discussion"
            r'.*(?P<season>\d+)x(?P<episode>\d+).*',  # "1x01 discussion"
            r'.*Season (?P<season>\d+) Episode[s]?(?P<episode>\d+).*',  # "Season 1 Episode 1 discussion"
            r'.*Episode[s]? (?P<episode>\d+) .*',  # "Episode 1 discussion" (more typical for single-season series)
        ]

    def get_title_pattern(self, submissions: list):
        """Determines the best regex pattern for this subreddit's discussion thread titles"""
        pattern_counter = {pattern: 0 for pattern in self.title_regexes}
        for submission in submissions:
            for pattern in pattern_counter.keys():
                if re.match(pattern, submission.title, re.IGNORECASE):
                    pattern_counter[pattern] += 1
                    break

        target_pattern, target_pattern_count = sorted(pattern_counter.items(), key=lambda p: p[1], reverse=True)[0]
        logger.info(f'Most common pattern: `{target_pattern}` (matched {target_pattern_count} times)')
        return target_pattern

    @staticmethod
    def clean_submissions(submissions: list):
        """Calculates the Levenshtein partial ratio for each submission's title compared to all other submission
        titles, and then removes any submissions that have a ratio greater than two standard deviations from the
        average levenshtein ratio."""
        for submission in submissions:
            ratio_total = 0
            for discussion_inner in submissions:
                ratio_total += fuzz.partial_ratio(submission['title'], discussion_inner['title'])
            submission['levenshtein_ratio'] = ratio_total / float(len(submissions))

        levenshtein_ratios = [d['levenshtein_ratio'] for d in submissions]
        levenshtein_avg = sum(levenshtein_ratios) / len(submissions)
        levenshtein_std_dev = math.floor(statistics.pstdev(levenshtein_ratios))
        max_deviation = 2 * levenshtein_std_dev

        deleted_submissions = []
        for idx, submission in enumerate(submissions):
            levenshtein_delta = math.floor(abs(levenshtein_avg - submission['levenshtein_ratio']))
            if levenshtein_delta > max_deviation:
                logger.info(
                    f'Removing `{submission["title"]}`, levenshtein delta ({levenshtein_delta:.2f}) '
                    f'> max deviation ({max_deviation:.2f})'
                )
                deleted_submissions.append(submission['title'])
                del submissions[idx]
            submission.pop('levenshtein_ratio')

        logger.info(f'Average Levenshtein ratio = {levenshtein_avg:.2f}')
        logger.info(f'Levenshtein standard deviation = {levenshtein_std_dev}')
        logger.info(f'Max deviation = {max_deviation}')
        logger.info(f'Number of deleted submissions = {len(deleted_submissions)}')

        return submissions

    def find_submissions(self, subreddit_name: str):
        """Queries the provided subreddit for submissions containing the term `episode discussion`"""
        logger.info(f'Searching `r/{subreddit_name}`')
        subreddit = self.client.subreddit(subreddit_name)
        submissions = [s for s in subreddit.search(query='episode discussion', limit=self.search_limit)]
        logger.info(f'Found {len(submissions)} submissions ({self.search_limit=})')
        return submissions

    def parse_submissions(self, submissions: list, pattern: str):
        """Filters a list of submissions based on a regex pattern and formats the results"""
        discussions = []
        for submission in submissions:
            matches = re.match(pattern, submission.title, re.IGNORECASE)
            if matches:
                logger.info(f'Matched `{submission.title}`')
                season = matches.groupdict().get('season', 1)
                episode = matches.groupdict().get('episode', 1)
                discussions .append({
                    'season': int(season),
                    'episode': int(episode),
                    'title': submission.title,
                    'created': str(datetime.fromtimestamp(submission.created_utc)) + ' UTC',
                    'comment_count': submission.num_comments,
                    'url': submission.url
                })
        discussions = sorted(discussions, key=lambda k: (k['season'], k['episode'], k['title']))
        discussions = self.clean_submissions(discussions)
        return discussions
