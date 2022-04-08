"""Plugin tests."""
from kaggle_import import KaggleImport
from cmem_plugin_base.dataintegration.discovery import discover_plugins


# package prefix
def test_regestration():
    plugins = discover_plugins(package_name="cmem_plugin_kaggle")
    assert len(plugins) > 0


def test_execution():
    """Test plugin execution"""
    url = "http://winterolympicsmedals.com/medals.csv"

    plugin = KaggleImport(url=url)
    plugin.execute()
    # write assertions
