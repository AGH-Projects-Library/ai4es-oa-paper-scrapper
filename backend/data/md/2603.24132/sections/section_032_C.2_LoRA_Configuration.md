## C.2 LoRA Configuration

| Parameter | Value |
| --- | --- |
| Rank ( r r ) | 16 |
| Target Modules | q_proj, k_proj, v_proj, o_proj, |
|  | gate_proj, up_proj, down_proj |
| LoRA Alpha | 16 |
| LoRA Dropout | 0 |
| Bias | none |
| Use RSLora | False |
| LoftQ Config | None |

 Table 5 summarizes the LoRA configuration used in our experiments. ![Table 5: LoRA configuration used for parameter-efficient fine-tuning.]() [[TABLE_0]] 