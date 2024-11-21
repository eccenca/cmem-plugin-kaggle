"""Plugin tests."""

from collections.abc import Generator
from dataclasses import dataclass

import pytest
from cmem.cmempy.workspace.projects.datasets.dataset import (
    make_new_dataset,
)
from cmem.cmempy.workspace.projects.project import delete_project, make_new_project
from cmem.cmempy.workspace.projects.resources.resource import resource_exist
from cmem_plugin_base.dataintegration.parameter.password import Password
from cmem_plugin_base.dataintegration.types import Autocompletion

from cmem_plugin_kaggle.kaggle_import import (
    DatasetFile,
    DatasetFileType,
    KaggleImport,
    KaggleSearch,
    auth,
)
from tests.utils import (
    TestExecutionContext,
    TestPluginContext,
    TestSystemContext,
    TestTaskContext,
    get_kaggle_config,
    needs_cmem,
    needs_kaggle,
)

PROJECT_NAME = "kaggle_test_project"
DATASET_NAME = "test-dataset"
DATASET_TYPE = "csv"
RESOURCE_NAME = f"{DATASET_NAME}.{DATASET_TYPE}"
KAGGLE_DATASET = "brsahan/data-science-job"
KAGGLE_CONFIG = get_kaggle_config()
KAGGLE_KEY = Password(encrypted_value=KAGGLE_CONFIG["key"], system=TestSystemContext())


@dataclass
class ProjectFixtureData:
    """Project fixture data"""

    project: str
    dataset: str
    resource: str


@pytest.fixture(name="project")
def _project() -> Generator[ProjectFixtureData, None, None]:
    """Provide the DI project incl. assets."""
    make_new_project(PROJECT_NAME)
    make_new_dataset(
        project_name=PROJECT_NAME,
        dataset_name=DATASET_NAME,
        dataset_type="csv",
        parameters={"file": RESOURCE_NAME},
        autoconfigure=False,
    )
    yield ProjectFixtureData(PROJECT_NAME, DATASET_NAME, RESOURCE_NAME)
    delete_project(PROJECT_NAME)


@needs_kaggle
def test_kaggle_search_completion() -> None:
    """Test completion"""
    parameter = KaggleSearch()
    # on empty query
    completion = parameter.autocomplete(
        query_terms=[],
        depend_on_parameter_values=[KAGGLE_CONFIG["username"], KAGGLE_KEY],
        context=TestTaskContext(),
    )
    assert isinstance(completion, list)
    assert len(completion) == 20  # noqa: PLR2004
    first_dataset_name = completion[0].value
    # on unmatch query
    completion = parameter.autocomplete(
        query_terms=["asdcjhasdcjasdc"],
        depend_on_parameter_values=[KAGGLE_CONFIG["username"], KAGGLE_KEY],
        context=TestTaskContext(),
    )
    assert len(completion) == 0

    # on match query
    completion = parameter.autocomplete(
        query_terms=[first_dataset_name],
        depend_on_parameter_values=[KAGGLE_CONFIG["username"], KAGGLE_KEY],
        context=TestTaskContext(),
    )
    assert len(completion) == 1
    assert completion[0] == Autocompletion(value=first_dataset_name, label=first_dataset_name)


@needs_kaggle
def test_dataset_file_type_completion(project: ProjectFixtureData) -> None:
    """Test completion"""
    _ = project
    auth(KAGGLE_CONFIG["username"], KAGGLE_KEY.decrypt())
    parameter = DatasetFileType(dependent_params=["file_name"])

    # on empty query
    completion = parameter.autocomplete(
        query_terms=["test-dataset"],
        depend_on_parameter_values=["test-dataset.csv"],
        context=TestPluginContext(project_id=PROJECT_NAME),
    )
    assert isinstance(completion, list)


@needs_cmem
@needs_kaggle
def test_execution(project: ProjectFixtureData) -> None:
    """Test plugin execution"""
    _ = project
    KaggleImport(
        username=KAGGLE_CONFIG["username"],
        api_key=KAGGLE_KEY,
        kaggle_dataset=KAGGLE_DATASET,
        file_name="data_science_job.csv",
        dataset=DATASET_NAME,
    ).execute(inputs=[], context=TestExecutionContext(project_id=PROJECT_NAME))
    assert resource_exist(project_name=PROJECT_NAME, resource_name=RESOURCE_NAME) is True


@needs_cmem
@needs_kaggle
def test_single_file_zip(project: ProjectFixtureData) -> None:
    """Test plugin execution"""
    _ = project
    KaggleImport(
        username=KAGGLE_CONFIG["username"],
        api_key=KAGGLE_KEY,
        kaggle_dataset="huascarmendez1/cord19csv",
        file_name="pdf_comm_use.csv",
        dataset=DATASET_NAME,
    ).execute(inputs=[], context=TestExecutionContext(project_id=PROJECT_NAME))
    assert resource_exist(project_name=PROJECT_NAME, resource_name=RESOURCE_NAME) is True


@needs_kaggle
def test_failing_init() -> None:
    """Test RandomValues plugin."""
    # Invalid Kaggle Dataset Slug
    with pytest.raises(ValueError, match=r".*'\{username}\/{dataset-slug\}'"):
        KaggleImport(
            username=KAGGLE_CONFIG["username"],
            api_key=KAGGLE_KEY,
            kaggle_dataset="INVALID_FILE_NAME",
            file_name=RESOURCE_NAME,
            dataset=DATASET_NAME,
        )

    # Invalid File Name of the Kaggle Dataset
    with pytest.raises(
        ValueError,
        match=r"The specified file doesn't exists in the "
        r"specified dataset and it must be from.*",
    ):
        KaggleImport(
            username=KAGGLE_CONFIG["username"],
            api_key=KAGGLE_KEY,
            kaggle_dataset=KAGGLE_DATASET,
            file_name="INVALID_FILE_NAME",
            dataset=DATASET_NAME,
        )

    with pytest.raises(
        ValueError,
        match=r"Dataset must be specified in the form of \'{username}/{dataset-slug}",
    ):
        KaggleImport(
            username=KAGGLE_CONFIG["username"],
            api_key=KAGGLE_KEY,
            kaggle_dataset="programmerrdaiteno",
            file_name="INVALID_FILE_NAME",
            dataset=DATASET_NAME,
        )


@needs_kaggle
def test_dataset_file_completion() -> None:
    """Test completion"""
    auth(KAGGLE_CONFIG["username"], KAGGLE_KEY.decrypt())
    parameter = DatasetFile()

    # on empty dataset
    with pytest.raises(ValueError, match="Select dataset before choosing a file"):
        parameter.autocomplete(
            query_terms=["apple.csv"],
            depend_on_parameter_values=[],
            context=TestTaskContext(),
        )

    # on empty query
    completion = parameter.autocomplete(
        query_terms=[],
        depend_on_parameter_values=[KAGGLE_DATASET],
        context=TestTaskContext(),
    )
    assert isinstance(completion, list)
    assert len(completion) == 1

    # on query with dataset
    completion = parameter.autocomplete(
        query_terms=["apple.csv"],
        depend_on_parameter_values=["vislupus/vegetable-and-fruit-prices"],
        context=TestTaskContext(),
    )
    assert isinstance(completion, list)
    assert len(completion) == 20  # noqa: PLR2004
    assert any(_ == Autocompletion(value="apple.csv", label="apple.csv") for _ in completion)
