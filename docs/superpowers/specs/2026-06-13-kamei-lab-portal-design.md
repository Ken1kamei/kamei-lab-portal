# Kamei Lab Portal Design

## Purpose

This specification defines a new Streamlit portal for Kamei Reverse Bioengineering Lab. The portal will be the shared entry point for lab apps and the central place to manage lab members, teams, and app permissions.

The portal will initially link three apps:

- Budget
- Notebooks/Protocols
- Project Tracker

The first release will build the portal and the central member registry. Existing apps will be connected to the registry in later stages so the lab can move safely from separate app-specific member management to one shared source of truth.

## Decisions Already Approved

- Create a new dedicated portal app instead of putting the top page inside an existing app.
- Use a single Google Sheet registry as the canonical member, team, and app-permission store.
- Include an app launcher plus basic member-management UI in v1.
- Include Budget, Notebooks/Protocols, and Project Tracker as the first portal apps.
- Use a full shared registry with an audit log.
- Use staged integration: portal first, then connect existing apps one by one.

## Goals

- Give lab members one clear home page for lab Streamlit apps.
- Let authorized admins add, deactivate, and update members in one place.
- Let admins assign members to multiple teams.
- Let admins grant per-app roles and optional team-scoped access.
- Record member/team/app permission edits in an append-only audit log.
- Keep the visual language consistent with the existing Kamei Lab dark Streamlit apps.
- Avoid breaking currently deployed apps while the shared registry is introduced.

## Non-Goals

- The portal will not merge Budget, Notebooks/Protocols, and Project Tracker into one app.
- The portal will not manage raw experimental files, Dropbox folders, or notebook/protocol content directly.
- The first release will not force all existing apps to read the new registry immediately.
- The first release will not replace budget allocation ledgers or project experiment ledgers.

## System Architecture

The system has four main parts:

1. Kamei Lab Portal Streamlit app
2. Central Google Sheet registry
3. Existing Streamlit apps linked from the portal
4. Shared registry access code copied or packaged into each app as integration proceeds

The portal is the user-facing administrative surface. It authenticates lab users, displays available apps, and provides member/team/app access management screens.

The Google Sheet registry is the canonical store. The portal writes registry changes and appends audit records. Apps read from the registry once each app is integrated.

Existing apps remain separately deployed Streamlit apps. The portal links to them through URLs stored in the `Apps` sheet. If an app does not yet have a production URL, it can remain inactive in the registry until the admin adds the URL.

## Authentication and Roles

The portal should follow the Budget app's existing authentication direction:

- Use Streamlit/OIDC login in deployed mode.
- Require verified lab/NYU emails.
- Keep a local development fallback only for local testing.

Portal-level roles:

- `pi`: full access to portal administration and all apps.
- `admin`: manage members, teams, app entries, and app permissions.
- `lead`: view member/team information and manage team-scoped app access when granted.
- `member`: view their own profile, teams, and app launch links.
- `inactive`: no app access.

App-level roles are stored separately from portal-level roles because each app may need its own vocabulary. Recommended initial app roles:

- `owner`
- `manager`
- `lead`
- `editor`
- `viewer`

Apps can map these shared roles to app-specific behavior during integration.

## Central Registry Schema

The Google Sheet registry will use six worksheets.

### Members

Purpose: identify lab members and their global status.

Core fields:

- `member_id`
- `email`
- `name`
- `display_name`
- `global_role`
- `active`
- `start_date`
- `end_date`
- `notes`

Rules:

- `email` must be unique among active members.
- `member_id` must be stable and should not be reused.
- Deactivation sets `active` to false instead of deleting the row.

### Teams

Purpose: define lab teams, projects, or working groups that can be used across apps.

Core fields:

- `team_id`
- `team_name`
- `description`
- `active`

Rules:

- `team_id` must be stable and should not be reused.
- Deactivation keeps historical membership and audit records readable.

### Member_Teams

Purpose: assign members to one or more teams.

Core fields:

- `member_team_id`
- `member_id`
- `team_id`
- `team_role`
- `active`
- `start_date`
- `end_date`

Rules:

- A member can belong to multiple teams.
- `team_role` is team-scoped and can differ from `global_role`.
- Deactivation ends a team assignment without deleting history.

### Apps

Purpose: store app launcher entries and integration metadata.

Core fields:

- `app_id`
- `app_name`
- `app_url`
- `description`
- `category`
- `active`
- `sort_order`

Initial rows:

- `budget`: Budget
- `notebooks_protocols`: Notebooks/Protocols
- `project_tracker`: Project Tracker

Rules:

- Only active apps appear as normal launch cards.
- Apps with missing or non-production URLs can remain inactive or appear with a disabled state.
- The portal reads app names and URLs from this sheet rather than hard-coding launcher cards.

### App_Roles

Purpose: grant app-specific access to members, optionally scoped to one team.

Core fields:

- `app_role_id`
- `member_id`
- `app_id`
- `app_role`
- `scope_team_id`
- `active`
- `start_date`
- `end_date`

Rules:

- `scope_team_id` may be blank for lab-wide app access.
- Deactivation removes future access without deleting the historical row.
- Apps should treat inactive members and inactive app roles as no access.

### Audit_Log

Purpose: append-only history of administrative changes.

Core fields:

- `audit_id`
- `timestamp`
- `actor_email`
- `action`
- `target_type`
- `target_id`
- `before`
- `after`

Rules:

- Every portal write to `Members`, `Teams`, `Member_Teams`, `Apps`, or `App_Roles` appends an audit row.
- `before` and `after` should be serialized JSON strings.
- Audit rows are never edited from the portal UI.

## Portal UI Design

The portal will use the same general visual direction as the existing lab Streamlit apps: dark background, compact research-dashboard layout, clear tabs, and cyan/teal accent styling.

### Home / App Launcher

The home page shows:

- Lab title and short subtitle.
- App cards for Budget, Notebooks/Protocols, and Project Tracker.
- App status indicators from the `Apps` sheet.
- Launch buttons for active apps with URLs.
- Disabled cards for inactive apps or apps missing a production URL.

### Members

The Members page supports:

- Search/filter by name, email, active state, role, and team.
- Add member.
- Edit member display name, global role, notes, and active state.
- Deactivate/reactivate member.
- View member's teams and app roles.

### Teams

The Teams page supports:

- Create team.
- Edit team name and description.
- Deactivate/reactivate team.
- Assign or remove team membership.
- Show team roster and team-scoped roles.

### App Access

The App Access page supports:

- Manage the list of launcher apps.
- Update app URLs and active states.
- Grant app roles to members.
- Scope an app role to a team when needed.
- Deactivate app roles.

### Audit

The Audit page supports:

- Read-only audit table.
- Filters by actor, target type, target id, and action.
- Recent changes view for quick review.

## Data Flow

Read flow:

1. User signs in.
2. Portal loads the registry worksheets.
3. Portal resolves the user's member record and roles.
4. Portal renders launcher cards and admin pages allowed by the user's role.

Write flow:

1. Admin submits a member, team, app, or app-role change.
2. Portal validates required fields and references.
3. Portal writes the changed row to the relevant worksheet.
4. Portal appends an `Audit_Log` row with actor, target, before state, and after state.
5. Portal refreshes cached registry data.

App integration flow:

1. App reads the same registry sheet using `REGISTRY_SPREADSHEET_ID`.
2. App resolves the signed-in user by email.
3. App checks active membership and active app role for its `app_id`.
4. App maps the shared app role to its own internal permissions.

## Staged Integration Plan

### Stage 1: Portal and Registry

Build the new portal app, create the registry schema, and provide member/team/app-access admin UI. Existing apps remain unchanged and are linked from the launcher.

### Stage 2: Project Tracker Integration

Connect Project Tracker to the central registry first. It is the newest app and already has member/team concepts, so it is the safest first integration target.

The Project Tracker should continue to keep project, milestone, experiment, and review records in its own ledger while reading people/team/app access from the registry.

### Stage 3: Budget Integration

Connect Budget access control to the central registry while keeping budget-specific allocation and expense data in the Budget app's existing sheets.

Budget's existing team/member columns should be migrated carefully because they currently mix team membership, budget roles, and budget allocation metadata.

### Stage 4: Notebooks/Protocols Integration

Connect Notebooks/Protocols to the registry for lab membership, role checks, and optional team visibility. Notebook/protocol records remain owned by the Notebooks/Protocols app.

## Error Handling

The portal should show clear admin-facing errors for:

- Missing Google Sheet credentials.
- Missing required worksheets.
- Missing required columns.
- Duplicate active member email.
- Unknown member, team, or app references.
- Attempting to grant access to inactive members or inactive apps.
- Google Sheet read/write failures.

For write failures, the portal should not show a successful save message unless both the target row update and audit log append succeed. If the target update succeeds but audit append fails, the UI should warn the admin and provide enough detail to repair the audit record manually.

## Caching

The portal may cache registry reads for responsiveness, but writes must clear or refresh the cache immediately after a successful save.

Apps that read the registry should use short-lived caching so permission changes become visible without waiting for a redeploy. A manual refresh button is acceptable for v1 admin workflows.

## Testing Strategy

Unit tests should cover:

- Registry schema validation.
- Required field validation.
- Unique active email validation.
- Member/team/app reference validation.
- App role resolution for lab-wide and team-scoped roles.
- Audit row creation.
- Permission checks for `pi`, `admin`, `lead`, `member`, and inactive users.

Integration or smoke tests should cover:

- Portal app imports successfully.
- Sample registry data renders launcher cards.
- Member add/edit/deactivate operations update sample data and create audit records.
- App role changes affect launcher visibility and permission resolution.

Manual verification should cover:

- Local Streamlit run.
- Login fallback in local mode.
- Google Sheet credentials in deployed-like mode.
- Launch links for Budget, Notebooks/Protocols, and Project Tracker.
- Cache refresh after administrative changes.

## Operational Setup Inputs

The implementation plan should include concrete setup steps for:

- Creating or selecting the central registry Google Sheet.
- Adding the six worksheets with required headers.
- Configuring Streamlit secrets for registry sheet access.
- Adding the portal app to Streamlit Cloud.
- Adding the portal service account to the registry Google Sheet.
- Entering production URLs for active apps in the `Apps` sheet.

These are deployment inputs, not open product requirements.
