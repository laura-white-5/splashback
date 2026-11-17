# SplashBack 

AI-supported progress reports for swim teachers. IS3329 Deliverable 2 prototype.
All data is synthetic 

## Setup 
Requires Python 3.11+

```bash
git clone https://github.com/laura-white-5/splashback.git
cd splashback
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
```
## Run
```bash
python app.py
```
Open http://127.0.0.1:5000. Delete `splashback.db` to reset the demo.

## Test
```bash
python -m pytest
```

## Structure
Each folder is one architecture component: `access` (mocked), `roster`, `skills`,
`notes`, `reports` (context → generate → check), `ai_provider`, `review`.
`app.py` and `templates/` are the web front end.

## AI provider
The app uses the mock AI in Deliverable 2. To switch provider, change only
`get_ai_provider()` in `ai_provider/factory.py`.



      

