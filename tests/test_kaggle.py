"""Plugin tests."""
import pytest
from cmem_plugin_kaggle.kaggle_import import (
    KaggleImport,
    KaggleSearch
)
from cmem_plugin_base.dataintegration.discovery import discover_plugins


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


def test_failing_init():
    """Test RandomValues plugin."""
    with pytest.raises(ValueError):
        KaggleImport(kaggle_dataset="sayansh001/crystal-structure-classification", file_name="data", dataset="hello")
    with pytest.raises(ValueError):
        KaggleImport(kaggle_dataset="https://www.kaggle.com/datasets/sayansh001/"
                                    "crystal-structure-classification", file_name="data",
                     dataset="crystal-structure-classification.csv")
