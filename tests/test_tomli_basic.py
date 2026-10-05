"""Basic behaviour tests for the vendored TOML parser (run with `python3 -m pytest -q`)."""
import datetime as dt

import pytest

import tomli


def test_empty_document():
    assert tomli.loads("") == {}
    assert tomli.loads("# just a comment\n\n   \n") == {}


def test_scalars():
    doc = 'name = "harbor"\nreplicas = 3\nratio = 0.25\nenabled = true\nlegacy = false\n'
    assert tomli.loads(doc) == {
        "name": "harbor", "replicas": 3, "ratio": 0.25, "enabled": True, "legacy": False,
    }


def test_integer_forms():
    doc = "a = 1_000\nb = 0xFF\nc = 0o17\nd = 0b101\ne = -42\nf = +7\n"
    assert tomli.loads(doc) == {"a": 1000, "b": 255, "c": 15, "d": 5, "e": -42, "f": 7}


def test_tables_and_dotted_keys():
    doc = (
        "[cluster]\n"
        "name = 'prod'\n"
        "limits.cpu = 4\n"
        "limits.memory_mb = 2048\n"
        "[cluster.network]\n"
        'cidr = "10.0.0.0/16"\n'
    )
    assert tomli.loads(doc) == {
        "cluster": {
            "name": "prod",
            "limits": {"cpu": 4, "memory_mb": 2048},
            "network": {"cidr": "10.0.0.0/16"},
        }
    }


def test_array_of_tables_with_subtables():
    doc = (
        "[[service]]\nname = 'a'\n[service.env]\nLEVEL = 'info'\n"
        "[[service]]\nname = 'b'\n[service.env]\nLEVEL = 'debug'\n"
    )
    assert tomli.loads(doc) == {
        "service": [
            {"name": "a", "env": {"LEVEL": "info"}},
            {"name": "b", "env": {"LEVEL": "debug"}},
        ]
    }


def test_inline_tables_and_arrays():
    doc = 'pt = { x = 1, y = 2 }\nnames = [\n  "a", # first\n  "b",\n]\nmixed = [[1, 2], ["x"]]\n'
    assert tomli.loads(doc) == {"pt": {"x": 1, "y": 2}, "names": ["a", "b"], "mixed": [[1, 2], ["x"]]}


def test_dates_and_times():
    doc = (
        "odt = 2026-09-14T08:15:30+02:00\n"
        "ldt = 2026-09-14T08:15:30\n"
        "ld = 2026-09-14\n"
        "lt = 08:15:30.5\n"
    )
    got = tomli.loads(doc)
    assert got["odt"] == dt.datetime(2026, 9, 14, 8, 15, 30, tzinfo=dt.timezone(dt.timedelta(hours=2)))
    assert got["ldt"] == dt.datetime(2026, 9, 14, 8, 15, 30)
    assert got["ld"] == dt.date(2026, 9, 14)
    assert got["lt"] == dt.time(8, 15, 30, 500000)


def test_basic_string_escapes():
    assert tomli.loads(r'a = "tab\there é \"q\""') == {"a": 'tab\there é "q"'}


def test_multiline_strings():
    doc = 'a = """\nfirst\nsecond"""\nb = \'\'\'\nraw \\n stays\n\'\'\'\n'
    assert tomli.loads(doc) == {"a": "first\nsecond", "b": "raw \\n stays\n"}


def test_line_ending_backslash_joins_lines():
    doc = 'a = """one \\\n     two \\\n     three"""\n'
    assert tomli.loads(doc) == {"a": "one two three"}


def test_invalid_documents_raise():
    for bad in ("a = ", "a = 1\na = 2\n", "[t]\n[t]\n", 'a = "unterminated'):
        with pytest.raises(tomli.TOMLDecodeError):
            tomli.loads(bad)


def test_issue_reproduction():
    """From deploy/platform.toml: the PagerDuty template body (line-ending backslashes, then a
    blank line, then the runbook line). tomllib returns the text below."""
    doc = (
        "[template]\n"
        'body = """\\\n'
        "    The payments service has been unhealthy for more than five minutes. \\\n"
        "    Check the dashboard first, then follow the linked runbook. \\\n"
        "\n"
        "    Runbook: https://wiki.example.internal/RB-0012\n"
        '    """\n'
    )
    assert tomli.loads(doc)["template"]["body"] == (
        "The payments service has been unhealthy for more than five minutes. "
        "Check the dashboard first, then follow the linked runbook. "
        "Runbook: https://wiki.example.internal/RB-0012\n    "
    )
