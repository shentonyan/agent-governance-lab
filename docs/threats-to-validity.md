# Threats to validity (living document)

- **Single model family.** Results on one local model may not transfer.
- **Non-determinism.** Seeding is repeatable per machine/build only; GPU and Ollama version can change outputs.
- **Wording vs. content.** A heading change can shift the `constitutional` view's centroid upstream; experiments separate a live-lens arm from a frozen-lens arm.
- **Translation.** zh variants are separate wording conditions, not validated translations.
- **Metric validity.** Automated judges can share errors; reviewer error correlation (phi) is reported.
- **Benchmark transfer.** Published memory-benchmark numbers used different models and are not comparable.
- **Multiple comparisons.** Holm correction over the pre-registered family; anything else is exploratory.
- **Floor and ceiling effects.** If a probe's unsafe option is never chosen, any wording looks equivalent. Pilot 1 hit this on both models tried; probes must show headroom first.
- **Exp 1 length confound.** In the F1 probes the honest option is about 30% longer than the comforting one. The contrasts between wordings are within scenario, but the absolute log-odds level partly reflects this.
- **Exp 1 weak headroom.** With `llama3.1:8b`, only 5 of 40 F1 scenarios have order-averaged P(comforting-false) between 0.1 and 0.9. Power is low, so "no difference detected" is not evidence of equivalence.
- **Exp 1 model choice.** `qwen2.5:7b` is saturated under the probability readout and `gemma4:26b` could not be read (code-fence output). The primary model differs from the upstream default, so numbers do not compare with upstream.
- **Exp 1 readout.** Logit-based readout measures the model's next-token preference for an answer letter, not what it would write in an open reply. Two option orders are averaged to cancel position bias, not to remove it from the model.
- **Exp 1 post-hoc gate change.** The 10–90% sensitivity rule was relaxed for F1 after seeing pilot data; declared in `PREREG.md`.
- **Exp 2 oracle metadata.** B2o receives the (entity, attribute) key and the channel label from the dataset generator. Its advantage on D2 and D4 shows what the mechanisms can do with perfect fact matching and labelling; the mislabelled D4 variant shows the advantage vanishing with wrong labels.
- **Exp 2 saturation.** D3 is saturated for lexical retrieval at the default size; it does not yet separate backends. Synthetic strings are also unlike natural dialogue.
- **Exp 2 missing arms.** The upstream distillation pipeline and OpenViking are not implemented, so the design's main predictions (P1, P3) are untested.
- **Exp 3 prompt–test overlap.** The safety reviewer prompt lists the behaviour classes that category D tests. A first pilot hit a ceiling on the explicit tier; the implicit tier and near-miss skills were added after seeing it, so dev results are not independent of design choices.
- **Exp 3 small n and one author.** Test proposals are hand-written by the harness author with no second annotator; dev has 28 bad proposals, so intervals are wide. Category C (hate patterns) is not yet built.
