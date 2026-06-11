## 4.1 Faster Models with FlashAttention

| BERT Implementation | Training time (minutes) |
| --- | --- |
| Nvidia MLPerf 1.1 [ 58 ] | 20.0 ± plus-or-minus \pm 1.5 |
| FlashAttention (ours) | 17.4 ± plus-or-minus \pm 1.4 |

| Model implementations | OpenWebText (ppl) | Training time (speedup) |
| --- | --- | --- |
| GPT-2 small - Huggingface [ 87 ] | 18.2 | 9.5 days (1.0 × \times ) |
| GPT-2 small - Megatron-LM [ 77 ] | 18.2 | 4.7 days (2.0 × \times ) |
| GPT-2 small - FlashAttention | 18.2 | 2.7 days (3.5 × \times ) |
| GPT-2 medium - Huggingface [ 87 ] | 14.2 | 21.0 days (1.0 × \times ) |
| GPT-2 medium - Megatron-LM [ 77 ] | 14.3 | 11.5 days (1.8 × \times ) |
| GPT-2 medium - FlashAttention | 14.3 | 6.9 days (3.0 × \times ) |

| Models | ListOps | Text | Retrieval | Image | Pathfinder | Avg | Speedup |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Transformer | 36.0 | 63.6 | 81.6 | 42.3 | 72.7 | 59.3 | - |
| FlashAttention | 37.6 | 63.9 | 81.4 | 43.5 | 72.7 | 59.8 | 2.4 × \times |
| Block-sparse FlashAttention | 37.0 | 63.0 | 81.3 | 43.6 | 73.3 | 59.6 | 2.8 × \times |
| Linformer [ 84 ] | 35.6 | 55.9 | 77.7 | 37.8 | 67.6 | 54.9 | 2.5 × \times |
| Linear Attention [ 50 ] | 38.8 | 63.2 | 80.7 | 42.6 | 72.5 | 59.6 | 2.3 × \times |
| Performer [ 12 ] | 36.8 | 63.6 | 82.2 | 42.1 | 69.9 | 58.9 | 1.8 × \times |
| Local Attention [ 80 ] | 36.1 | 60.2 | 76.7 | 40.6 | 66.6 | 56.0 | 1.7 × \times |
| Reformer [ 51 ] | 36.5 | 63.8 | 78.5 | 39.6 | 69.4 | 57.6 | 1.3 × \times |
| Smyrf [ 19 ] | 36.1 | 64.1 | 79.0 | 39.6 | 70.5 | 57.9 | 1.7 × \times |

 FlashAttention yields the fastest single-node BERT training speed that we know of. We train a BERT-large [ 22 ] model with FlashAttention on Wikipedia. Table 1 compares our training time to the implementation from Nvidia that set the training speed record for MLPerf 1.1 [ 58 ] . Our implementation is 15% faster. ![Table 1: Training time of BERT-large, starting from the same initialization provided by the MLPerf benchmark, to reach the target accuracy of 72.0% on masked language modeling. Averaged over 10 runs on 8 × \times A100 GPUs.]() [[TABLE_0]]  FlashAttention yields faster training times for GPT-2 [ 67 ] on the large OpenWebtext dataset [ 32 ] than the widely used HuggingFace [ 87 ] and Megatron-LM [ 77 ] implementations. Table 2 shows up to 3 × \times end-to-end speedup compared to Huggingface and 1.7 × \times speedup compared to Megatron-LM. FlashAttention achieves the same perplexity as the other two implementations, as we do not change the model definition. Appendix E includes plots of the validation perplexity throughout training, confirming that FlashAttention is as numerically stable as the baselines and produces the same training / validation curves. ![Table 2: GPT-2 small and medium using FlashAttention achieve up to 3 × \times speed up compared to Huggingface implementation and up to 1.7 × \times compared to Megatron-LM. Training time reported on 8 × \times A100s GPUs.]() [[TABLE_1]]  We compare vanilla Transformer (with either standard implementation or FlashAttention ) on the long-range arena (LRA [ 80 ] ) benchmark. We measure accuracy, throughput, and training time of all models. Each task has a different sequence length varying between 1024 and 4096. We follow the implementation and experimental setting in Tay et al. [ 80 ] and Xiong et al. [ 90 ] . 3 3 3 LRA accuracy results are known to be highly dependent on the tuning procedure [ 90 ] . Our reproduced baselines perform better than as reported in the original comparison [ 80 ] . Table 3 shows that FlashAttention achieves up 2.4 × \times speed-up compared to standard attention. Block-sparse FlashAttention is faster than all of the approximate attention methods that we have tested. ![Table 3 : The performance of standard attention, FlashAttention , block-sparse FlashAttention , and approximate attention baselines on the Long-Range-Arena benchmarks.]() [[TABLE_2]] 