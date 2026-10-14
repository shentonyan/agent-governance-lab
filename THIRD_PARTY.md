# Third-party material

Nothing below is vendored in this repository. `scripts/fetch_upstream.py` clones pinned
revisions into `third_party/` (gitignored) for local use.

| Project | License | Use here | Pin |
|---|---|---|---|
| shentonyan/contemplative-agent (fork of shimo4228/contemplative-agent) | MIT | agent core run as a library/process | `4f070f2b2e2b36864762656a70aa7cb42adb0273` |
| shimo4228/contemplative-agent-rules | verify before use | upstream axioms text, input to variant generation | `c21be2b45f26e06505a4b9d4ce3bd985fce828bb` |
| naturaldao/NaturalDAO | CC0-1.0 at time of writing; the maintainers have said the license may change | source of design ideas; record commit SHA and date whenever text is used | record at use |
| OpenViking | AGPL-3.0 | external process for comparison only; never imported or copied | version recorded per run |
| LoCoMo, HateCheck, ToxiGen, COLD | verify each | evaluation data, downloaded locally, not redistributed | record at use |

Rule: if a license is unverified, the material is not committed here.

## Datasets and models used by experiments 2 and 3

- HateCheck (Rottger et al., 2021), https://github.com/paul-rottger/hatecheck-data. Downloaded by the user into data/raw (not committed); only case ids and hashes are in data/exp03/c_manifest.json. Licence to be confirmed against the repository before any redistribution.
- nomic-embed-text, served by a local Ollama, used as the dense retriever. Model licence per its Ollama library page.
