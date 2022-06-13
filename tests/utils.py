"""Testing utilities."""
import os

import pytest

# check for cmem environment and skip if not present
needs_cmem = pytest.mark.skipif(
    "CMEM_BASE_URI" not in os.environ, reason="Needs CMEM configuration"
)
