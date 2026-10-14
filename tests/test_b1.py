import pytest

from agent_governance_lab.memory.b1 import B1
from agent_governance_lab.memory.backends import Entry


def test_channel_maps_to_episode_type() -> None:
    be = B1(generator=None, embed=lambda texts: None)  # type: ignore[arg-type,return-value]
    be.write(Entry("trusted fact", channel="trusted"))
    be.write(Entry("outside claim", channel="external"))
    t, x = be.records
    assert t["type"] == "insight" and t["data"]["observation"] == "trusted fact"
    assert x["type"] == "interaction" and x["data"]["direction"] == "received"
    assert x["data"]["content_summary"] == "outside claim"
    assert t["ts"] < x["ts"]


def test_retrieve_requires_finalize() -> None:
    be = B1(generator=None, embed=lambda texts: None)  # type: ignore[arg-type,return-value]
    with pytest.raises(RuntimeError):
        be.retrieve("anything")
