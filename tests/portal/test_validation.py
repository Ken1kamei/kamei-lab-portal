from pathlib import Path

import pandas as pd

from lab_portal.portal.storage import CsvRegistryStore
from lab_portal.portal.validation import validate_registry


def test_valid_sample_registry_has_no_errors():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()

    assert validate_registry(registry) == []


def test_duplicate_active_email_is_reported():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    duplicate = registry["Members"].iloc[[0]].copy()
    duplicate.loc[duplicate.index[0], "member_id"] = "M999"
    registry["Members"] = pd.concat([registry["Members"], duplicate], ignore_index=True)

    errors = validate_registry(registry)

    assert "Duplicate active member email: kkamei@nyu.edu" in errors


def test_unknown_app_role_reference_is_reported():
    registry = CsvRegistryStore(Path("lab_portal/data/sample")).load()
    registry["App_Roles"].loc[0, "app_id"] = "missing_app"

    errors = validate_registry(registry)

    assert "App_Roles AR001 references unknown app_id missing_app" in errors
