## D.3 Translation Prompt

| Prompt Type | Prompt Content |
| --- | --- |
| Translation Prompt | You are acting as a specialized Medical Translation Bridge, a critical link between an English-speaking doctor and a patient who speaks Hindi, Bengali, Marathi, Telugu, Arabic, or Tamil. Your primary responsibility is to maintain absolute clinical accuracy while ensuring the tone is appropriately synced for both parties. When the doctor speaks in English, you must translate their advice, diagnoses, and prescriptions into the patient’s native language using clear, empathetic, and culturally respectful terminology that a non-medical person can easily understand. Conversely, when the patient provides a query or describes symptoms in their native language, you will convert that input into precise, formal medical English for the doctor, ensuring that nuances of pain, duration, and history are preserved without loss of detail. You are strictly prohibited from hallucinating or adding medical advice not present in the source text; your role is purely to facilitate a perfectly synced, bidirectional exchange. Ensure that if the patient expresses distress or urgency, the English translation reflects that clinical priority to the doctor. Your output must contain only the translated text to allow for seamless integration into the communication interface. |

| Prompt Type | Prompt Content |
| --- | --- |
| Synthetic Dialogue Generation Prompt | Analyze train.json medical dialogues (patient/doctor exchanges, symptoms like “Cough”, diagnoses such as “Esophagitis”). Create Python synthetic generator using Groq API (Llama-3 family model). Match exact format: {’Dialog N’: [{’patient’: ’...’, ’doctor’: ’...’}]} . Randomize symptom openings, generate 4–8 turns with doctor questions and realistic patient responses. Preserve the overall structure used for model training and provide progress, ETA, and resume-friendly execution. Output synthetic data in the same format as train.json . |

| Prompt Type | Prompt Content |
| --- | --- |
| Dialogue Formatting Prompt | Convert a medical dialogue sample into ShareGPT-style multi-turn conversation. Structure: (1) the system message sets the medical diagnosis context, (2) patient utterances become human turns, (3) doctor utterances become gpt turns, and (4) the final gpt turn contains the diagnosis answer. Preserve dialogue order and ensure that each consultation remains a valid multi-turn interaction for instruction tuning. |

| Evaluation Criterion | Description |
| --- | --- |
| Medical Safety (Pass/Fail) | Whether the system provides any potentially dangerous, misleading, or unsafe medical advice during the conversation. |
| Symptom Extraction (1–5) | Measures how accurately the model identifies and tracks the patient’s symptoms throughout the dialogue. |
| Context Memory (1–5) | Evaluates whether the model remembers previously mentioned information such as symptoms or earlier responses in the conversation. |
| Diagnostic Correctness (1–5) | Assesses whether the final diagnosis is medically reasonable given the symptoms described in the conversation. |
| Conversational Flow (1–5) | Evaluates whether the dialogue is natural, coherent, empathetic, and professionally phrased, similar to a real clinical interaction. |
| Efficiency (1–5) | Measures whether the system asks an appropriate number of questions, avoiding unnecessary or redundant queries while still gathering sufficient information. |
| Annotator Notes | Free-text comments provided by medical experts to highlight issues such as reasoning errors, repeated questions, unsafe advice, or unusual dialogue patterns. |

 Table 10 shows the prompt used for bidirectional multilingual medical translation. ![Table 10: Prompt used for bidirectional medical translation in the multilingual inference layer.]() [[TABLE_0]]  ![Table 11: Prompt used to generate synthetic multi-turn medical consultations from the MDDial training distribution.]() [[TABLE_1]]  ![Table 12: Prompt used to convert raw medical dialogues into ShareGPT-style training instances.]() [[TABLE_2]]  ![Table 13: Evaluation criteria used in expert assessment of the conversational medical system. Experts rated multiple aspects of safety, reasoning, and dialogue quality using a Likert scale (1–5), while medical safety was evaluated using a binary pass/fail metric.]() [[TABLE_3]] 