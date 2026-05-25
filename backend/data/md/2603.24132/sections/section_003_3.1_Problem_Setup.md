## 3.1 Problem Setup

|  | C t = { u 1 , u 2 , … , u t − 1 } C_{t}=\{u_{1},u_{2},...,u_{t-1}\} |  | (1) |
| --- | --- | --- | --- |

|  | u t = arg ⁡ max u ⁡ P ​ ( u ∣ C t ) u_{t}=\arg\max_{u}P(u\mid C_{t}) |  | (2) |
| --- | --- | --- | --- |

 A medical consultation dialogue is represented as a sequence of conversational turns between a patient and a doctor D = { u 1 , u 2 , … , u T } D=\{u_{1},u_{2},...,u_{T}\} , where u t u_{t} denotes the utterance at turn t t , and T T is the total number of dialogue turns. In our setting, odd turns correspond to patient utterances and even turns correspond to doctor responses. Each dialogue is associated with a diagnostic label y y drawn from a disease set y ∈ 𝒴 y\in\mathcal{Y} , where 𝒴 \mathcal{Y} denotes the set of possible diseases considered in the dataset. Given a dialogue context consisting of the previous turns: [[TABLE_0]]  The objective of the model is to generate the next doctor response: [[TABLE_1]]  The conversation continues until sufficient information has been collected and a diagnostic recommendation is produced.