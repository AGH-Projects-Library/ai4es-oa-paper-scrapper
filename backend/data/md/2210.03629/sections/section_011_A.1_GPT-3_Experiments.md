## A.1 GPT-3 Experiments

|  | PaLM-540B | GPT-3 |
| --- | --- | --- |
| HotpotQA (exact match) | 29.4 | 30.8 |
| ALFWorld (success rate %) | 70.9 | 78.4 |

 ![Table 5: \model prompting results using PaLM-540B vs. GPT-3 (text-davinci-002, greedy decoding). On HotpotQA, we randomly sample a subset of 500 validation questions. On ALFWorld, we use all 134 unseen validation task instances, and use the best prompt set according to PaLM-540B.]() [[TABLE_0]]  We run additional GPT-3 (Brown et al., 2020 ) experiments to confirm \model prompting performance is general across different large language models. As shown in Table 5 , GPT-3 (text-davinci-002, greedy decoding) consistently outperforms PaLM-540B on HotpotQA and ALFWorld, possibly because it is finetuned with human instruction following. This indicates ReAct prompting is effective across different large language models on different tasks. The code for these experiments are at https://react-lm.github.io/ .