# automated-face-recognition-attendance-system
An automated face recognition system for taking class attendance in an institution

## Setup
Create a virtual environment `python3 -m venv 'env-name'`
Activate the venv `source env-name/bin/activate`
Install dependencies `pip install -r requirements.txt`

## Run the server
`uvicorn main:app --reload`

## Change Control and Commits
Before commits, run `isort .` then `black .` for consistent sorting and formatting.