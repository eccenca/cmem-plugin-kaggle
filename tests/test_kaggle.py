"""Plugin tests."""
import os
import pytest
from cmem.cmempy.workspace.projects.datasets.dataset import make_new_dataset, get_dataset
from cmem.cmempy.workspace.projects.project import make_new_project, delete_project
from cmem_plugin_kaggle.kaggle_import import (
    KaggleImport,
    KaggleSearch,
    get_zip_file_path
)
from cmem_plugin_base.dataintegration.discovery import discover_plugins
from cmem.cmempy.workspace.projects.resources.resource import (
    create_resource,
    resource_exist
)
from .utils import needs_cmem

PROJECT_NAME = "kaggle_test_project"
DATASET_NAME = "annual"
DATASET_TYPE = 'csv'
RESOURCE_NAME = f'{DATASET_NAME}.{DATASET_TYPE}'
DATASET_ID = f'{PROJECT_NAME}:{DATASET_NAME}'
KAGGLE_DATASET = 'programmerrdai/global-temperature'


# package prefix
def test_regestration():
    """test regestration"""
    plugins = discover_plugins(package_name="cmem_plugin_kaggle")
    assert len(plugins) > 0


def test_completion():
    """test completion"""
    parameter = KaggleSearch()
    completion = parameter.autocomplete(query_terms=[""])
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
    with pytest.raises(ValueError):
        KaggleImport(kaggle_dataset="sayansh001/crystal-structure-classification", file_name="data", dataset="hello")
    with pytest.raises(ValueError):
        KaggleImport(kaggle_dataset="https://www.kaggle.com/datasets/sayansh001/"
                                    "crystal-structure-classification", file_name="data",
                     dataset="crystal-structure-classification.csv")
