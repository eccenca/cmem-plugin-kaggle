"""Kaggle Dataset workflow plugin module"""

import os
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar
from zipfile import ZipFile

from cmem_plugin_base.dataintegration.context import (
    ExecutionContext,
    ExecutionReport,
    PluginContext,
)
from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.entity import Entities
from cmem_plugin_base.dataintegration.parameter.dataset import DatasetParameterType
from cmem_plugin_base.dataintegration.parameter.password import Password
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import Autocompletion, StringParameterType
from cmem_plugin_base.dataintegration.utils import write_to_dataset
from kaggle.api import KaggleApi
from kaggle.models.kaggle_models_extended import Dataset, File
from kaggle.rest import ApiException

api = KaggleApi()

DATASET_TYPES = {
    "csv": "csv",
    "json": "json",
    "xlsx": "excel",
    "xml": "xml",
    "zip": "multiCsv",
    "txt": "text",
}


@dataclass
class KaggleDataset:
    """Kaggle Dataset Object for Internal Purpose"""

    owner: str
    name: str


def get_slugs(dataset: str) -> KaggleDataset:
    """Dataset Slugs"""
    if "/" in dataset:
        api.validate_dataset_string(dataset)
        dataset_urls = dataset.split("/")
        return KaggleDataset(dataset_urls[0], dataset_urls[1])
    raise ValueError("Not a valid Kaggle Dataset name")


def upload_file(
    dataset_id: str, remote_file_name: str, path: str, context: ExecutionContext
) -> None:
    """Check whether the file is downloaded or not"""
    file_path = Path(path) / remote_file_name
    try:
        if file_path.is_file():
            create_resource_from_file(
                dataset_id=dataset_id, remote_file_name=file_path, context=context
            )
        elif Path(get_zip_file_path(file_path)).is_file():
            unzip_file(get_zip_file_path(file_path))
            upload_file(
                dataset_id=dataset_id,
                remote_file_name=remote_file_name,
                path=path,
                context=context,
            )
        else:
            raise FileNotFoundError  # noqa: TRY301
    except FileNotFoundError:
        files = os.listdir(path)
        paths = [str(Path(path) / file) for file in files]
        summary = [("Files in the downloaded directory", list_to_string(paths))]
        context.report.update(
            ExecutionReport(
                entity_count=0,
                operation="write",
                operation_desc="failed",
                summary=summary,
            )
        )


def get_zip_file_path(file_name: Path) -> str:
    """Return the zip of a file name"""
    return f"{file_name!s}.zip"


def unzip_file(file_path: str) -> None:
    """Unzip the file"""
    with ZipFile(file_path, "r") as zip_file:
        zip_file.extractall(Path(file_path).parent)
        zip_file.close()


def create_resource_from_file(
    dataset_id: str, remote_file_name: Path, context: ExecutionContext
) -> None:
    """Create Resource"""
    with Path(remote_file_name).open("rb") as response_file:
        write_to_dataset(dataset_id=dataset_id, file_resource=response_file, context=context.user)


def list_to_string(query_list: list[str]) -> str:
    """Convert each query term to a single search term"""
    string_join = ""
    return string_join.join(query_list)


def auth(username: str, api_key: str) -> None:
    """Kaggle Authenticate"""
    # Set environment variables
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = api_key
    api.authenticate()


def search(query: str) -> list[Dataset]:
    """Kaggle Dataset Search"""
    try:
        return api.dataset_list(search=query) if query else api.dataset_list()  # type: ignore[no-any-return]
    except ApiException:
        raise ValueError("Failed to authenticate with Kaggle API") from ApiException


def list_files(dataset: str) -> list[File]:
    """List Dataset Files"""
    return api.dataset_list_files(dataset).files  # type: ignore[no-any-return]


class DatasetFileType(DatasetParameterType):
    """Dataset File Type"""

    def __init__(self, dependent_params: list[str]):
        super().__init__()
        self.autocompletion_depends_on_parameters = dependent_params

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[Any],
        context: PluginContext,
    ) -> list[Autocompletion]:
        """Return all results that match ALL provided query terms."""
        _ = context
        try:
            self.dataset_type = DATASET_TYPES[depend_on_parameter_values[0].split(".")[-1]]
        except KeyError:
            self.dataset_type = ""
        return super().autocomplete(query_terms, depend_on_parameter_values, context)  # type: ignore[no-any-return]


class DatasetFile(StringParameterType):
    """Kaggle Dataset File Autocomplete"""

    autocompletion_depends_on_parameters: ClassVar[list[str]] = ["kaggle_dataset"]

    # auto complete for values
    allow_only_autocompleted_values: bool = True
    # auto complete for labels
    autocomplete_value_with_labels: bool = True

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[Any],
        context: PluginContext,
    ) -> list[Autocompletion]:
        """Return all results that match ALL provided query terms."""
        _ = context, query_terms
        if not depend_on_parameter_values:
            raise ValueError("Select dataset before choosing a file")

        result = []
        files = list_files(dataset=depend_on_parameter_values[0])
        count_csv = len([file for file in files if str(file).endswith(".csv")])
        can_support_multi_csv = count_csv == len(files) > 1
        if can_support_multi_csv:
            slug = get_slugs(depend_on_parameter_values[0])
            result.append(
                Autocompletion(
                    value=f"{slug.name}.zip",
                    label="Download all csv files as a Zip file",
                )
            )
        result += [Autocompletion(value=f"{file.name}", label=f"{file.name}") for file in files]
        if len(result) != 0:
            result.sort(key=lambda x: x.label)
        else:
            result.append(Autocompletion(value="", label="No files found for this dataset"))
        return result


class KaggleSearch(StringParameterType):
    """Kaggle Search Type"""

    autocompletion_depends_on_parameters: ClassVar[list[str]] = ["username", "api_key"]

    # auto complete for values
    allow_only_autocompleted_values: bool = True
    # auto complete for labels
    autocomplete_value_with_labels: bool = True

    def autocomplete(
        self,
        query_terms: list[str],
        depend_on_parameter_values: list[Any],
        context: PluginContext,
    ) -> list[Autocompletion]:
        """Return all results that match ALL provided query terms."""
        _ = context
        auth(depend_on_parameter_values[0], depend_on_parameter_values[1].decrypt())
        datasets = search(query="".join(query_terms))
        result = [Autocompletion(value=dataset.ref, label=dataset.ref) for dataset in datasets]
        result.sort(key=lambda x: x.label)
        return result


@Plugin(
    label="Kaggle",
    plugin_id="cmem_plugin_kaggle",
    description="Import dataset resources from Kaggle.",
    documentation="""
This workflow operator downloads a dataset from the Kaggle library.
To download datasets, you will need your Kaggle username and API Key,
which you can obtain from the [Kaggle Public API](https://www.kaggle.com/docs/api).
""",
    parameters=[
        PluginParameter(
            name="username",
            label="Kaggle Username",
            description="Username of Kaggle Account",
        ),
        PluginParameter(
            name="api_key",
            label="Kaggle Key",
            description="API Token of Kaggle Account",
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
            param_type=DatasetFileType(dependent_params=["file_name"]),
        ),
    ],
)
class KaggleImport(WorkflowPlugin):
    """Example Workflow Plugin: Kaggle Dataset"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        username: str,
        api_key: Password,
        kaggle_dataset: str,
        file_name: str,
        dataset: str,
    ) -> None:
        self.username = username
        self.api_key = api_key
        api.validate_dataset_string(dataset=kaggle_dataset)
        if not file_name.endswith(".zip") and self.validate_file_name(
            dataset=kaggle_dataset, file_name=file_name
        ):
            raise ValueError(
                "The specified file doesn't exists in the specified "
                f"dataset and it must be from "
                f"{list_files(kaggle_dataset)}"
            )
        self.kaggle_dataset = kaggle_dataset
        self.file_name = file_name
        self.dataset = dataset

    def execute(self, inputs: Sequence[Entities], context: ExecutionContext) -> None:
        """Execute the workflow plugin."""
        _ = inputs
        summary: list[tuple[str, str]] = []
        warnings: list[str] = []
        if context.user is None:
            warnings.append("User info not available")
        else:
            summary.append(("Executed by", context.user.user_uri()))

        self.log.info("Start loading kaggle dataset.")
        dataset_id = f"{context.task.project_id()}:{self.dataset}"

        dataset_file_name = self.get_downloadable_file_name()

        with tempfile.TemporaryDirectory() as temp_dir:
            context.report.update(
                ExecutionReport(
                    operation="wait",
                    operation_desc=f"{dataset_file_name} downloading",
                )
            )
            self.download_files(
                dataset=self.kaggle_dataset, file_name=dataset_file_name, path=temp_dir
            )
            time.sleep(1)
            upload_file(
                dataset_id=dataset_id,
                remote_file_name=dataset_file_name,
                path=temp_dir,
                context=context,
            )

        summary.append(("Kaggle Dataset", self.kaggle_dataset))
        summary.append(("File", dataset_file_name))
        summary.append(("Dataset ID", dataset_id))

        context.report.update(
            ExecutionReport(
                entity_count=1,
                operation="write",
                operation_desc=f"{dataset_file_name} downloaded",
                summary=summary,
                warnings=warnings,
            )
        )

    def get_downloadable_file_name(self) -> str:
        """Get the file name for the dataset"""
        dataset_filename = ""
        if "" in self.file_name:
            dataset_filename = self.file_name.replace(" ", "%20")

        if "." in dataset_filename:
            file_type = dataset_filename.split(".")[-1]
            if file_type in DATASET_TYPES:
                return dataset_filename

        return f"{get_slugs(self.kaggle_dataset).name}.zip"

    def validate_file_name(self, dataset: str, file_name: str) -> bool:
        """Validate File Exists"""
        auth(self.username, self.api_key.decrypt())
        files = list_files(dataset=dataset)
        return all(str(file.name).lower() != file_name.lower() for file in files)

    def download_files(self, dataset: str, file_name: str, path: str) -> None:
        """Kaggle Single Dataset File Download"""
        auth(self.username, self.api_key.decrypt())
        if file_name.endswith(".zip"):
            api.dataset_download_files(dataset=dataset, path=path)
        else:
            api.dataset_download_file(dataset=dataset, file_name=file_name, path=path)
