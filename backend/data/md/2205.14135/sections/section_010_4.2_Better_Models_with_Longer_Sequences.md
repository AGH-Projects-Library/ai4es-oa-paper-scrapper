## 4.2 Better Models with Longer Sequences

| Model implementations | Context length | OpenWebText (ppl) | Training time (speedup) |
| --- | --- | --- | --- |
| GPT-2 small - Megatron-LM | 1k | 18.2 | 4.7 days (1.0 × \times ) |
| GPT-2 small - FlashAttention | 1k | 18.2 | 2.7 days (1.7 × \times ) |
| GPT-2 small - FlashAttention | 2k | 17.6 | 3.0 days (1.6 × \times ) |
| GPT-2 small - FlashAttention | 4k | 17.5 | 3.6 days (1.3 × \times ) |

|  | 512 | 1024 | 2048 | 4096 | 8192 | 16384 |
| --- | --- | --- | --- | --- | --- | --- |
| MIMIC-III [ 47 ] | 52.8 | 50.7 | 51.7 | 54.6 | 56.4 | 57.1 |
| ECtHR [ 6 ] | 72.2 | 74.3 | 77.1 | 78.6 | 80.7 | 79.2 |

| Model | Path-X | Path-256 |
| --- | --- | --- |
| Transformer | ✗ | ✗ |
| Linformer [ 84 ] | ✗ | ✗ |
| Linear Attention [ 50 ] | ✗ | ✗ |
| Performer [ 12 ] | ✗ | ✗ |
| Local Attention [ 80 ] | ✗ | ✗ |
| Reformer [ 51 ] | ✗ | ✗ |
| SMYRF [ 19 ] | ✗ | ✗ |
| FlashAttention | 61.4 | ✗ |
| Block-sparse FlashAttention | 56.0 | 63.1 |

 The runtime and memory-efficiency of FlashAttention allow us to increase the context length of GPT-2 by 4 × \times while still running faster than the optimized implementation from Megatron-LM. Table 4 shows that that GPT-2 with FlashAttention and context length 4K is still 30% faster than GPT-2 from Megatron with context length 1K, while achieving 0.7 better perplexity. ![Table 4: GPT-2 small with FlashAttention , with 4 × \times larger context length compared to Megatron-LM, is still 30% faster while achieving 0.7 better perplexity. Training time on 8 × \times A100 GPUs is reported.]() [[TABLE_0]]  Training Transformers with longer sequences with FlashAttention improves performance on the MIMIC-III [ 47 ] and ECtHR [ 6 , 7 ] datasets. MIMIC-III contains intensive care unit patient discharge summaries, each annotated with multiple labels. ECtHR contains legal cases from the European Court of Human Rights, each of which is mapped to articles of the Convention of Human Rights that were allegedly violaged. Both of these datasets contain very long text documents; the average number of tokens in MIMIC is 2,395 tokens, and the longest document contains 14,562 tokens, while the average and longest numbers in ECtHR are 2,197 and 49,392, respectively. We evaluate lift from increasing the sequence length of a pretrained RoBERTa model [ 56 ] (we repeat the positional embeddings, as in Beltagy et al. [ 3 ] ). Table 6 shows that sequence length 16K outperforms length 512 by 4.3 points on MIMIC, and that length 8K outperforms length 512 by 8.5 points on ECtHR. The discrepancies may be due to subtle distribution shifts: MIMIC-III contains specialized medical text and thus may be more susceptible to a distribution shift in the document length, whereas ECtHR contains general language. ![Table 5: Long Document performance (micro F 1 subscript 𝐹 1 F_{1} ) at different sequence lengths using FlashAttention .]() ![Table 5: Long Document performance (micro F 1 subscript 𝐹 1 F_{1} ) at different sequence lengths using FlashAttention .]() [[TABLE_1]]  ![Table 6 : We report the first Transformer model that can achieve non-random performance on Path-X and Path-256.]() [[TABLE_2]]  The Path-X and Path-256 benchmarks are challenging tasks from the long-range arena benchmark designed to test long context. The task is to classify whether two points in a black and white 128 × \times 128 (or 256 × \times 256) image have a path connecting them, and the images are fed to the transformer one pixel at a time. In prior work, all transformer models have either run out of memory, or only achieved random performance [ 80 ] . There has been a search for alternative architectures that can model such long context [ 37 ] . We present here the first result of Transformer models being able to solve Path-X and Path-256 ( Table 6 ). We pretrain a transformer on Path-64, and then transfer to Path-X by spatially interpolating the positional embeddings. FlashAttention achieves 61.4 accuracy on Path-X. Additionally, block-sparse FlashAttention enables the Transformers to scale to sequence length 64K, achieving 63.1 accuracy 4 4 4 Path-256 requires longer sequences but has relatively shorter paths than Path-X, so it is easier to obtain a higher accuracy. on Path-256.