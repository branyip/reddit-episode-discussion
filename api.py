from fastapi import FastAPI
from starlette import status

from reddit_handler import RedditHandler

app = FastAPI()


@app.get('/')
async def root():
    return {'status': status.HTTP_200_OK}


@app.get('/discussions')
async def discussions(subreddit: str):
    reddit = RedditHandler(search_limit=200)
    submissions = reddit.find_submissions(subreddit_name=subreddit)
    pattern = reddit.get_title_pattern(submissions)
    return reddit.parse_submissions(submissions, pattern)
