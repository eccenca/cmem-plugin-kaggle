"""Kaggle Dataset workflow plugin module"""

from typing import Optional
import os
from kaggle.api import KaggleApi

from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import StringParameterType, Autocompletion
from cmem.cmempy.workspace.projects.resources.resource import (
    create_resource,
)

api = KaggleApi()

KAGGLE_USERNAME = 'rangareddynukala'
KAGGLE_KEY = '0678724483534d355962db8f07650473'


class KaggleDataset:
    """ Kaggle Dataset Object for Internal Purpose"""

    def __init__(self, owner, name):
        """ Constructor """
        self.owner = owner
        self.name = name


def get_slugs(dataset):
    """ Dataset Slugs """
    if '/' in dataset:
        api.validate_dataset_string(dataset)
        dataset_urls = dataset.split('/')
        dataset_slugs = KaggleDataset(dataset_urls[1], dataset_urls[2])
        return dataset_slugs
    return None


def download_file(dataset, file_name):
    """ dataset file download """
    files = list_files(dataset)
    print(f'DATASET: {dataset}')
    print(f'FILES: {files}')

    if files is not None and len(files) != 0:
        for file in files:
            if str(file).lower() == file_name.lower():
                print("🐸 Downloading")
                # status = api.dataset_download_file(dataset, file_name=file_name)
                if '/' in dataset:
                    api.validate_dataset_string(dataset)
                    dataset_urls = dataset.split('/')
                    owner_slug = dataset_urls[0]
                    dataset_slug = dataset_urls[1]
                else:
                    owner_slug = api.get_config_value(api.CONFIG_NAME_USER)
                    dataset_slug = dataset

                response = api.process_response(
                    api.datasets_download_file_with_http_info(
                        owner_slug=owner_slug,
                        dataset_slug=dataset_slug,
                        file_name=file_name,
                        _preload_content=False))
                return response
            return None
        return None
    return None


def create_resource_from_file(dataset, file_name):
    """ Create Dataset """
    create_resource(
        project_name='python-plugins',
        resource_name='data.csv',
        file_resource=download_file(dataset=dataset, file_name=file_name),
        replace=True
    )


def list_to_string(query_list: list[str]):
    """Converts each query term to a single search term"""

    string_join = ""
    return string_join.join(query_list)


def auth():
    """Kaggle Authenticate"""

    # Set environment variables
    os.environ['KAGGLE_USERNAME'] = KAGGLE_USERNAME
    os.environ['KAGGLE_KEY'] = KAGGLE_KEY
    api.authenticate()


def search(query_terms: list[str]):
    """Kaggle Dataset Search"""

    datasets = api.dataset_list(search=list_to_string(query_list=query_terms))
    return datasets


def list_files(dataset):
    """ List Dataset Files """
    files = api.dataset_list_files(dataset).files
    if len(files) != 0:
        return files
    return None


def validate_file(dataset: str, file_name: str):
    """ Validate File """
    files = list_files(dataset)
    print(f'FILE NAMES: {files}')
    print(f'FILE NAME: {file_name}')


class KaggleSearch(StringParameterType):
    """Kaggle Search Type"""

    # auto complete for values
    allow_only_autocompleted_values: bool = True
    # auto complete for labels
    autocomplete_value_with_labels: bool = True

    def autocomplete(self,
                     query_terms: list[str], project_id: Optional[str] = None
                     ) -> list[Autocompletion]:
        auth()
        result = []
        if len(query_terms) != 0:
            datasets = search(query_terms=query_terms)
            for dataset in datasets:
                slug = get_slugs(str(dataset))
                result.append(Autocompletion(value=f"{slug.owner}/{slug.name}",
                                             label=f"{slug.owner}:{slug.name}"))
            result.sort(key=lambda x: x.label)  # type: ignore
            return result
        if len(query_terms) == 0:
            value = "Message"
            label = "Search for kaggle datasets"
            result.append(Autocompletion(value=value, label=f"{label}"))
        result.sort(key=lambda x: x.label)  # type: ignore
        return result


@Plugin(
    label="Kaggle",
    description="Download datasets from kaggle library",
    documentation="""
This example workflow operator downloads dataset from Kaggle library

The dataset will be loaded from the URL specified:

- 'dataset': Name of the dataset to be needed.
- 'file_name': Name of the file to be downloaded.
""",
    parameters=[
        PluginParameter(
            name="dataset",
            label="Dataset",
            description="Name of the dataset to be needed",
            param_type=KaggleSearch(),
        ),
        PluginParameter(
            name="file_name",
            label="File Name",
            description="Name of the file to be downloaded",
        ),
    ],
)
class KaggleImport(WorkflowPlugin):
    """Example Workflow Plugin: Kaggle Dataset"""

    def __init__(
            self,
            dataset: str,
            file_name: str,
    ) -> None:
        if dataset is not str:
            raise ValueError("The specified Dataset is not valid")
        self.dataset = dataset
        if file_name is not str:
            raise ValueError("The specified File name is not valid")
        self.file_name = file_name

    def execute(self, inputs=()) -> None:
        self.log.info("Start creating random values.")
        self.log.info(f"Config length: {len(self.config.get())}")
        create_resource_from_file(dataset=self.dataset, file_name=self.file_name)
        self.log.info("Resource Updated")
