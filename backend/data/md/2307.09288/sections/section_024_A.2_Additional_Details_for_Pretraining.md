## A.2 Additional Details for Pretraining

| Context | NarrativeQA | Qasper | QuALITY | QMSum | ContractNLI | SQuAD |
| --- | --- | --- | --- | --- | --- | --- |
| Length | (F1) | (F1) | (acc) | (Rouge 1/2/L) | (EM) | (EM/F1) |
| 2k | 0.21 | 0.71 | 26.1 | 0.13/0.01/0.12 | 11.76 | 57.23/62.89 |
| 4k | 17.26 | 18.52 | 29.6 | 15.08 / 3.55 / 12.16 | 16.33 | 57.99 / 64.46 |

| Context | Hella- Swag | NQ | TQA | GSM8K | Human- Eval |
| --- | --- | --- | --- | --- | --- |
| Length | (0-shot) | (64-shot) | (64-shot) | (8-shot) | (0-shot) |
| 2k | 75.1 | 25.5 | 53.7 | 4.9 | 7.9 |
| 4k | 74.8 | 25.5 | 52.2 | 6.5 | 7.3 |

|  | BoolQ | PIQA | SIQA | Hella- Swag | ARC- e | ARC- c | NQ | TQA | MMLU | GSM8K | Human- Eval |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MHA | 71.0 | 79.3 | 48.2 | 75.1 | 71.2 | 43.0 | 12.4 | 44.7 | 28.0 | 4.9 | 7.9 |
| MQA | 70.6 | 79.0 | 47.9 | 74.5 | 71.6 | 41.9 | 14.5 | 42.8 | 26.5 | 4.8 | 7.3 |
| GQA | 69.4 | 78.8 | 48.6 | 75.4 | 72.1 | 42.5 | 14.0 | 46.2 | 26.9 | 5.3 | 7.9 |

|  |  | Humanities | STEM | Social Sciences | Other | Average |
| --- | --- | --- | --- | --- | --- | --- |
| MPT | 7B | 26.7 | 25.3 | 27.1 | 28.2 | 26.8 |
| 30B | 44.5 | 39.0 | 52.8 | 52.9 | 46.9 |  |
| Falcon | 7B | 26.4 | 26.2 | 24.7 | 27.4 | 26.2 |
| 40B | 49.3 | 45.5 | 65.4 | 65.0 | 55.4 |  |
| Llama 1 | 7B | 34.0 | 30.5 | 38.3 | 38.1 | 35.1 |
| 13B | 45.0 | 35.8 | 53.8 | 53.3 | 46.9 |  |
| 33B | 55.8 | 46.0 | 66.7 | 63.4 | 57.8 |  |
| 65B | 61.8 | 51.7 | 72.9 | 67.4 | 63.4 |  |
| Llama 2 | 7B | 42.9 | 36.4 | 51.2 | 52.2 | 45.3 |
| 13B | 52.8 | 44.1 | 62.6 | 61.1 | 54.8 |  |
| 34B | 59.4 | 52.1 | 71.8 | 69.2 | 62.6 |  |
| 70B | 65.0 | 58.0 | 80.3 | 74.6 | 68.9 |  |

|  |  | BoolQ | PIQA | SIQA | HellaSwag | WinoGrande | ARC-e | ARC-c | OBQA | CSQA | MMLU |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MPT | 7B | 75.0 | 80.6 | 48.5 | 76.4 | 68.3 | 70.2 | 42.6 | 51.4 | 21.3 | 26.8 |
| 30B | 79.0 | 81.9 | 48.9 | 79.9 | 71.0 | 76.5 | 50.6 | 52.0 | 58.2 | 46.9 |  |
| Falcon | 7B | 67.5 | 76.7 | 47.2 | 74.1 | 66.3 | 70.0 | 42.4 | 51.6 | 20.8 | 26.2 |
| 40B | 83.1 | 82.4 | 50.1 | 83.6 | 76.9 | 79.2 | 54.5 | 56.6 | 70.4 | 55.4 |  |
| Llama 1 | 7B | 76.5 | 79.8 | 48.9 | 76.1 | 70.1 | 72.8 | 47.6 | 57.2 | 33.6 | 35.1 |
| 13B | 78.1 | 80.1 | 50.4 | 79.2 | 73.0 | 74.8 | 52.7 | 56.4 | 62.0 | 46.9 |  |
| 33B | 83.1 | 82.3 | 50.4 | 82.8 | 76.0 | 80.0 | 57.8 | 58.6 | 72.5 | 57.8 |  |
| 65B | 85.3 | 82.8 | 52.3 | 84.2 | 77.0 | 78.9 | 56.0 | 60.2 | 74.0 | 63.4 |  |
| Llama 2 | 7B | 77.4 | 78.8 | 48.3 | 77.2 | 69.2 | 75.2 | 45.9 | 58.6 | 57.8 | 45.3 |
| 13B | 81.7 | 80.5 | 50.3 | 80.7 | 72.8 | 77.3 | 49.4 | 57.0 | 67.3 | 54.8 |  |
| 34B | 83.7 | 81.9 | 50.9 | 83.3 | 76.7 | 79.4 | 54.5 | 58.2 | 74.3 | 62.6 |  |
|  | 70B | 85.0 | 82.8 | 50.7 | 85.3 | 80.2 | 80.2 | 57.4 | 60.2 | 78.5 | 68.9 |

|  |  | Human-Eval | MBPP |
| --- | --- | --- | --- |
|  |  | pass@1 | pass@100 |
| MPT | 7B | 18.3 | - |
| 30B | 25.0 | - | 32.8 |
| Falcon | 7B | 0.0 | - |
| 40B | 0.6 | - | 29.8 |
| Llama 1 | 7B | 10.5 | 36.5 |
| 13B | 15.8 | 52.5 | 22.0 |
| 33B | 21.7 | 70.7 | 30.2 |
| 65B | 23.7 | 79.3 | 37.7 |
| Llama 2 | 7B | 12.8 | 45.6 |
| 13B | 18.3 | 60.2 | 30.6 |
| 34B | 22.6 | 77.2 | 33.0 |
| 70B | 29.9 | 89.0 | 45.0 |

|  |  | NaturalQuestions | TriviaQA (Wiki) |
| --- | --- | --- | --- |
|  |  | 0-shot | 1-shot |
| MPT | 7B | 11.6 | 17.8 |
| 30B | 15.8 | 23.0 | 26.6 |
| Falcon | 7B | 15.7 | 18.1 |
| 40B | 26.3 | 29.5 | 33.5 |
| Llama 1 | 7B | 16.8 | 18.7 |
| 13B | 20.1 | 23.4 | 28.1 |
| 33B | 24.9 | 28.3 | 32.9 |
| 65B | 23.8 | 31.0 | 35.0 |
| Llama 2 | 7B | 16.4 | 22.7 |
| 13B | 16.1 | 28.0 | 31.2 |
| 34B | 25.1 | 30.0 | 32.8 |
| 70B | 25.3 | 33.0 | 39.5 |

|  |  | SQUAD (EM) | QUAC (f1) |
| --- | --- | --- | --- |
| Model | Size | 0-shot | 1-shot |
| MPT | 7B | 59.5 | 62.8 |
| MPT | 30B | 74.7 | 74.2 |
| Falcon | 7B | 16.4 | 16.0 |
| Falcon | 40B | 72.9 | 73.1 |
| Llama 1 | 7B | 60.0 | 62.3 |
| 13B | 68.9 | 68.4 | 66.4 |
| 33B | 75.5 | 77.0 | 76.3 |
| 65B | 79.4 | 80.0 | 78.3 |
| Llama 2 | 7B | 67.2 | 72.3 |
| 13B | 72.9 | 72.1 | 70.6 |
| 34B | 77.4 | 78.8 | 77.5 |
| 70B | 80.7 | 82.6 | 81.9 |

| Model | Size | Avg | AQuA-RAT | LogiQA | LSAT-AR | LSAT-LR | LSAT-RC | SAT-en | SAT-en (w/o Psg.) | SAT-math |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MPT | 7B | 23.5 | 27.6 | 23.0 | 18.7 | 21.2 | 20.8 | 25.2 | 32.5 | 23.6 |
| MPT | 30B | 33.8 | 28.0 | 28.7 | 23.9 | 35.1 | 37.9 | 63.1 | 36.9 | 27.7 |
| Falcon | 7B | 21.2 | 21.7 | 22.3 | 16.1 | 17.3 | 20.4 | 26.2 | 23.8 | 26.4 |
| Falcon | 40B | 37.0 | 18.5 | 36.4 | 19.6 | 40.2 | 45.7 | 58.7 | 58.7 | 32.7 |
| Llama 1 | 7B | 23.9 | 18.9 | 24.6 | 26.1 | 19.2 | 21.9 | 33.0 | 32.5 | 22.3 |
| 13B | 33.9 | 20.1 | 34.9 | 22.2 | 31.6 | 39.8 | 52.9 | 45.1 | 29.5 |  |
| 33B | 41.7 | 18.9 | 37.3 | 18.7 | 48.0 | 59.5 | 74.8 | 44.7 | 35.0 |  |
| 65B | 47.6 | 23.6 | 42.1 | 23.9 | 56.7 | 63.6 | 83.0 | 48.1 | 41.8 |  |
| Llama 2 | 7B | 29.3 | 23.2 | 31.0 | 23.9 | 22.4 | 32.7 | 43.2 | 37.4 | 28.2 |
| 13B | 39.1 | 21.7 | 38.1 | 23.0 | 41.0 | 54.6 | 62.1 | 46.1 | 27.3 |  |
| 34B | 43.4 | 19.3 | 40.7 | 21.3 | 47.5 | 62.1 | 77.2 | 49.0 | 32.7 |  |
| 70B | 54.2 | 23.2 | 48.8 | 25.7 | 70.2 | 76.6 | 86.9 | 53.4 | 41.8 |  |

| Model | Size | GSM8k | MATH |
| --- | --- | --- | --- |
| MPT | 7B | 6.8 | 3.0 |
| 30B | 15.2 | 3.1 |  |
| Falcon | 7B | 6.8 | 2.3 |
| 40B | 19.6 | 5.5 |  |
| Llama 1 | 7B | 11.0 | 2.9 |
| 13B | 17.8 | 3.9 |  |
| 33B | 35.6 | 7.1 |  |
| 65B | 50.9 | 10.6 |  |
| Llama 2 | 7B | 14.6 | 2.5 |
| 13B | 28.7 | 3.9 |  |
| 34B | 42.2 | 6.24 |  |
| 70B | 56.8 | 13.5 |  |

 We expand the context window for Llama 2 from 2048 tokens to 4096 tokens. The longer context window enables models to process more information, which is particularly useful for supporting longer histories in chat applications, various summarization tasks, and understanding longer documents. Table 16 compares the performance of 2k and 4k context pretraining on long-context benchmarks. Both models are trained for 150B tokens, keeping the same architecture and hyperparameters as a baseline, varying only the context length. We observe improvement on SCROLLS (Shaham et al., 2022 ) , where the average input length is 3.5k, and no performance degradation on SQUAD (Rajpurkar et al., 2018 ) . Table 17 shows that the longer context model retains strong performance on various general-purpose tasks. ![Table 16: Context length ablation on long-context tasks.]() [[TABLE_0]]  ![Table 17: Context length ablation on general tasks.]() [[TABLE_1]]  A standard practice for autoregressive decoding is to cache the key (K) and value (V) pairs for the previous tokens in the sequence, speeding up attention computation. With increasing context windows or batch sizes, however, the memory costs associated with the KV cache size in multi-head attention (MHA) models grow significantly. For larger models, where KV cache size becomes a bottleneck, key and value projections can be shared across multiple heads without much degradation of performance (Chowdhery et al., 2022 ) . Either the original multi-query format with a single KV projection (MQA, Shazeer, 2019 ) or a grouped-query attention variant with 8 KV projections (GQA, Ainslie et al., 2023 ) can be used. In Table 18 , we compare MQA and GQA variants with an MHA baseline. We train all models with 150B tokens while keeping a fixed 30B model size. To keep a similar overall parameter count across GQA and MQA, we increase the dimension of the feed-forward layers to compensate for the reduction in the attention layers. For the MQA variant, we increase the FFN dimension by a factor of 1.33 1.33 1.33 , and for the GQA variant, we increase it by a factor of 1.3 1.3 1.3 . From the results, we observe that the GQA variant performs comparably to the MHA baseline on most evaluation tasks and is better than the MQA variant on average. ![Table 18: Attention architecture ablations. We report 0-shot results for all tasks except MMLU(5-shot) and GSM8K(8-shot). For GSM8K and Human-Eval we report maj@1 and pass@1 results. For NQ and TriviaQA we report EM. For all other tasks we report accuracy.]() [[TABLE_2]]  To optimize for latency, we host our largest models using 8 A100s in a single node with tensor parallelism (Shoeybi et al., 2019 ) . In this setting, sharding for MQA cannot be done across heads anymore, given the number of heads is lower than the number of GPUs. Either you duplicate the KV values in all GPUs (making the KV cache size equal to GQA), or an alternative is to shard across the batch dimension instead (Pope et al., 2022 ) . The latter, however, can complicate an inference service, as it works only when batch sizes are larger than the number of shards and the additional communication cost is not worth it in all cases. Therefore, based on the ablation results and ease of scaling inference, for the 34B and 70B Llama 2 models we chose to use GQA instead of MQA. ![Figure 24: Multi-query variants enable higher throughput with larger batch sizes, and show similar latency on smaller batches. Output length is fixed at 128 tokens. The first data point corresponds to batch size 1, and then we double it until the model runs out of memory. The MHA variant triggers an out-of-memory error at a batch size of 1024 for a context of 256 tokens and at a batch size of 128 for 2k context, whereas MQA and GQA have successful runs in those settings.](png/2307.09288/2307.09288/llama-mq-combined.png) Figure 24 shows how inference speed changed for the 30B GQA and MQA ablation models compared to the MHA baseline, in an experiment using 8 x 80 GiB A100s with tensor parallelism. In these runs we simply duplicated the KV heads for MQA in all GPUs, so the KV cache size for MQA became equal to the GQA and the two variants behaved very similar (with MQA just having a slightly larger FFN dimension). In Table 19 , we report details of the MMLU (Hendrycks et al., 2020 ) evaluation for Llama 2 models and others open-source models. ![Table 19: Five-shot performance on the Massive Multitask Language Understanding (MMLU) benchmark.]() [[TABLE_3]]  In Table 20 , we show results on several standard benchmarks. ![Table 20: Performance on standard benchmarks.]() [[TABLE_4]]  In Table 21 , we compare results of Llama 2 with popular open source models on the Human-Eval and MBPP code generation benchmarks. ![Table 21: Code generation results on Human-Eval and MBPP . We report 0-shot and 3-shot results for Human-Eval and MBPP respectively. For pass@100 and pass@80 scores, we use a temperature of 0.8 and top- p 𝑝 p =0.95. For pass@1 scores, we use a temperature of 0.1 and top- p 𝑝 p =0.95.]() [[TABLE_5]]  We evaluate the Llama 2 model together with other open-source models on the NaturalQuestions and TriviaQA benchmarks (Table 22 ). ![Table 22: (Left) NaturalQuestions. Exact match performance. (Right) TriviaQA. Zero-shot and few-shot exact match performance on the filtered dev set. For TriviaQA, we evaluate on Wiki validation subset.]() [[TABLE_6]]  In Table 23 we report zero-shot and few-shot results on SQUAD and zero-shot and one-shot experiments on QUAC. Here Llama 2 performs best on all evaluation settings and models except the QUAC 0-shot where Llama 1 30B performs slightly better. ![Table 23: Comparison to open-source models on reading comprehension (SQUAD and QUAC).]() [[TABLE_7]]  In Table 24 , we present fine-grained results from the English part of the AGI Eval (Zhong et al., 2023 ) benchmark. AGI Eval is a collection of standardized exams in different subjects. ![Table 24: Comparison to open source models on AGI Eval (English)]() [[TABLE_8]]  In Table 25 , we report results for Llama 2 and other open-source datasets on the GSM8k and MATH tasks. ![Table 25: Comparison to other open-source models on mathematical reasoning tasks , GSM8k and MATH (maj1@1 is reported).]() [[TABLE_9]] 