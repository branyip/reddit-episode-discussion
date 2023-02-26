import math
import operator
import re
import statistics
from datetime import datetime
from difflib import SequenceMatcher

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
            user_agent=REDDIT_CONFIG['user_agent'],
            check_for_async=False
        )
        self.search_limit = search_limit
        self.title_regexes = [
            r'.*S(?P<season>\d+)E(?P<episode>\d+).*',  # "S01E01 discussion"
            r'.*(?P<season>\d+)x(?P<episode>\d+).*',  # "1x01 discussion"
            r'.*Season (?P<season>\d+) Episode[s]? (?P<episode>\d+).*',  # "Season 1 Episode 1 discussion"
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

    # @staticmethod
    # def clean_submissions(submissions: list):
    #     """
    #     Used for cleaning up titles like `I have a question about the ending of s01e08`
    #
    #     Calculates the Levenshtein token sort ratio for each submission's title compared to all other submission
    #     titles, and then removes any submissions that have a ratio greater than two standard deviations from the
    #     average token set ratio.
    #
    #     Levenshtein token sort ratio: Sorts all string tokens before performing a fuzz.ratio() operation
    #     """
    #     for submission in submissions:
    #         token_set_ratio = 0
    #         for discussion_inner in submissions:
    #             token_set_ratio += fuzz.partial_ratio(submission['title'], discussion_inner['title'])
    #             submission['meta'] = {}
    #             submission['meta']['levenshtein_token_sort_ratio'] = token_set_ratio / float(len(submissions))
    #
    #     _meta = [(s['meta']['levenshtein_token_sort_ratio'], s['title']) for s in submissions]
    #
    #     levenshtein_token_sort_ratios = [d['meta']['levenshtein_token_sort_ratio'] for d in submissions]
    #     levenshtein_token_sort_avg = sum(levenshtein_token_sort_ratios) / len(submissions)
    #     levenshtein_token_sort_std_dev =statistics.pstdev(levenshtein_token_sort_ratios)
    #     max_deviation = 3 * levenshtein_token_sort_std_dev
    #
    #     for submission in submissions:
    #         levenshtein_token_sort_ratio = submission['meta']['levenshtein_token_sort_ratio']
    #         submission['meta']['levenshtein_token_sort_delta'] =abs(levenshtein_token_sort_avg - levenshtein_token_sort_ratio)
    #
    #     levenshtein_token_sort_deltas = [d['meta']['levenshtein_token_sort_delta'] for d in submissions]
    #     levenshtein_token_sort_delta_avg = sum(levenshtein_token_sort_deltas) / len(submissions)
    #     levenshtein_token_sort_std_dev = statistics.pstdev(levenshtein_token_sort_deltas)
    #     max_deviation = 3 * levenshtein_token_sort_delta_avg
    #
    #     deleted_submissions = []
    #     for idx, submission in enumerate(submissions):
    #         levenshtein_token_sort_delta = submission['meta']['levenshtein_token_sort_delta']
    #         logger.info(f'{levenshtein_token_sort_delta=}\t{levenshtein_token_sort_std_dev=}\t{levenshtein_token_sort_delta_avg=}')
    #         if levenshtein_token_sort_delta > max_deviation:
    #             logger.info(
    #                 f'Removing `{submission["title"]}`, levenshtein token sort delta ({levenshtein_token_sort_delta:.2f}) '
    #                 f'> max deviation ({max_deviation:.2f})'
    #             )
    #             deleted_submissions.append(submission['title'])
    #             del submissions[idx]
    #
    #     logger.info(f'Average Levenshtein ratio = {levenshtein_token_sort_avg:.2f}')
    #     logger.info(f'Levenshtein standard deviation = {levenshtein_token_sort_std_dev}')
    #     logger.info(f'Max deviation = {max_deviation}')
    #     logger.info(f'Number of deleted submissions = {len(deleted_submissions)}')
    #     [s.pop('meta') for s in submissions]
    #
    #     return submissions

    @staticmethod
    def clean_submissions(submissions: list):
        """Removes submissions that don't contain the most common substring among all submissions"""
        substring_counter = {}
        for i in range(0, len(submissions)):
            for j in range(i + 1, len(submissions)):
                string_a = submissions[i]['title']
                string_b = submissions[j]['title']
                match = SequenceMatcher(None, string_a, string_b).find_longest_match(0, len(string_a), 0, len(string_b))
                matching_substring = string_a[match.a:match.a + match.size]
                if matching_substring in substring_counter:
                    substring_counter[matching_substring] += 1
                else:
                    substring_counter[matching_substring] = 1

        substring_counter = {k: v for k, v in substring_counter.items() if v > 1}
        # average_substring_count = sum(substring_counter.values()) / len(substring_counter)
        found_substring_std_dev = statistics.pstdev(substring_counter.values())
        average_substring_count = statistics.mean(substring_counter.values())
        logger.info(f'{substring_counter=}')

        # TODO: tweak this so it can handle thelastofus
        # substring merging: if entire string is in another and off by 1 word
        common_substrings = []
        for substring, substring_count in substring_counter.items():
            if substring_count >= average_substring_count - 1.5 * found_substring_std_dev:
                logger.info(f'Found common substring: `{substring}` ({substring_count}) >= {average_substring_count:.2f}')
                common_substrings.append(substring)

        logger.info(f'{common_substrings=}')
        for idx, submission in enumerate(submissions):
            found_substring_count = 0
            for substring in common_substrings:
                if substring in submission['title']:
                    found_substring_count += 1
            found_substring_pct = found_substring_count / len(common_substrings) * 100
            submission['meta'] = {'found_substring_pct': found_substring_pct}

        found_substring_pct_mean = statistics.mean([s['meta']['found_substring_pct'] for s in submissions])
        found_substring_std_dev = statistics.pstdev([s['meta']['found_substring_pct'] for s in submissions])

        for idx, submission in enumerate(submissions):
            found_substring_pct = submission['meta']['found_substring_pct']
            max_delta = found_substring_pct_mean - 1.5 * found_substring_std_dev
            if found_substring_pct < max_delta:
                logger.info(f'Removing: `{submission["title"]}` {found_substring_pct} < { found_substring_pct_mean - found_substring_std_dev}')
                del submissions[idx]

        [s.pop('meta') for s in submissions]

        return submissions

    def find_submissions(self, subreddit_name: str):
        """Queries the provided subreddit for submissions containing the term `episode discussion`"""
        logger.info(f'Searching: `r/{subreddit_name}`')
        subreddit = self.client.subreddit(subreddit_name)
        submissions = [s for s in subreddit.search(query='episode discussion', limit=self.search_limit)]
        logger.info(f'Found: {len(submissions)} submissions ({self.search_limit=})')
        return submissions

    def parse_submissions(self, submissions: list, pattern: str):
        """Filters a list of submissions based on a regex pattern and formats the results"""
        discussions = []
        for submission in submissions:
            matches = re.match(pattern, submission.title, re.IGNORECASE)
            if matches:
                logger.info(f'Matched: `{submission.title}`')
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
