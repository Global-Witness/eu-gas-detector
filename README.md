# EU Gas Detector

This repository contains a couple of [AWS Lambda](https://aws.amazon.com/lambda/) functions which power Global Witness's [EU Gas Detector Twitter bot](https://twitter.com/eugasdetector). The functions, `detector.py` and `actor.py`, are written in Python and deployed using the [serverless](https://www.serverless.com/) framework.

## Usage

To run your own version of the bot, create a `.env` file in the root of this repository and fill in the environment variables listed below. Use the following magic spell to create a Lambda 'layer' including the required Python packages: `docker run -v "$PWD":/var/task "lambci/lambda:build-python3.8" /bin/sh -c "pip install -r requirements.txt -t .; exit"`. Then edit `serverless.yml` to tweak the template text and deploy it using `serverless deploy`. As well as AWS Lambda for hosting the functions and SES for sending emails, you'll need a Twitter account linked to a registered [Twitter app](https://developer.twitter.com/en) and an account on [AskTheEU.org](https://www.asktheeu.org/) for sending freedom of information (FOI) requests.

## Environment variables

| Variable name           | Description |
|-------------------------|-------------|
| SOURCE_EMAIL            | Email address to send confirmation emails from—this must already be authorised to send email on your behalf in SES. |
| RECIPIENT_EMAILS        | Email addresses to receive confirmation emails (comma-separated list). |
| TWITTER_CONSUMER_KEY    | Credential for the Twitter API—get it from your [Twitter apps page](https://developer.twitter.com/en/portal/projects-and-apps). |
| TWITTER_CONSUMER_SECRET | *Ditto* |
| TWITTER_ACCESS_TOKEN    | *Ditto* |
| TWITTER_ACCESS_SECRET   | *Ditto* |
| ASKTHEEU_EMAIL          | Email address for your AskTheEU.org account. |
| ASKTHEEU_PASSWORD       | Password for your AskTheEU.org account. |

## How it works

At set intervals (once a day by default), `detector.py` loads the lists of meetings between European Commissioners and their staff published on the EC website—[here](http://ec.europa.eu/transparencyinitiative/meetings/meeting.do?host=f1afd532-0d40-4dcd-8e45-667b57075377) is an example for Frans Timmermans and [another](http://ec.europa.eu/transparencyinitiative/meetings/meeting.do?host=ec1ecb7e-2615-44eb-895b-6b08637c2a0d) for his cabinet. The script checks the first page of meetings and extracts key information: date, host names, guest names, and the EU Transparency Register ID for each guest, which is hidden in the page's source code.

Once the meeting information has been extracted, it's compared to a static list of relevant hosts and guests given in `data/entities.csv`. Hosts are keyed by name and guests by their Transparency Register ID. It also adds the relevant public body ID from AskTheEU.org to the data, using the `data/public-bodies.csv` lookup table—this allows FOI requests to be sent to the correct departments.

When the script finds a meeting with a relevant company it hashes it to generate a unique ID and puts it in a DynamoDB table. If the meeting isn't already in the database and a corresponding tweet doesn't exist on the Twitter timeline, the script sends a confirmation email to the addresses given in the `RECIPIENT_EMAILS` environment variable, including a link to trigger the `actor.py` function. When the link is clicked, `actor.py` uses the Twitter API to send a tweet; it also logs in to AskTheEU.org and creates a draft FOI request for the meeting minutes, which can be checked over and sent manually by a Global Witness campaigner.
