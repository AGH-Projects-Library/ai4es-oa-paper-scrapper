## Appendix D Contamination on academic benchmarks

| Benchmark | GPT-4 | GPT-3.5 | Contamination | GPT-4 (non-contaminated) | Degradation |
| --- | --- | --- | --- | --- | --- |
| MMLU | 86.4% | 70.0% | ~0.6% | - | - |
| GSM-8K | 92.0% | 57.1% | ~1% | - | - |
| HellaSwag | 95.3% | 85.5% | - * | - | - |
| AI2 | 96.3% | 85.2% | ~3.4% | - | - |
| WinoGrande | 87.5% | 81.6% | ~0.9% | - | - |
| HumanEval | 67.0% | 48.1% | 25% | 65.58% | -2.12% |
| DROP (F1) | 80.9 | 64.1 | ~21% | 82.8 * (subsample) | 0 |

 We measure cross-contamination between academic benchmarks and the pre-training data similarly to the methodology presented in Appendix C . Results are presented in Table 11 . ![Table 11 : Contamination between GPT-4 pre-training data and academic benchmarks. We report the approximate contamination between the GPT-4 pre-training data and the academic benchmarks we evaluate on. For datasets other than HumanEval, we estimated contamination based on 1000 randomly chosen examples against our training data. For HellaSwag, results are computed on a privately held secret holdout, so we did not check it for contamination against our pre-training dataset; however GPT-4’s holdout results are close to the results on the validation set (95.6%) which was explicitly masked out during training. For DROP, GPT-4’s score on the entire subsample was 82.5. We used the base GPT-4 model (without RLHF) for these evals.]() [[TABLE_0]] 