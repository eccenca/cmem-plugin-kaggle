"""Kaggle Dataset workflow plugin module"""

from typing import Optional
import os

from kaggle.api import KaggleApi

from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import StringParameterType, Autocompletion
from cmem_plugin_base.dataintegration.entity import Entities

api = KaggleApi()

KAGGLE_USERNAME = 'rangareddynukala'
KAGGLE_KEY = '0678724483534d355962db8f07650473'


def get_dataset_value(dataset):
    """Returns Kaggle Dataset File Slug"""

    name = str(dataset)
    values = name.split("/")
    return values[2]


def get_dataset_label(dataset):
    """Returns Kaggle Dataset Owner Slug"""

    name = str(dataset)
    values = name.split("/")
    return values[1]


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
                size = dataset.size
                value = get_dataset_value(dataset)
                label = get_dataset_label(dataset)
                result.append(Autocompletion(value=value,
                                             label=f"{value}: {label} : {size}"))
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

- 'url': Path for the required dataset.
""",
    parameters=[
        PluginParameter(
            name="url",
            label="Dataset URL",
            description="URL for the dataset to download",
            param_type=KaggleSearch(),
        ),
    ],
)
class KaggleImport(WorkflowPlugin):
    """Example Workflow Plugin: Kaggle Dataset"""

    def __init__(
            self,
            url: str,
    ) -> None:
        if url is not str:
            raise ValueError("The specified URL is not valid")
        self.url = url

    def execute(self, inputs=()) -> None:
        self.log.info("Start creating random values.")
        self.log.info(f"Config length: {len(self.config.get())}")
        pass
