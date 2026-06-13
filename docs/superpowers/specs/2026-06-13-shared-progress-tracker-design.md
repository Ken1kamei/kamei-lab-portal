# Shared Progress Tracker Design

## Purpose

This specification defines a shared progress-tracking system for the Endometriosis project. The system will let project members track milestones, experiment progress, review state, and optional links to experiment data. It is designed for a research group workflow where members update their own records and Lead/PI users review those updates.

The first implementation will be a local Streamlit prototype backed by a Google Sheet-compatible ledger. After the workflow is stable, the system can be deployed to Streamlit Cloud with login and role-based permissions.

## Decisions Already Approved

- Platform direction: Google Sheet as the official ledger, Streamlit as the dashboard and edit interface.
- Experimental data storage: keep files in Dropbox and store only URLs in the tracker.
- Update workflow: members update records; Lead/PI users review and approve.
- Dashboard views: provide tabs for Overview, Members, Milestones, Experiments, and Review.
- Status vocabulary: use research-oriented progress states.
- Review vocabulary: keep review status separate from experimental progress status.
- Deployment path: local prototype first, then Streamlit Cloud.
- Authentication path: member-name selection in the prototype, then PI/Lead/Member login roles in the shared version.
- Milestone model: include project, aim, milestone, and time_window fields to support roadmaps, grant aims, and free-entry milestones.

## System Architecture

The app will have four main parts:

1. Streamlit dashboard
2. Google Sheet-compatible ledger
3. Dropbox links to experimental data folders or files
4. Review history recorded in the ledger

Streamlit is the user-facing layer. It reads the ledger, renders progress dashboards, provides member update forms, and provides Lead/PI review controls.

The ledger is the official record. During prototype work, it may be represented as local CSV files with the same schema as the future Google Sheet. When Google Sheet access is configured, the app should read from and write to the Sheet using the same table structure.

Dropbox remains the storage location for experimental files. The app will not upload, copy, or manage raw data. It will store fields such as `experiment_data_link`, `protocol_link`, and `analysis_folder_link`.

## Roles

### Prototype Roles

The prototype will not require full login. Users choose their member name from a controlled list. This keeps the first version simple and lets the lab test the workflow quickly.

### Shared Version Roles

The Streamlit Cloud version will add login and enforce role-based behavior.

- PI: view all records, approve any record, monitor project-level progress, manage configuration.
- Lead: view and review records for assigned projects, aims, milestones, or teams.
- Member: update assigned experiments and milestones, add progress notes, add Dropbox links, respond to revision requests.

## Ledger Structure

The ledger will use five logical tables. In Google Sheets these will be separate tabs.

### Members

Purpose: identify users and their roles.

Core fields:

- `member_id`
- `name`
- `email`
- `role`
- `team`
- `lead_id`
- `active`

### Projects

Purpose: define the project and high-level aim structure.

Core fields:

- `project_id`
- `project`
- `aim`
- `owner_member_id`
- `start_date`
- `target_date`
- `notes`

### Milestones

Purpose: track progress against project and aim milestones.

Core fields:

- `milestone_id`
- `project_id`
- `project`
- `aim`
- `milestone`
- `time_window`
- `owner_member_id`
- `status`
- `review_status`
- `next_action`
- `due_date`
- `blocker_reason`
- `help_needed_from`
- `updated_at`

### Experiments

Purpose: track individual experiments and connect them to milestones.

Core fields:

- `experiment_id`
- `milestone_id`
- `project_id`
- `member_id`
- `experiment_title`
- `experiment_type`
- `status`
- `review_status`
- `next_action`
- `due_date`
- `experiment_data_link`
- `protocol_link`
- `analysis_folder_link`
- `blocker_reason`
- `help_needed_from`
- `updated_at`

### Updates / Reviews

Purpose: keep a lightweight history of member updates, Lead/PI approvals, and revision requests.

Core fields:

- `update_id`
- `record_type`
- `record_id`
- `updated_by`
- `update_note`
- `old_status`
- `new_status`
- `reviewed_by`
- `review_status`
- `review_note`
- `timestamp`

The main Milestones and Experiments tables should remain readable and current. The Updates / Reviews table preserves context and review history without making the main tables too noisy.

## Status Model

The `status` field describes scientific or operational progress.

Allowed values:

- `Planned`
- `Preparing`
- `Running`
- `Data acquired`
- `Analyzing`
- `Review needed`
- `Completed`
- `Blocked`

The `review_status` field describes approval state.

Allowed values:

- `Pending`
- `Approved`
- `Needs revision`

When a member updates a milestone or experiment, the app should set `review_status` to `Pending` unless the update is only a draft-like local change that is not saved to the ledger. Lead/PI users can then set it to `Approved` or `Needs revision`.

If `status` is `Blocked`, `blocker_reason` is required. `help_needed_from` is optional but should be encouraged when the blocker depends on another person, core facility, collaborator, reagent, or instrument.

If `review_status` is `Needs revision`, `review_note` is required.

## Dashboard Design

The Streamlit app will use five tabs.

### Overview

Shows the project-level summary:

- Count of milestones and experiments by status.
- Count of pending review items.
- List of blocked items.
- Upcoming due dates.
- Recent updates.

### Members

Shows progress grouped by member:

- Assigned milestones.
- Assigned experiments.
- Current status counts.
- Items needing review or revision.
- Blocked items owned by that member.

### Milestones

Shows progress grouped by project, aim, milestone, and time_window:

- Milestone table with filters.
- Linked experiments under each milestone.
- Progress and review status.
- Due dates and next actions.

### Experiments

Shows experiment-level details:

- Experiment table with filters for project, aim, member, status, and review_status.
- Editable progress fields.
- Dropbox links rendered as clickable links.
- Next action and blocker fields.

### Review

Lead/PI workspace:

- Pending items.
- Needs revision items.
- Blocked items.
- Review note entry.
- Approve or request revision actions.

## Workflow

1. A member chooses their name in the prototype app.
2. The member updates an assigned milestone or experiment.
3. The app validates required fields.
4. The app saves the update and sets `review_status` to `Pending`.
5. The update is recorded in Updates / Reviews.
6. Lead/PI reviews the item in the Review tab.
7. Lead/PI sets `review_status` to `Approved` or `Needs revision`.
8. If revision is needed, Lead/PI writes a `review_note`.
9. The member revises the record and resubmits it.
10. The PI monitors Overview for important milestones, delays, and blocked work.

## Prototype Scope

The first build should include:

- Streamlit app under a dedicated subproject folder.
- Sample ledger files using the approved schema.
- Local CSV mode for development and testing.
- Google Sheet-compatible data access boundary, even if Sheet credentials are configured later.
- Overview, Members, Milestones, Experiments, and Review tabs.
- Member-name selector.
- Member update form for experiment and milestone records.
- Lead/PI review controls.
- Status and review_status validation.
- Required blocker_reason when status is Blocked.
- Required review_note when review_status is Needs revision.
- Clickable Dropbox URL fields.

The prototype should not include:

- Automatic email, Slack, or calendar notifications.
- Raw experimental file upload or storage.
- Deep Dropbox API integration.
- Audit-grade authentication.
- Complex analytics or predictive modeling.

These can be added after the workflow stabilizes.

## Error Handling

The app should prevent saves when required fields are missing. At minimum:

- Milestone and experiment records require an owner/member, status, and next action.
- `Blocked` requires `blocker_reason`.
- `Needs revision` requires `review_note`.
- URL fields should be validated as URL-like strings before rendering as links.

If Google Sheet access is not configured, the app should fall back to local CSV mode. The UI should clearly indicate which backend is active.

If a save fails, the app should show a clear error and avoid partially updating the visible table.

## Testing Plan

Prototype testing should verify:

- Sample ledger loads successfully.
- Overview counts match the sample ledger.
- Members tab groups work by member.
- Milestones tab groups work by project, aim, milestone, and time_window.
- Experiments tab shows Dropbox links as clickable links.
- Member update form saves changes.
- Member updates set review_status to Pending.
- Lead/PI review changes review_status to Approved.
- Needs revision requires review_note.
- Blocked requires blocker_reason.
- Updates / Reviews receives a history row.
- Local CSV mode works without Google Sheet credentials.

Streamlit Cloud testing should add:

- Login works.
- PI, Lead, and Member roles have the expected visibility and edit permissions.
- Sheet credentials are read from Streamlit secrets.
- The deployed app can read and write the Google Sheet ledger.

## Open Implementation Choices

The following can be decided during implementation:

- Exact folder name for the subproject.
- Whether local prototype storage starts as CSV files, a local SQLite database, or both CSV and Sheet adapters.
- Whether the first Google Sheet is generated from a template script or manually prepared.
- Whether role enforcement is included behind a feature flag before Streamlit Cloud deployment.

The recommended implementation choice is to start with local CSV files that mirror the Google Sheet tabs, then add a Sheet adapter once the app shape is stable.
