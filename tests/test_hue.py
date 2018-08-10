"""
Test hue.py
"""

from .context import hue


def test_parse_zgp():
    """Test parse_zgp."""
    dummy_data = {'name': None,
                  'state': {'buttonevent': None,
                            'lastupdated': "2017-10-13T06:01:10"},
    }           
    assert hue.parse_zgp(dummy_data)['state'] == 'No data'
