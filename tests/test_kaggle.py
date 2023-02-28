"""Plugin tests."""
import os
import pytest
from cmem_plugin_kaggle.kaggle_import import (
    KaggleImport,
    KaggleSearch,
    DatasetFile,
    DatasetFileType,
    auth,
    get_zip_file_path,
)
from cmem.cmempy.workspace.projects.project import make_new_project, delete_project
from cmem.cmempy.workspace.projects.datasets.dataset import (
    make_new_dataset,
)
from cmem_plugin_base.dataintegration.parameter.password import Password
from cmem.cmempy.workspace.projects.resources.resource import resource_exist
from tests.utils import (
    needs_cmem,
    needs_kaggle,
    get_kaggle_config,
    TestTaskContext,
    TestExecutionContext,
    TestSystemContext,
    TestPluginContext,
)
from cmem_plugin_base.dataintegration.types import Autocompletion

PROJECT_NAME = "kaggle_test_project"
DATASET_NAME = "test-dataset"
DATASET_TYPE = "csv"
RESOURCE_NAME = f"{DATASET_NAME}.{DATASET_TYPE}"
KAGGLE_DATASET = "rangareddynukala/cmem-plugin-kaggle-test"
KAGGLE_CONFIG = get_kaggle_config()
KAGGLE_KEY = Password(encrypted_value=KAGGLE_CONFIG["key"], system=TestSystemContext())


@needs_kaggle
def test_kaggle_search_completion():
    """test completion"""
    parameter = KaggleSearch()

    # on empty query
    completion = parameter.autocomplete(
        query_terms=[],
        depend_on_parameter_values=[KAGGLE_CONFIG["username"], KAGGLE_KEY],
        context=TestTaskContext(),
    )
    print(completion)
    assert isinstance(completion, list)
    assert len(completion) == 1
    assert completion[0] == Autocompletion(
        value="Message", label="Search for kaggle datasets"
    )

    # on unmatch query
    completion = parameter.autocomplete(
        query_terms=["asdcjhasdcjasdc"],
        depend_on_parameter_values=[KAGGLE_CONFIG["username"], KAGGLE_KEY],
        context=TestTaskContext(),
    )
    assert len(completion) == 0

    # on match query
    completion = parameter.autocomplete(
        query_terms=[KAGGLE_DATASET],
        depend_on_parameter_values=[KAGGLE_CONFIG["username"], KAGGLE_KEY],
        context=TestTaskContext(),
    )
    assert len(completion) == 1
    assert completion[0] == Autocompletion(value=KAGGLE_DATASET, label=KAGGLE_DATASET)


@needs_kaggle
def test_dataset_file_type_completion(project):
    """test completion"""
    auth(KAGGLE_CONFIG["username"], KAGGLE_KEY.decrypt())
    parameter = DatasetFileType(dependent_params=["file_name"])

    # on empty query
    completion = parameter.autocomplete(
        query_terms=["test-dataset"],
        depend_on_parameter_values=["test-dataset.csv"],
        context=TestPluginContext(project_id=PROJECT_NAME),
    )
    print(completion)
    assert isinstance(completion, list)


@pytest.fixture(scope="function")
def project():
    """Provides the DI build project incl. assets."""
    make_new_project(PROJECT_NAME)
    make_new_dataset(
        project_name=PROJECT_NAME,
        dataset_name=DATASET_NAME,
        dataset_type="csv",
        parameters={"file": RESOURCE_NAME},
        autoconfigure=False,
    )

    yield None
    delete_files()
    delete_project(PROJECT_NAME)


def delete_files():
    """Delete Downloaded Files on Test"""
    file_path = f"./{RESOURCE_NAME}"
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(get_zip_file_path(RESOURCE_NAME)):
        os.remove(get_zip_file_path(RESOURCE_NAME))


@needs_cmem
@needs_kaggle
def test_execution(project):
    """Test plugin execution"""
    KaggleImport(
        username=KAGGLE_CONFIG["username"],
        api_key=KAGGLE_KEY,
        kaggle_dataset=KAGGLE_DATASET,
        file_name="test csv.csv",
        dataset=DATASET_NAME,
    ).execute(inputs=[], context=TestExecutionContext(project_id=PROJECT_NAME))
    assert (
        resource_exist(project_name=PROJECT_NAME, resource_name=RESOURCE_NAME) is True
    )


@needs_kaggle
def test_failing_init():
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
def test_dataset_file_completion():
    """test completion"""
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
    print(completion)
    assert isinstance(completion, list)
    assert len(completion) == 6

    # on query with dataset
    completion = parameter.autocomplete(
        query_terms=["apple.csv"],
        depend_on_parameter_values=["vislupus/vegetable-and-fruit-prices"],
        context=TestTaskContext(),
    )
    assert isinstance(completion, list)
    assert len(completion) == 22
    assert completion[0] == Autocompletion(value="apple.csv", label="apple.csv")
