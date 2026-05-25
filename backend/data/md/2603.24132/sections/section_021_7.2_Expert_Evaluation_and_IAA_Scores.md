## 7.2 Expert Evaluation and IAA Scores

| Disease | Correct | Total | Accuracy |
| --- | --- | --- | --- |
| Asthma | 16 | 19 | 84.2% |
| Conjunctivitis | 19 | 21 | 90.5% |
| Coronary heart disease | 16 | 19 | 84.2% |
| Dermatitis | 19 | 20 | 95.0% |
| Enteritis | 22 | 24 | 91.7% |
| Esophagitis | 22 | 27 | 81.5% |
| External otitis | 15 | 17 | 88.2% |
| Mastitis | 12 | 15 | 80.0% |
| Pneumonia | 12 | 20 | 60.0% |
| Rhinitis | 15 | 15 | 100.0% |
| Thyroiditis | 19 | 19 | 100.0% |
| Traumatic brain injury | 19 | 19 | 100.0% |

 As shown in Table 7 , MedAidLM achieves a 95.3% medical safety pass rate, indicating that unsafe advice is rare in the sampled dialogues. The model also obtains strong average scores for symptom extraction (4.20), context memory (4.40), diagnostic correctness (4.10), conversational flow (4.30), and efficiency (4.00). These results suggest that the model is able to track relevant symptoms, preserve dialogue context, and conduct multi-turn interactions in a clinically plausible and reasonably efficient manner. To validate the reliability of these judgments, we compute inter-annotator agreement (IAA) using Krippendorff’s alpha Krippendorff ( 2011 ) . Table 9 shows an average agreement score of 0.81 , indicating strong consistency among the medical experts. ![Table 4: Per-disease diagnostic accuracy of the final MedAidLM model on the evaluation set.]() [[TABLE_0]] 