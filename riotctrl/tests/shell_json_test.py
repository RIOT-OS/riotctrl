"""riotctrl.shell.json test module"""

import riotctrl.shell.json


def test_json_shell_interaction_parser():
    """Test JSON parsing"""
    parser = riotctrl.shell.json.JSONShellInteractionParser()

    res = parser.parse('[{"test": [1234, {"obj": {"val": 3.14}}]}]')
    assert len(res) == 1
    assert len(res[0]) == 1
    assert len(res[0]["test"]) == 2
    assert res[0]["test"][0] == 1234
    assert len(res[0]["test"][1]) == 1
    assert len(res[0]["test"][1]["obj"]) == 1
    assert res[0]["test"][1]["obj"]["val"] == 3.14
