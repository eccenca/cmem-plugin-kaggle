"""Kaggle Dataset workflow plugin module"""
from typing import Sequence, Tuple
import os
import time
from zipfile import ZipFile

from kaggle.api import KaggleApi
from cmem_plugin_base.dataintegration.context import (
    ExecutionContext,
    PluginContext,
    ExecutionReport,
)
from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.entity import Entities
from cmem_plugin_base.dataintegration.parameter.dataset import DatasetParameterType
from cmem_plugin_base.dataintegration.parameter.password import Password
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import StringParameterType, Autocompletion
from cmem_plugin_base.dataintegration.utils import write_to_dataset

api = KaggleApi()


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


def find_file(dataset_id: str, remote_file_name: str, context: ExecutionContext):
    """Check weather the file is downloaded or not"""
    file_path = f"./{remote_file_name}"
    if os.path.exists(file_path):
        create_resource_from_file(
            dataset_id=dataset_id, remote_file_name=remote_file_name, context=context
        )
    elif os.path.exists(get_zip_file_path(remote_file_name)):
        unzip_file(get_zip_file_path(remote_file_name))
        find_file(
            dataset_id=dataset_id, remote_file_name=remote_file_name, context=context
        )
    else:
        raise ValueError("FILE IS IN FOLDER")


def get_zip_file_path(file_name) -> str:
    """Returns the zip of a file name"""
    return f"{file_name}.zip"


def unzip_file(file_path):
    """Unzip the file"""
    with ZipFile(file_path, "r") as zip_file:
        zip_file.extractall("./")
        zip_file.close()


def create_resource_from_file(
    dataset_id: str, remote_file_name: str, context: ExecutionContext
):
    """Create Resource"""
    with open(remote_file_name, "rb") as response_file:
        write_to_dataset(
            dataset_id=dataset_id, file_resource=response_file, context=context.user
        )


def list_to_string(query_list: list[str]):
    """Converts each query term to a single search term"""

    string_join = ""
    return string_join.join(query_list)


def auth(username: str, access_token: str):
    """Kaggle Authenticate"""

    # Set environment variables
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = access_token
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


def change_space_format(string: str) -> bool:
    """Make changes"""
    for element in string:
        if element == " ":
            return True
    return False


class DatasetFile(StringParameterType):
    """Kaggle Dataset File Autocomplete"""

    autocompletion_depends_on_parameters: list[str] = ["kaggle_dataset"]

    # auto complete for values
    allow_only_autocompleted_values: bool = True
    # auto complete for labels
    autocomplete_value_with_labels: bool = False

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[str],
        context: PluginContext,
    ) -> list[Autocompletion]:
        result = []
        if len(query_terms) != 0:
            files = list_files(dataset=depend_on_parameter_values[0])
            for file in files:
                result.append(
                    Autocompletion(
                        value=f"{file}",
                        label=f"{file}",
                    )
                )
            result.sort(key=lambda x: x.label)  # type: ignore
            return result

        files = list_files(dataset=depend_on_parameter_values[0])
        for file in files:
            result.append(
                Autocompletion(
                    value=f"{file}",
                    label=f"{file}",
                )
            )
        result.sort(key=lambda x: x.label)  # type: ignore
        if len(result) == 0:
            value = ""
            label = "No files found for this dataset"
            result.append(Autocompletion(value=value, label=f"{label}"))
        return result


class KaggleSearch(StringParameterType):
    """Kaggle Search Type"""

    autocompletion_depends_on_parameters: list[str] = ["username", "access_token"]

    # auto complete for values
    allow_only_autocompleted_values: bool = True
    # auto complete for labels
    autocomplete_value_with_labels: bool = True

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[str],
        context: PluginContext,
    ) -> list[Autocompletion]:
        auth(depend_on_parameter_values[0], depend_on_parameter_values[1])
        result = []
        if len(query_terms) != 0:
            datasets = search(query_terms=query_terms)
            for dataset in datasets:
                slug = get_slugs(str(dataset))
                result.append(
                    Autocompletion(
                        value=f"{slug.owner}/{slug.name}",
                        label=f"{slug.owner}/{slug.name}",
                    )
                )
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
    plugin_id="cmem_plugin_kaggle",
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
            name="username",
            label="Kaggle Username",
            description="Username of kaggle account",
        ),
        PluginParameter(
            name="access_token",
            label="Kaggle Access Token",
            description="Access Token of kaggle account",
        ),
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
            param_type=DatasetFile(),
        ),
        PluginParameter(
            name="dataset",
            label="Dataset",
            description="To which Dataset to write the response",
            param_type=DatasetParameterType(dataset_type="csv"),
        ),
    ],
)
class KaggleImport(WorkflowPlugin):
    """Example Workflow Plugin: Kaggle Dataset"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        username: str,
        access_token: Password,
        kaggle_dataset: str,
        file_name: str,
        dataset: str,
    ) -> None:
        self.username = username
        self.access_token = access_token
        if api.validate_dataset_string(dataset=kaggle_dataset):
            raise ValueError("The specified dataset is not valid")
        if self.validate_file_name(dataset=kaggle_dataset, file_name=file_name):
            raise ValueError(
                "The specified file doesn't exists in the specified "
                f"dataset and it must be from "
                f"{list_files(kaggle_dataset)}"
            )
        self.kaggle_dataset = kaggle_dataset
        self.file_name = file_name
        self.dataset = dataset

    def execute(self, inputs: Sequence[Entities], context: ExecutionContext) -> None:
        summary: list[Tuple[str, str]] = []
        warnings: list[str] = []
        if context.user is None:
            warnings.append("User info not available")
        else:
            summary.append(("Executed by", context.user.user_uri()))

        self.log.info("Start loading kaggle dataset.")
        dataset_id = f"{context.task.project_id()}:{self.dataset}"

        if change_space_format(string=self.file_name):
            self.file_name = self.file_name.replace(" ", "%20")

        self.download_files(dataset=self.kaggle_dataset, file_name=self.file_name)
        time.sleep(1)
        find_file(
            dataset_id=dataset_id, remote_file_name=self.file_name, context=context
        )

        context.report.update(
            ExecutionReport(
                entity_count=1,
                operation="write",
                operation_desc="successfully downloaded",
                summary=summary,
                warnings=warnings,
            )
        )

    def validate_file_name(self, dataset: str, file_name: str) -> bool:
        """Validate File Exists"""
        auth(self.username, self.access_token.decrypt())
        files = list_files(dataset=dataset)
        for file in files:
            if str(file).lower() == file_name.lower():
                return False
        return True

    def download_files(self, dataset, file_name):
        """Kaggle Single Dataset File Download"""
        auth(self.username, self.access_token.decrypt())
        api.dataset_download_file(dataset=dataset, file_name=file_name, path="./")
