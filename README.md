# ArXiv Paper Email Summaries

This repository produces daily email updates of yesterday's arXiv papers that use a specific selection of keywords, using a summary from Gemini.

This is a fork of [this](https://github.com/Shaier/arxiv_summarizer) by @Shaier. Thanks for your work.

## Prerequisites
- Python 3.11
- Conda (for environment management)
- A Gemini API key (free to obtain)

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/LewisClifton/arxiv_summariser.git
cd arxiv_summariser
```

### 2. Set Up the Conda Environment
Create and activate a Conda environment with Python 3.11:
```bash
conda create -n arxiv_summariser -f environment.yml
conda activate arxiv_summariser
```

### 4. Configure .env
Create a `.env` file in the project directory containing:

```
GEMINI_API_KEY=[your Gemini key]
EMAIL_TO=[your recipient's email password]
EMAIL_FROM=[your sender's email address]
EMAIL_PASSWORD=[your email password]
```

### 5. Configure paths
Modify `daily_summary.sh` with the path to your `daily_summary.py`

Set up daily scheduling e.g. with cron:

```
EDITOR=nano crontab -e
```
Then (for daily execution at 10am) add:
```
00 10 * * * your_path_to/daily_summary.sh >> your_path_to/cron.log 2>&1

```

## Usage
- Modify `keywords.txt` with the desired keywords
- Modify `daily_summary.py` with the desired number of papers per keyword
- (Optional) Modify the date range in `daily_summary.py` to consider papers before yesterday
