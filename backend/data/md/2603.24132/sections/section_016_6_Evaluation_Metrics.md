## 6 Evaluation Metrics

| Model Family | Dataset | Method | Accuracy |
| --- | --- | --- | --- |
| Mistral-7B-Instruct | MedAidDialog (MD+SYN) | SFT | 88.09% |
| LLaMA 3.2 3B (MedAidLM) | MedAidDialog (MD+SYN) | SFT | 90.21% |
| Qwen3-4B | MedAidDialog (MD+SYN) | SFT | 80.00% |
| DeepSeek-R1-Distill-Qwen-1.5B | MedAidDialog (MD+SYN) | SFT | 40.00% |

 ![Table 2: Results on the MedAidDialog dataset.]() [[TABLE_0]]  Evaluating conversational medical systems is challenging because a correct diagnosis alone does not guarantee a safe or clinically meaningful interaction. Therefore, we adopt a two-stage evaluation strategy consisting of (i) automatic evaluation based on diagnostic accuracy and (ii) human expert evaluation focusing on clinical reliability and conversational quality.