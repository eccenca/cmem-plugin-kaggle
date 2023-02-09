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
    get_dataset
)
from cmem.cmempy.workspace.projects.resources.resource import resource_exist
from .utils import needs_cmem

PROJECT_NAME = "kaggle_test_project"
DATASET_NAME = "annual"
DATASET_TYPE = "csv"
RESOURCE_NAME = f"{DATASET_NAME}.{DATASET_TYPE}"
DATASET_ID = f"{PROJECT_NAME}:{DATASET_NAME}"
KAGGLE_DATASET = "programmerrdai/global-temperature"


def test_completion():
    """test completion"""
    parameter = KaggleSearch()
    completion = parameter.autocomplete(query_terms=[""])
    assert isinstance(completion, list)

    parameter = KaggleSearch()
    completion = parameter.autocomplete(query_terms=["asdcjhasdcjasdc"])
    assert isinstance(completion, list)


@pytest.fixture
def setup(request):
    make_new_project(PROJECT_NAME)
    make_new_dataset(
        project_name=PROJECT_NAME,
        dataset_name=DATASET_NAME,
        dataset_type=DATASET_TYPE,
        parameters={"file": RESOURCE_NAME},
        autoconfigure=False,
    )

    def teardown():
        delete_project(PROJECT_NAME)
        delete_files()

    request.addfinalizer(teardown)

    return get_dataset(PROJECT_NAME, DATASET_NAME)


def delete_files():
    """Delete Downloaded Files on Test"""
    file_path = f'./{RESOURCE_NAME}'
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(get_zip_file_path(RESOURCE_NAME)):
        os.remove(get_zip_file_path(RESOURCE_NAME))


@needs_cmem
def test_execution(setup):
    """Test plugin execution"""
    assert setup['id'] == DATASET_NAME
    KaggleImport(
        kaggle_dataset=KAGGLE_DATASET,
        file_name=RESOURCE_NAME,
        dataset=DATASET_ID
    ).execute()
    assert resource_exist(
        project_name=PROJECT_NAME,
        resource_name=RESOURCE_NAME
    ) is True


def test_failing_init():
    """Test RandomValues plugin."""

    # Invalid Kaggle Dataset Slug
    with pytest.raises(ValueError, match=r".*'\{username}\/{dataset-slug\}'"):
        KaggleImport(kaggle_dataset="INVALID_FILE_NAME", file_name=RESOURCE_NAME,
                     dataset=DATASET_ID)

    # Invalid File Name of the Kaggle Dataset
    with pytest.raises(ValueError, match=r"The specified file doesn't exists in the "
                                         r"specified dataset and it must be from.*"):
        KaggleImport(kaggle_dataset=KAGGLE_DATASET, file_name="INVALID_FILE_NAME",
                     dataset=DATASET_ID)

    # Invalid Dataset ID
    with pytest.raises(ValueError, match=r'() is not a valid task ID.$'):
        KaggleImport(kaggle_dataset=KAGGLE_DATASET,
                     file_name=RESOURCE_NAME,
                     dataset='INVALID_DATASET_ID')


def test_dummy():
    """dummy"""
