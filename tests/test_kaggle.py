"""Plugin tests."""
from cmem_plugin_kaggle import DollyPlugin


def test_execution():
    """Test plugin execution"""
    entities = 100
    values = 10

    plugin = DollyPlugin(number_of_entities=entities, number_of_values=values)
    result = plugin.execute()
    for item in result.entities:
        assert len(item.values) == len(result.schema.paths)

