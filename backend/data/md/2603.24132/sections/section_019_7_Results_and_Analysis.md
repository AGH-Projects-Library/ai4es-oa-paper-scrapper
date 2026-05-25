## 7 Results and Analysis

| Model | Dataset | Avg. Turns | Dialogs | Method | Accuracy |
| --- | --- | --- | --- | --- | --- |
| Mistral-7B-Instruct | MD | 4.90 | 1879 | SFT | 18.72% |
| Mistral-7B-Instruct | SYN | 7.28 | 1101 | SFT | 61.28% |
| Mistral-7B-Instruct | MD+SYN | 5.78 | 2980 | SFT | 80.85% |
| Mistral-7B-Instruct | MD+SYN | 5.78 | 2980 | SFT+GRPO | 77.87% |
| LLaMA 3.2 3B | MD | 4.90 | 1879 | SFT | 75.74% |
| LLaMA 3.2 3B | SYN | 7.28 | 1101 | SFT | 71.97% |
| LLaMA 3.2 3B | MD+SYN | 5.78 | 2980 | SFT | 77.87% |
| LLaMA 3.2 3B | MD+SYN | 5.78 | 2980 | SFT+GRPO | 43.83% |
| Qwen3-4B | MD+SYN | 5.78 | 2980 | SFT | 80.00% |
| DeepSeek-R1 | MD+SYN | 5.78 | 2980 | SFT | 40.00% |

 Table 2 presents the main automatic evaluation results, reporting only the best-performing configuration for each model family trained on the final MedAidDialog corpus. Among all evaluated compact models, LLaMA3.2-3B achieves the highest diagnostic accuracy of 90.21% , and we designate this final model as MedAidLM . Mistral-7B-Instruct also performs strongly with 88.09% accuracy, whereas Qwen3-4B reaches 80.00%. DeepSeek-R1-Distill-Qwen-1.5B performs substantially worse, suggesting that very small distilled reasoning models may be less suitable for this dialogue-driven medical prediction setting. These results indicate that compact open-source models can achieve strong diagnostic performance when trained on the augmented MedAidDialog corpus, even without relying on large proprietary systems. ![Table 3: Ablation study over training data composition and optimisation strategy. These experiments correspond to shorter training runs (100 steps), used to analyze the effect of original data (MD), synthetic data (SYN), and the combined MedAidDialog corpus (MD+SYN).]() [[TABLE_0]] 