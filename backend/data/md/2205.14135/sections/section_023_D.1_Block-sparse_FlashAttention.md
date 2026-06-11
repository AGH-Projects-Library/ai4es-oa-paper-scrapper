## D.1 Block-sparse FlashAttention

|  | Θ ​ ( N ​ d + N 2 ​ d 2 M ​ s ) . Θ 𝑁 𝑑 superscript 𝑁 2 superscript 𝑑 2 𝑀 𝑠 \Theta\left(Nd+\frac{N^{2}d^{2}}{M}s\right). |  |
| --- | --- | --- |

 We describe the full block-sparse FlashAttention algorithm in Algorithm 5 . The algorithm is identical to Algorithm 2 , except that we skip zero blocks. ![Algorithm 5 Block-Sparse FlashAttention Forward Pass]() We prove the IO-complexity of block-sparse FlashAttention . The proof is very similar to the proof of Theorem 2 . For the block-sparse case, notice that we only need to load blocks corresponding to nonzero blocks. As a result, the number of HBM accesses are scaled by s 𝑠 s , the fraction of nonzero blocks in the block-sparsity mask. However, for small values of s 𝑠 s , we would still need to write the result 𝐎 ∈ ℝ N × d 𝐎 superscript ℝ 𝑁 𝑑 \mathbf{O}\in\mathbb{R}^{N\times d} . Therefore the number of HBM accesses is [[TABLE_0]]  ∎