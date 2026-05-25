## 4.1 Synthetic Dialogue Generation

|  | Dialogue Turns | Average Words |
| --- | --- | --- |
| Dataset | Avg | Total |
|  | Turns | Dialogues |
| MDDial (MD) | 4.9 | 1879 |
| Synthetic (SYN) | 6.6 | 1101 |
| MD + SYN | 5.7 | 2980 |
| MDDial Test | 5.9 | 237 |

 To increase conversational diversity beyond template-based dialogues, we generate synthetic medical consultations using the Llama-3.3-70B-Versatile model through the Groq API 1 1 1 https://groq.com/ . The model architecture follows the design described in the Llama 3 model card (AI@Meta, 2024 ) . The generation pipeline simulates diagnostic consultations involving 12 diseases and 118 symptoms. Each dialogue begins with a randomized patient complaint and proceeds through multiple conversational exchanges in which the physician asks follow-up questions to gather diagnostic evidence. Dialogues typically contain 4–8 conversational turns and conclude with a final diagnosis. To better approximate real clinical conversations, the generation process introduces variability through non-deterministic patient responses, overlapping symptom descriptions, and incomplete or ambiguous symptom reporting. Using this pipeline, we generated 1,101 synthetic consultations, providing a more diverse training resource compared with template-based dialogue construction. Table 1 summarizes the statistics of the original MDDial dataset and the synthetic dialogues used to construct MedAidDialog . Compared with the template-driven corpus, the synthetic dataset contains longer dialogues and richer conversational exchanges. ![Table 1: Statistics of the original MDDial dataset (MD) and the synthetic dialogues used to construct the MedAidDialog corpus. The synthetic dialogues contain more conversational turns and longer utterances, resulting in richer physician–patient interactions.]() [[TABLE_0]] 