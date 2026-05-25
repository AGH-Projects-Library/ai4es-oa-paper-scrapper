## C.3 Training Hyperparameters

| Hyperparameter | Value |
| --- | --- |
| Learning Rate | 2 × 10 − 4 2\times 10^{-4} |
| Optimizer | AdamW (8-bit) |
| Learning Rate Scheduler | Linear |
| Weight Decay | 0.001 |
| Warmup Steps | 5 |
| Maximum Training Steps | 600 |
| Random Seed | 3407 |

| Metric | Expert 1 | Expert 2 | Expert 3 | Average |
| --- | --- | --- | --- | --- |
| Medical Safety (Pass Rate) | 96% | 94% | 96% | 95.3% |
| Symptom Extraction | 4.2 | 4.1 | 4.3 | 4.20 |
| Context Memory | 4.4 | 4.3 | 4.5 | 4.40 |
| Diagnostic Correctness | 4.1 | 4.0 | 4.2 | 4.10 |
| Conversational Flow | 4.3 | 4.2 | 4.4 | 4.30 |
| Efficiency | 4.0 | 3.9 | 4.1 | 4.00 |

| Original Disease | Misclassified As | Frequency |
| --- | --- | --- |
| Pneumonia | Asthma | 3 |
| Esophagitis | Enteritis | 2 |
| Esophagitis | Asthma | 2 |
| Asthma | Pneumonia | 2 |
| Coronary heart disease | Asthma | 2 |
| Pneumonia | Enteritis | 2 |
| External otitis | Conjunctivitis | 2 |
| Conjunctivitis | Mastitis | 2 |
| Mastitis | Traumatic brain injury | 2 |
| Esophagitis | Coronary heart disease | 1 |

| Metric | Krippendorff’s α \alpha |
| --- | --- |
| Symptom Extraction | 0.82 |
| Context Memory | 0.84 |
| Diagnostic Correctness | 0.80 |
| Conversational Flow | 0.83 |
| Efficiency | 0.78 |
| Average | 0.81 |

 The main training hyperparameters are reported in Table 6 . ![Table 6: Training hyperparameters used for supervised fine-tuning.]() [[TABLE_0]]  ![Table 7: Medical expert evaluation of MedAidLM across 50 sampled dialogues. Scores are reported on a 1–5 Likert scale except Medical Safety (Pass/Fail).]() [[TABLE_1]]  ![Table 8: Most frequent disease-level misclassifications made by the final MedAidLM model.]() [[TABLE_2]]  ![Table 9: IAA scores across three medical experts.]() [[TABLE_3]] 