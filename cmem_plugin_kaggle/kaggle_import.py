"""Kaggle Dataset workflow plugin module"""
from constants import KAGGLE_USERNAME,KAGGLE_KEY
import os
from typing import Optional
from kaggle.api.kaggle_api_extended import KaggleApi
from cmem_plugin_base.dataintegration.description import Plugin, PluginParameter
from cmem_plugin_base.dataintegration.plugins import WorkflowPlugin
from cmem_plugin_base.dataintegration.types import StringParameterType, Autocompletion


def list_to_string(query_list: [str]):
    string_result = ""
    for element in query_list:
        string_result += element
    return string_result


class KaggleSearch(StringParameterType):
    """Kaggle Search Type"""

    # auto complete for values
    allow_only_autocompleted_values: bool = True
    # auto complete for labels
    autocomplete_value_with_labels: bool = True

    def autocomplete(
            self, query_terms: list[str], project_id: Optional[str] = None
    ) -> list[Autocompletion]:
        result = []
        # Set environment variables
        os.environ['KAGGLE_USERNAME'] = KAGGLE_USERNAME
        os.environ['KAGGLE_KEY'] = KAGGLE_KEY
        api = KaggleApi()
        api.authenticate()
        if len(query_terms) != 0:
            datasets = api.dataset_list(search=list_to_string(query_list=query_terms))
            for dataset in datasets:
                value = str(dataset.size)
                label = str(dataset)
                result.append(Autocompletion(value=value, label=f"{label}"))
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

    def execute(self, inputs=()) -> str:
        self.log.info("Start creating random values.")
        self.log.info(f"Config length: {len(self.config.get())}")
        return self.url
