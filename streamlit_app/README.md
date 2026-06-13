# Endometriosis Project Progress Tracker

This is a local Streamlit prototype for shared milestone and experiment progress tracking.

## Data Model

The prototype reads and writes CSV files in `streamlit_app/data/sample/`. These CSV files mirror the planned Google Sheet tabs:

- `Members.csv`
- `Teams.csv`
- `Member_Teams.csv`
- `Projects.csv`
- `Milestones.csv`
- `Experiments.csv`
- `Updates_Reviews.csv`

Dropbox experiment folders are stored as URL fields. The app does not store raw experimental data.

`Teams.csv` defines selectable teams. `Member_Teams.csv` links members to teams, so one member can appear in multiple teams. The legacy `team` column in `Members.csv` remains for compatibility, but team filtering uses `Teams.csv` and `Member_Teams.csv` when they are present.

## Run Locally

```bash
python -m streamlit run streamlit_app/app.py
```

## Test

```bash
python -m pytest tests -v
```

## Prototype Workflow

1. Select `All teams` or a team name in the sidebar.
2. Select a member name from the members assigned to that team.
3. Open the Overview tab to review the team Gantt chart.
4. Open the Milestones tab to review the milestone Gantt chart.
5. Open the Experiments tab.
6. Update an assigned experiment status, next action, and Dropbox data link.
7. Save the update.
8. Open the Review tab.
9. Approve the pending item or request revision with a review note.

## Shared Version Direction

After the workflow stabilizes, deploy to Streamlit Cloud and add login-based PI, Lead, and Member permissions. The local CSV adapter should be replaced or complemented by a Google Sheet adapter using the same logical table structure.
