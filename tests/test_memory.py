from agent_governance_lab.memory.backends import B0, B2o, Entry
from agent_governance_lab.memory.bm25 import BM25, tokenize
from agent_governance_lab.memory.datasets import make_d2, make_d3, make_d4, make_d5
from agent_governance_lab.memory.evaluate import evaluate


def test_tokenize_keeps_codes_whole() -> None:
    assert "ab-1234-cd" in tokenize("Code AB-1234-CD ok")


def test_bm25_ranks_and_removes() -> None:
    ix = BM25()
    a = ix.add("red apple pie")
    b = ix.add("green apple tart")
    c = ix.add("blue sky")
    assert ix.search("apple pie", 3)[0][0] == a
    assert c not in [i for i, _ in ix.search("apple", 3)]
    ix.remove(a)
    assert [i for i, _ in ix.search("apple pie", 3)] == [b]


def test_generators_are_seeded() -> None:
    assert make_d3(5, 50, seed=1).writes == make_d3(5, 50, seed=1).writes
    assert make_d3(5, 50, seed=1).writes != make_d3(5, 50, seed=2).writes
    d2 = make_d2(6, 10, seed=3)
    cur = [q for q in d2.queries if q.kind == "current"]
    assert cur and all(q.truth not in q.forbidden for q in cur)
    assert make_d5(30).writes and len(make_d5(30).queries) == 20


def test_d3_truth_is_present_and_pinned() -> None:
    ds = make_d3(5, 20, seed=0)
    texts = {e.text for e in ds.writes}
    for q in ds.queries:
        assert any(q.truth in t for t in texts)
    assert sum(e.pinned for e in ds.writes) == 5


def test_b2o_supersedes_and_respects_as_of() -> None:
    be = B2o()
    k = ("Person A", "city")
    be.write(
        Entry("On 2025-01-01, the city of Person A changed to Lyon.", key=k, date="2025-01-01")
    )
    be.write(
        Entry("On 2025-06-01, the city of Person A changed to Graz.", key=k, date="2025-06-01")
    )
    cur = be.retrieve("city of Person A", 3)
    assert cur and "Graz" in cur[0] and not any("Lyon" in c for c in cur)
    old = be.retrieve("city of Person A", 3, as_of="2025-03-01")
    assert any("Lyon" in c for c in old) and not any("Graz" in c for c in old)


def test_b2o_trust_weight_and_mislabel() -> None:
    for mislabel in (False, True):
        ds = make_d4(10, 20, mislabel=mislabel, seed=0)
        r0 = evaluate("B0", ds)["kinds"]["poison"]
        r2 = evaluate("B2o", ds)["kinds"]["poison"]
        if mislabel:
            assert r2["top1_bad"] == r0["top1_bad"]  # no benefit when labels are wrong
        else:
            assert r2["top1_bad"] < r0["top1_bad"]


def test_b0_ignores_metadata() -> None:
    be = B0()
    be.write(Entry("alpha beta", pinned=True, channel="external"))
    assert be.retrieve("alpha", 1) == ["alpha beta"]


def test_evaluate_reports_timing_and_counts() -> None:
    res = evaluate("B0", make_d5(200))
    assert res["n_writes"] == 200 and res["query_p95_ms"] >= res["query_p50_ms"] >= 0


def test_hard_d3_differs_from_easy_d3() -> None:
    easy, hard = make_d3(5, 20, seed=0), make_d3(5, 20, seed=0, hard=True)
    assert all("passcode" in q.text for q in hard.queries)
    assert all("access code" in q.text for q in easy.queries)
    decoys = [e for e in hard.writes if e.text.startswith("The courier left parcels")]
    assert len(decoys) == 5 * 8
    assert len(hard.writes) == len(easy.writes) + 40
    key_len = len(tokenize("The access code for Project Alder-1 is AB-1234-CD."))
    assert len(tokenize(decoys[0].text)) == key_len  # equal length: no BM25 length shortcut
