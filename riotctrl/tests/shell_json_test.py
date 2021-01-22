"""riotctrl.shell.json test module"""

import logging

import pytest

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


def test_rapid_json_shell_interaction_parser_wo_rapidjson(caplog):
    """Test RapidJSONShellInteractionParser initialization without rapidjson
    installed"""
    with caplog.at_level(logging.WARNING,
                         logger='RapidJSONShellInteractionParser'):
        parser = riotctrl.shell.json.RapidJSONShellInteractionParser()
    assert "RapidJSONShellInteractionParser initialized without " \
        "rapidjson installed" in caplog.text
    with pytest.raises(AttributeError):
        parser.parse('[{"test": [1234, {"obj": {"val": 3.14}}]}]')


@pytest.mark.rapidjson
def test_rapid_json_shell_interaction_parser_w_rapidjson(caplog):
    """Test RapidJSONShellInteractionParser initialization with rapidjson
    installed"""
    # pylint: disable=import-outside-toplevel,import-error
    import rapidjson

    assert not caplog.text
    with caplog.at_level(logging.WARNING,
                         logger='RapidJSONShellInteractionParser'):
        parser = riotctrl.shell.json.RapidJSONShellInteractionParser()
    assert not caplog.text
    res = parser.parse('[{"test": [1234, {"obj": {"val": 3.14}}]}]')
    assert len(res) == 1
    assert len(res[0]) == 1
    assert len(res[0]["test"]) == 2
    assert res[0]["test"][0] == 1234
    assert len(res[0]["test"][1]) == 1
    assert len(res[0]["test"][1]["obj"]) == 1
    assert res[0]["test"][1]["obj"]["val"] == 3.14
    parser.set_parser_args(parse_mode=rapidjson.PM_TRAILING_COMMAS)
    res = parser.parse('[{"test": [1234, {"obj": {"val": 3.14},},],},]')
    assert len(res) == 1
    assert len(res[0]) == 1
    assert len(res[0]["test"]) == 2
    assert res[0]["test"][0] == 1234
    assert len(res[0]["test"][1]) == 1
    assert len(res[0]["test"][1]["obj"]) == 1
    assert res[0]["test"][1]["obj"]["val"] == 3.14
