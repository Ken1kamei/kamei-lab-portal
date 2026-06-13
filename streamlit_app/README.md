# Endometriosis Project Progress Tracker

This is a local Streamlit prototype for shared milestone and experiment progress tracking.

## Data Model

The prototype reads and writes CSV files in `streamlit_app/data/sample/`. These CSV files mirror the planned Google Sheet tabs:

- `Members.csv`
- `Projects.csv`
- `Milestones.csv`
- `Experiments.csv`
- `Updates_Reviews.csv`

Dropbox experiment folders are stored as URL fields. The app does not store raw experimental data.

## Run Locally

```bash
python -m streamlit run streamlit_app/app.py
```

## Test

```bash
python -m pytest tests -v
```

## Prototype Workflow

1. Select a member name in the sidebar.
2. Open the Experiments tab.
3. Update an assigned experiment status, next action, and Dropbox data link.
4. Save the update.
5. Open the Review tab.
6. Approve the pending item or request revision with a review note.

## Shared Version Direction

After the workflow stabilizes, deploy to Streamlit Cloud and add login-based PI, Lead, and Member permissions. The local CSV adapter should be replaced or complemented by a Google Sheet adapter using the same logical table structure.
