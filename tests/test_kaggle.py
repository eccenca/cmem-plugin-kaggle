"""Plugin tests."""
import os
import pytest
from cmem_plugin_kaggle.kaggle_import import (
    KaggleImport,
    KaggleSearch,
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
    TestTaskContext,
    TestExecutionContext,
    TestSystemContext,
)

PROJECT_NAME = "kaggle_test_project"
DATASET_NAME = "annual"
DATASET_TYPE = "csv"
RESOURCE_NAME = f"{DATASET_NAME}.{DATASET_TYPE}"
KAGGLE_DATASET = "programmerrdai/global-temperature"
KAGGLE_USERNAME = "rangareddynukala"
KAGGLE_PASSWORD = Password(
    encrypted_value="0678724483534d355962db8f07650473", system=TestSystemContext()
)


def test_completion():
    """test completion"""
    parameter = KaggleSearch()
    completion = parameter.autocomplete(
        query_terms=[""],
        depend_on_parameter_values=[KAGGLE_USERNAME, KAGGLE_PASSWORD.decrypt()],
        context=TestTaskContext(),
    )
    assert isinstance(completion, list)

    parameter = KaggleSearch()
    completion = parameter.autocomplete(
        query_terms=["asdcjhasdcjasdc"],
        depend_on_parameter_values=[KAGGLE_USERNAME, KAGGLE_PASSWORD.decrypt()],
        context=TestTaskContext(),
    )
    assert isinstance(completion, list)


@pytest.fixture(scope="module")
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
def test_execution(project):
    """Test plugin execution"""
    KaggleImport(
        username=KAGGLE_USERNAME,
        access_token=KAGGLE_PASSWORD,
        kaggle_dataset=KAGGLE_DATASET,
        file_name=RESOURCE_NAME,
        dataset=DATASET_NAME,
    ).execute(inputs=[], context=TestExecutionContext(project_id=PROJECT_NAME))
    assert (
        resource_exist(project_name=PROJECT_NAME, resource_name=RESOURCE_NAME) is True
    )


def test_failing_init():
    """Test RandomValues plugin."""

    # Invalid Kaggle Dataset Slug
    with pytest.raises(ValueError, match=r".*'\{username}\/{dataset-slug\}'"):
        KaggleImport(
            username=KAGGLE_USERNAME,
            access_token=KAGGLE_PASSWORD,
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
            username=KAGGLE_USERNAME,
            access_token=KAGGLE_PASSWORD,
            kaggle_dataset=KAGGLE_DATASET,
            file_name="INVALID_FILE_NAME",
            dataset=DATASET_NAME,
        )

    # Invalid Dataset ID
    # with pytest.raises(ValueError, match=r'() is not a valid task ID.$'):
    #     KaggleImport(kaggle_dataset=KAGGLE_DATASET,
    #                  file_name=RESOURCE_NAME,
    #                  dataset='INVALID_DATASET_ID')


def test_dummy():
    """dummy"""
