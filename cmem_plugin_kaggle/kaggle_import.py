"""Kaggle Dataset workflow plugin module"""
from typing import Optional
import os
import time
from zipfile import ZipFile
from kaggle.api import KaggleApi

from cmem_plugin_base.dataintegration.description import (
    Plugin,
    PluginParameter
)

from cmem_plugin_base.dataintegration.utils import (
    setup_cmempy_super_user_access,
    split_task_id
)
from cmem_plugin_base.dataintegration.parameter.dataset import DatasetParameterType
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import (
    StringParameterType,
    Autocompletion
)
from cmem.cmempy.workspace.projects.resources.resource import (
    create_resource,
)
from cmem.cmempy.workspace.tasks import get_task

api = KaggleApi()

KAGGLE_USERNAME = "rangareddynukala"
KAGGLE_KEY = "0678724483534d355962db8f07650473"


class KaggleDataset:
    """Kaggle Dataset Object for Internal Purpose"""

    def __init__(self, owner, name):
        """Constructor"""
        self.owner = owner
        self.name = name


def get_slugs(dataset):
    """Dataset Slugs"""
    if "/" in dataset:
        api.validate_dataset_string(dataset)
        dataset_urls = dataset.split("/")
        dataset_slugs = KaggleDataset(dataset_urls[0], dataset_urls[1])
        return dataset_slugs
    return None


def find_file(project_id: str, remote_file_name: str, dataset_file_name: str):
    """ Check weather the file is downloaded or not"""
    file_path = f'./{remote_file_name}'
    if os.path.exists(file_path):
        create_resource_from_file(project_id=project_id,
                                  remote_file_name=remote_file_name,
                                  dataset_file_name=dataset_file_name)
    elif os.path.exists(get_zip_file_path(remote_file_name)):
        unzip_file(get_zip_file_path(remote_file_name))
        find_file(project_id=project_id,
                  remote_file_name=remote_file_name,
                  dataset_file_name=dataset_file_name)
    else:
        raise ValueError('FILE IS IN FOLDER')


def get_zip_file_path(file_name) -> str:
    """ Returns the zip of a file name"""
    return f'{file_name}.zip'


def unzip_file(file_path):
    """ Unzip the file """
    with ZipFile(file_path, 'r') as zip_file:
        zip_file.extractall('./')
        zip_file.close()


def create_resource_from_file(project_id: str,
                              remote_file_name: str,
                              dataset_file_name: str):
    """Create Resource"""
    with open(remote_file_name, 'rb') as response_file:
        create_resource(
            project_name=project_id,
            resource_name=get_file_name_of_dataset(project_id=project_id,
                                                   task_id=dataset_file_name),
            file_resource=response_file,
            replace=True,
        )


def get_file_name_of_dataset(project_id: str, task_id: str) -> str:
    """Get Resource name of  a dataset in a project"""
    task_meta_data = get_task(project=project_id, task=task_id)
    resource_name = str(task_meta_data["data"]["parameters"]["file"]["value"])
    return resource_name


def list_to_string(query_list: list[str]):
    """Converts each query term to a single search term"""

    string_join = ""
    return string_join.join(query_list)


def auth():
    """Kaggle Authenticate"""

    # Set environment variables
    os.environ["KAGGLE_USERNAME"] = KAGGLE_USERNAME
    os.environ["KAGGLE_KEY"] = KAGGLE_KEY
    api.authenticate()


def search(query_terms: list[str]):
    """Kaggle Dataset Search"""

    datasets = api.dataset_list(search=list_to_string(query_list=query_terms))
    return datasets


def list_files(dataset):
    """List Dataset Files"""
    files = api.dataset_list_files(dataset).files
    if len(files) != 0:
        return files
    return None


def validate_file_name(dataset: str, file_name: str) -> bool:
    """ Validate File Exists"""
    auth()
    files = list_files(dataset=dataset)
    for file in files:
        if str(file).lower() == file_name.lower():
            return False
    return True


def change_space_format(string: str) -> bool:
    """Make changes"""
    for element in string:
        if element == " ":
            return True
    return False


class KaggleSearch(StringParameterType):
    """Kaggle Search Type"""

    # auto complete for values
    allow_only_autocompleted_values: bool = True
    # auto complete for labels
    autocomplete_value_with_labels: bool = True

    def autocomplete(
            self, query_terms: list[str], project_id: Optional[str] = None
    ) -> list[Autocompletion]:

        auth()
        result = []
        if len(query_terms) != 0:
            datasets = search(query_terms=query_terms)
            for dataset in datasets:
                slug = get_slugs(str(dataset))
                result.append(Autocompletion(value=f"{slug.owner}/{slug.name}",
                                             label=f"{slug.owner}/{slug.name}"))
            result.sort(key=lambda x: x.label)  # type: ignore
            return result
        if len(query_terms) == 0:
            value = "Message"
            label = "Search for kaggle datasets"
            result.append(Autocompletion(value=value, label=f"{label}"))
        result.sort(key=lambda x: x.label)  # type: ignore
        return result


def download_files(dataset, file_name):
    """Kaggle Single Dataset File Download"""
    auth()
    api.dataset_download_file(dataset=dataset, file_name=file_name, path="./")


@Plugin(
    label="Kaggle",
    plugin_id="kaggle",
    description="Download datasets from kaggle library",
    documentation="""
This example workflow operator downloads dataset from Kaggle library

The dataset will be loaded from the URL specified:

- `kaggle_dataset`: Name of the dataset to be needed.
- `file_name`: Name of the file to be downloaded.
- `dataset`: To which Dataset to write the response.
""",
    parameters=[
        PluginParameter(
            name="kaggle_dataset",
            label="Kaggle Dataset",
            description="Name of the dataset to be needed",
            param_type=KaggleSearch(),
        ),
        PluginParameter(
            name="file_name",
            label="File Name",
            description="Name of the file to be downloaded",
        ),
        PluginParameter(
            name="dataset",
            label="Dataset",
            description="To which Dataset to write the response",
            param_type=DatasetParameterType(dataset_type="csv")
        )
    ],
)
class KaggleImport(WorkflowPlugin):
    """Example Workflow Plugin: Kaggle Dataset"""

    def __init__(
            self,
            kaggle_dataset: str,
            file_name: str,
            dataset: str = "",
    ) -> None:
        if api.validate_dataset_string(dataset=kaggle_dataset):
            raise ValueError("The specified dataset is not valid")
        if validate_file_name(dataset=kaggle_dataset, file_name=file_name):
            raise ValueError("The specified file doesn't exists in the specified "
                             f"dataset and it must be from "
                             f"{list_files(kaggle_dataset)}")
        self.kaggle_dataset = kaggle_dataset
        self.file_name = file_name
        self.dataset = dataset

        project_name, task_name = split_task_id(self.dataset)
        self.project_name = project_name
        self.task_name = task_name

    def execute(self, inputs=()):
        setup_cmempy_super_user_access()
        self.log.info("Start loading kaggle dataset.")
        if change_space_format(string=self.file_name):
            self.file_name = self.file_name.replace(" ", "%20")

        download_files(dataset=self.kaggle_dataset, file_name=self.file_name)
        time.sleep(1)
        find_file(project_id=self.project_name,
                  remote_file_name=self.file_name,
                  dataset_file_name=self.task_name)
