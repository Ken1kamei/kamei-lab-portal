# Endometriosis Project Progress Tracker

This is a local Streamlit prototype for shared milestone and experiment progress tracking.

## Data Model

The prototype reads and writes progress CSV files in `streamlit_app/data/sample/` for local development. In Streamlit Cloud, set `PROGRESS_SPREADSHEET_ID` to store progress tables in Google Sheets. Member and team data are loaded from the shared Kamei Lab Portal registry in `lab_portal/data/sample/` for local development, or from the configured registry Google Sheet in Streamlit Cloud.

The Project Tracker progress CSV files mirror these planned tabs:

- `Projects.csv`
- `Milestones.csv`
- `Experiments.csv`
- `Updates_Reviews.csv`

Dropbox experiment folders are stored as URL fields. The app does not store raw experimental data.

Selectable teams and member-team assignments come from the Portal registry. This keeps member management centralized across Budget, Notebooks/Protocols, Project Tracker, and the Portal launcher.

Projects can now be added manually from the `Projects` tab, and milestone creation requires a responsible person. The `Projects` tab also accepts `.xlsx` and `.docx` imports for project and milestone rows. For Excel imports, use sheets named `Projects` and/or `Milestones`. For Word imports, use simple tables whose headers match the corresponding table columns.

## Run Locally

```bash
python -m streamlit run streamlit_app/app.py
```

## Streamlit Cloud Setup

Deploy from:

- Repository: `Ken1kamei/kamei-lab-portal`
- Branch: `main`
- Main file path: `streamlit_app/app.py`

Configure the app secrets with:

```toml
REGISTRY_SPREADSHEET_ID = "your-google-sheet-id"
PROGRESS_SPREADSHEET_ID = "your-google-sheet-id"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

The service account must have edit access to the Google Sheet.

## Test

```bash
python -m pytest tests -v
```

## Prototype Workflow

1. Select `All teams` or a team name in the sidebar.
2. Select a member name from the members assigned to that team.
3. Open the Overview tab to review the team Gantt chart.
4. Open the Projects tab to create a new project or import rows from Excel or Word.
5. Open the Milestones tab to create a milestone and assign a responsible person.
6. Open the Experiments tab.
7. Update an assigned experiment status, next action, and Dropbox data link.
8. Save the update.
9. Open the Review tab.
10. Approve the pending item or request revision with a review note.

## Shared Version Direction

After the workflow stabilizes, add login-based PI, Lead, and Member permissions. The app already uses the shared Portal registry path for member/team data and can store progress tables in Google Sheets through `PROGRESS_SPREADSHEET_ID`.
