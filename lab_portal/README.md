# Kamei Lab Portal

Kamei Lab Portal is a Streamlit entry point for Kamei Reverse Bioengineering Lab apps. It launches the Budget, Notebooks/Protocols, and Project Tracker apps while keeping lab members, teams, app access, and audit history in one shared registry.

## Local Run

```bash
PORTAL_DEV_EMAIL=kkamei@nyu.edu .venv/bin/streamlit run lab_portal/app.py --server.port 8503
```

Local development reads and writes CSV files in `lab_portal/data/sample`.

## Registry Tables

The shared registry uses these tables. In Google Sheets deployment, each table should be a worksheet with the headers defined in `lab_portal/portal/schema.py`.

- `Members`
- `Teams`
- `Member_Teams`
- `Apps`
- `App_Roles`
- `Audit_Log`

## Streamlit Cloud Setup

Deploy from:

- Repository: `Ken1kamei/kamei-lab-portal`
- Branch: `main`
- Main file path: `lab_portal/app.py`
- Portal URL: `https://kamei-lab-tools.streamlit.app/`
- Project Tracker URL: `https://kamei-lab-roadmap.streamlit.app/`

Configure the portal app secrets with:

```toml
PORTAL_APP_URL = "https://kamei-lab-tools.streamlit.app/"
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

The service account must have edit access to the registry/progress Google Sheet. `PROGRESS_SPREADSHEET_ID` can use the same Sheet as `REGISTRY_SPREADSHEET_ID` when the workbook includes the Project Tracker tabs.

### Sign in

For Streamlit sign in, configure OIDC under `[auth]` in Streamlit Cloud secrets and keep `Authlib>=1.3.2` installed. Google OIDC can be configured like this:

```toml
[auth]
redirect_uri = "https://kamei-lab-tools.streamlit.app/oauth2callback"
cookie_secret = "replace-with-a-long-random-secret"
client_id = "your-google-oauth-client-id"
client_secret = "your-google-oauth-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

The signed-in email must match an active `Members.email` row with `global_role` set to `pi` or `admin` to add members, add teams, or manage app access. For temporary Cloud administration before OIDC is ready, set `PORTAL_DEV_EMAIL = "kkamei@nyu.edu"` in secrets.

## Sleep Mitigation

Streamlit Community Cloud apps can become inactive when they have not been used for a while. The repository includes `.github/workflows/keep-streamlit-awake.yml`, which pings the deployed lab apps every 10 minutes and can also be run manually from GitHub Actions.

## Initial Apps

- Budget: `https://kamei-lab-budget-qff7jmewjwgpft4qyhc7hb.streamlit.app/`
- Notebooks/Protocols: `https://kamei-lab-notebooks-protocols.streamlit.app/`
- Project Tracker: `https://kamei-lab-roadmap.streamlit.app/`

## Current Admin Scope

The first shared portal supports adding/deactivating members, adding teams, granting app roles, updating launcher URLs, and appending audit records. Editing team memberships, reactivating members, editing existing role rows, and deactivating app roles are intentionally left for the next integration stage.
