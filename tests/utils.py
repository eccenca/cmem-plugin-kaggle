"""Testing utilities."""
import os
from typing import Optional

import pytest

# check for cmem environment and skip if not present
from _pytest.mark import MarkDecorator
from cmem.cmempy.api import get_token
from cmem_plugin_base.dataintegration.context import (
    UserContext,
    TaskContext,
    ExecutionContext,
    ReportContext,
    SystemContext,
    PluginContext,
)

needs_cmem: MarkDecorator = pytest.mark.skipif(
    "CMEM_BASE_URI" not in os.environ, reason="Needs CMEM configuration"
)

needs_kaggle: MarkDecorator = pytest.mark.skipif(
    "KAGGLE_USERNAME" not in os.environ or "KAGGLE_KEY" not in os.environ,
    reason="Needs Kaggle API configuration",
)


def get_kaggle_config():
    """To get the kaggle configuration from environment variables"""
    return {
        "username": os.environ.get("KAGGLE_USERNAME", ""),
        "key": os.environ.get("KAGGLE_KEY", ""),
    }


class TestUserContext(UserContext):
    """dummy user context that can be used in tests"""

    __test__ = False

    def __init__(self):
        # get access token from default service account
        access_token: str = f"{get_token()['access_token']}"  # type: ignore
        self.token = lambda: access_token


class TestTaskContext(TaskContext):
    """dummy Task context that can be used in tests"""

    __test__ = False

    def __init__(self, project_id: str = "dummyProject"):
        self.project_id = lambda: project_id


class TestExecutionContext(ExecutionContext):
    """dummy execution context that can be used in tests"""

    __test__ = False

    def __init__(
        self,
        project_id: str = "dummyProject",
        user: Optional[UserContext] = TestUserContext(),
    ):
        self.report = ReportContext()
        self.task = TestTaskContext(project_id=project_id)
        self.user = user


class TestSystemContext(SystemContext):
    """dummy system context that can be used in tests"""

    __test__ = False

    def __init__(self):
        self._version = "1.0.0"
        self._prefix = "encrypted_"

    def di_version(self) -> str:
        return f"{self._version}"

    def encrypt(self, value: str) -> str:
        return f"{self._prefix + value}"

    def decrypt(self, value: str) -> str:
        return value.replace(self._prefix, "")


class TestPluginContext(PluginContext):
    """dummy test plugin context that can be used in tests"""

    __test__ = False

    def __init__(self, project_id: str = "dummyProject"):
        self.system = TestSystemContext()
        self.user = TestUserContext()
        self.project_id = project_id
