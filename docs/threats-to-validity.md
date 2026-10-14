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
