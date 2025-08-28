# gradescope-discohook

[![run main.py](https://github.com/bachtran02/GradescopeSync/actions/workflows/actions.yml/badge.svg)](https://github.com/bachtran02/GradescopeSync/actions/workflows/actions.yml)

gradescope-discohook is a simple Python script that scrapes data from [Gradescope](https://www.gradescope.com/) and send to [Discord](https://discord.com/) text channel via [Discord Webhook](https://discord.com/developers/docs/resources/webhook)

 <img src="https://github.com/bachtran02/gradescope-discohook/assets/83796054/42e4f3e0-863b-4b03-88d6-4d5f1b6bd0e2" width="450">

 <img src="https://github.com/bachtran02/gradescope-discohook/assets/83796054/b6bb7015-401b-485c-968c-91baa974381e" width="450">

## How to set up

> Feel free to make use of the code for your own purposes. Here is how I set it up and use it at the moment.

1. Clone the repo.
2. Create an `.env` file using this [template](https://github.com/bachtran02/gradescope-discohook/blob/master/.env.example) and enter your Gradescope credentials. 

> `WEBHOOK_URL` is the webhook URL of the Discord text channel you want to send the message to. Check out [this article](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) on how to get it.

3. Install dependencies with `pip install -r requirements.txt` (preferably using `Python venv`)  
4.  Run `python main.py`

To automate the execution of the script, I use [Linux cron Jobs](https://www.freecodecamp.org/news/cron-jobs-in-linux/). This should be rather straightforward as we only need to run one command for execution.  


 For gradescope scraping, I used [this repo](https://github.com/jlumbroso/pylifttk) for reference and made my own changes due to Gradescope having updated their front end over time so the code in the original repo may or may not work as intended. 
