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

Configure the portal app secrets with:

```toml
REGISTRY_SPREADSHEET_ID = "your-google-sheet-id"

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

The service account must have edit access to the registry Google Sheet.

## Initial Apps

- Budget: active launcher card
- Notebooks/Protocols: active launcher card
- Project Tracker: can remain inactive or URL-disabled until its production deployment URL is ready

## Current Admin Scope

The first shared portal supports adding/deactivating members, adding teams, granting app roles, updating launcher URLs, and appending audit records. Editing team memberships, reactivating members, editing existing role rows, and deactivating app roles are intentionally left for the next integration stage.
