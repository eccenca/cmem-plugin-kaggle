"""Kaggle Dataset workflow plugin module"""

from typing import Optional
import os
from secrets import token_urlsafe, token_hex
import time
import kaggle

from cmem_plugin_base.dataintegration.description import (
    Plugin,
    PluginParameter
)

from cmem_plugin_base.dataintegration.utils import setup_cmempy_super_user_access

from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import (
    StringParameterType,
    Autocompletion
)
from cmem.cmempy.workspace.projects.datasets.dataset import create_dataset
from cmem.cmempy.workspace.projects.resources.resource import create_resource

RANDOM_FUNCTIONS = [
    ["token_urlsafe", "Return a random URL-safe text string."],
    ["token_hex", "Return a random text string, in hexadecimal."],
]

api = kaggle.api

KAGGLE_USERNAME = "rangareddynukala"
KAGGLE_KEY = "0678724483534d355962db8f07650473"


def _create_value(random_function: str, string_length: int = 16) -> str:
    """Create random values for import"""
    if random_function != "token_urlsafe":
        if random_function == "token_hex":
            return token_hex(string_length)
        raise ValueError("Unknown random function value.")
    return token_urlsafe(string_length)


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
        dataset_slugs = KaggleDataset(dataset_urls[1], dataset_urls[2])
        return dataset_slugs

    return None


def download_file(dataset, file_name):
    """dataset file download"""
    files = list_files(dataset)
    print(f"DATASET: {dataset}")
    print(f"FILES: {files}")

    if files is not None and len(files) != 0:
        for file in files:
            if str(file).lower() == file_name.lower():
                print("🐸 Downloading")
                # status = api.dataset_download_file(dataset, file_name=file_name)
                if "/" in dataset:
                    api.validate_dataset_string(dataset)
                    dataset_urls = dataset.split("/")
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
                        _preload_content=True,
                    )
                )
                return response
            return None
        return None
    return None


def create_dataset_from_file(sample_file_name):
    """Create Dataset"""
    # try:
    with open(sample_file_name, 'rb') as response_file:
        value = create_dataset(
            project_id='python-plugins',
            dataset_type='csv',
            parameter=None,
        )
        print(f'{response_file.read()}')
        print(f'HEY {value}')
    # except FileNotFoundError:
    #     print('File is missing')


def create_resource_from_file(sample_file_name):
    """Create Resource"""

    with open(sample_file_name, 'rb') as response_file:
        create_resource(
            project_name='python-plugins',
            resource_name=sample_file_name,
            file_resource=response_file,
            replace=False,
        )


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


def validate_file(dataset: str, file_name: str):
    """Validate File"""
    files = list_files(dataset)
    print(f"FILE NAMES: {files}")
    print(f"FILE NAME: {file_name}")


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


def search_dataset():
    """Search Dataset"""
    auth()
    datasets = search(query_terms=['o', 'n', 't', 'o', ' ', 'l', 'o', 'g', 'y'])
    print(len(datasets))
    for dataset in datasets:
        size = dataset.size
        slug = get_slugs(str(dataset))
        print(slug)
        dataset_name = f'{slug.owner}/{slug.name}'
        response = download_file(dataset_name, file_name='anime-ontology.csv')
        print(f'{slug.owner}: {slug.name} : {size}')
        tags = dataset.tags
        if len(tags) != 0:
            # for tag in tags:
            print(f'TAGs: {tags}')
        versions = dataset.versions
        if len(versions) != 0:
            # for version in versions:
            print(f'VERSIONs: {versions}')
        return response


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
        if not isinstance(dataset, str):
            raise ValueError("The specified Dataset is not valid")
        if not isinstance(file_name, str):
            raise ValueError("The specified File name is not valid")
        self.dataset = dataset
        self.file_name = file_name

    def execute(self, inputs=()):
        setup_cmempy_super_user_access()
        self.log.info("Start creating random values.")
        # self.log.info(f"Config length: {len(self.config.get())}")
        sample_dataset = 'imdevskp/cholera-dataset'
        sample_file_name = 'data.csv'
        download_files(dataset=sample_dataset, file_name=sample_file_name)
        time.sleep(6)

        create_resource_from_file(sample_file_name)
