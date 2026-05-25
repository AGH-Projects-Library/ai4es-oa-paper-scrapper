## 4.1. Linear Temporal Logic (LTL) with predicates

| (14) |  | ϕ \displaystyle\phi | : := ⊤ ∣ P ∣ ¬ ϕ ∣ ϕ 1 ∧ ϕ 2 ∣ ϕ 1 ∨ ϕ 2 ∣ ○ ϕ ∣ ϕ 1 𝒰 ϕ 2 \displaystyle::=\top\mid P\mid\neg\phi\mid\phi_{1}\land\phi_{2}\mid\phi_{1}\lor\phi_{2}\mid\bigcirc\phi\mid\phi_{1}\mathcal{U}\phi_{2} |  |
| --- | --- | --- | --- | --- |
| (15) |  | P \displaystyle P | : := a 1 y 1 + a 2 y 2 + … + a n y n ⋈ b \displaystyle::=a_{1}y_{1}+a_{2}y_{2}+\ldots+a_{n}y_{n}\bowtie b |  |

| (16) |  | ◇ ​ ϕ \displaystyle\Diamond\phi | := ⊤ 𝒰 ​ ϕ \displaystyle:=\top\mathcal{U}\phi |  |
| --- | --- | --- | --- | --- |
| (17) |  | □ ​ ϕ \displaystyle\Box\phi | := ¬ ◇ ​ ¬ ϕ \displaystyle:=\neg\Diamond\neg\phi |  |

| (18) |  | ( σ , j ) ⊧ P \displaystyle(\sigma,j)\models P | ⇔ a 1 ​ s j ​ ( y 1 ) + a 2 ​ s j ​ ( y 2 ) + … + a n ​ s j ​ ( y n ) ⋈ b \displaystyle\iff a_{1}s_{j}(y_{1})+a_{2}s_{j}(y_{2})+\ldots+a_{n}s_{j}(y_{n})\bowtie b |  |
| --- | --- | --- | --- | --- |
| (19) |  | ( σ , j ) ⊧ ¬ ϕ \displaystyle(\sigma,j)\models\neg\phi | ⇔ ( σ , j ) ⊧̸ ϕ \displaystyle\iff(\sigma,j)\not\models\phi |  |
| (20) |  | ( σ , j ) ⊧ ϕ 1 ∧ ϕ 2 \displaystyle(\sigma,j)\models\phi_{1}\land\phi_{2} | ⇔ ( σ , j ) ⊧ ϕ 1 ​ and ​ ( σ , j ) ⊧ ϕ 2 \displaystyle\iff(\sigma,j)\models\phi_{1}\text{ and }(\sigma,j)\models\phi_{2} |  |

| (22) |  | ( σ , j ) ⊧ ϕ 1 ∨ ϕ 2 \displaystyle(\sigma,j)\models\phi_{1}\lor\phi_{2} | ⇔ ( σ , j ) ⊧ ϕ 1 ​ or ​ ( σ , j ) ⊧ ϕ 2 \displaystyle\iff(\sigma,j)\models\phi_{1}\text{ or }(\sigma,j)\models\phi_{2} |  |
| --- | --- | --- | --- | --- |
| (23) |  | ( σ , j ) ⊧ ○ ϕ \displaystyle(\sigma,j)\models\bigcirc\phi | ⇔ ( σ , j + 1 ) ⊧ ϕ \displaystyle\iff(\sigma,j+1)\models\phi |  |
| (24) |  | ( σ , j ) ⊧ ϕ 1 ​ 𝒰 ​ ϕ 2 \displaystyle(\sigma,j)\models\phi_{1}\mathcal{U}\phi_{2} | ⇔ ∃ k ≥ j ​ such that ​ ( σ , k ) ⊧ ϕ 2 \displaystyle\iff\exists k\geq j\text{ such that }(\sigma,k)\models\phi_{2} |  |
| (25) |  |  | and ​ ∀ l ∈ [ j , k ) , σ , l ⊧ ϕ 1 \displaystyle\quad\text{ and }\forall l\in[j,k),\sigma,l\models\phi_{1} |  |
| (26) |  | ( σ , j ) ⊧ □ ​ ϕ \displaystyle(\sigma,j)\models\Box\phi | ⇔ ∀ k ≥ j , ( σ , k ) ⊧ ϕ \displaystyle\iff\forall k\geq j,(\sigma,k)\models\phi |  |
| (27) |  | ( σ , j ) ⊧ ◇ ​ ϕ \displaystyle(\sigma,j)\models\Diamond\phi | ⇔ ∃ k ≥ j , ( σ , k ) ⊧ ϕ \displaystyle\iff\exists k\geq j,(\sigma,k)\models\phi |  |

|  | ϕ := 2 ​ y 1 − y 2 ≥ 10 \phi:=2y_{1}-y_{2}\geq 10 |  |
| --- | --- | --- |

|  | 2 ⋅ s 5 ​ ( y 1 ) − s 5 ​ ( y 2 ) = 2 ⋅ 15 − 18 = 30 − 18 = 12 2\cdot s_{5}(y_{1})-s_{5}(y_{2})=2\cdot 15-18=30-18=12 |  |
| --- | --- | --- |

 To translate Synchronous Signal Temporal Logic formulae to a form suitable for model checking, we use Linear Temporal Logic (LTL) with predicates (LTL P ), taking inspiration from the work presented in (Kwon and Agha, 2008 ) , which extends traditional LTL by integrating predicates defined over real-valued variables. The LTL P logic allows us to express temporal properties while maintaining predicates over continuous or discrete-valued signals. (LTL P Syntax) The syntax of LTL P formulas ϕ \phi is defined as follows: [[TABLE_0]]  where P : ℝ n → 𝔹 P:\mathbb{R}^{n}\rightarrow\mathbb{B} is a predicate symbol representing a relational condition over variables y 1 , y 2 , … , y n y_{1},y_{2},\ldots,y_{n} . Specifically, P P takes the form a 1 ​ y 1 + a 2 ​ y 2 + … + a n ​ y n ⋈ b a_{1}y_{1}+a_{2}y_{2}+\ldots+a_{n}y_{n}\bowtie b , where a 1 , … , a n a_{1},\ldots,a_{n} are real-valued coefficients, b b is an offset, and ⋈ \bowtie is a relational operator chosen from { < , ≤ , = , ≥ , > } \{<,\leq,=,\geq,>\} . The temporal operators are: - • ○ ϕ \bigcirc\phi (next): ϕ \phi holds in the next state ○ ϕ \bigcirc\phi (next): ϕ \phi holds in the next state - • ϕ 1 ​ 𝒰 ​ ϕ 2 \phi_{1}\mathcal{U}\phi_{2} (until): ϕ 1 \phi_{1} holds until ϕ 2 \phi_{2} becomes true ϕ 1 ​ 𝒰 ​ ϕ 2 \phi_{1}\mathcal{U}\phi_{2} (until): ϕ 1 \phi_{1} holds until ϕ 2 \phi_{2} becomes true The operators □ \Box and ◇ \Diamond can be defined as syntactic abbreviations: [[TABLE_1]]  (LTL P Semantics): An LTL P trace σ \sigma is an infinite sequence of states, where each state s j , ∀ j ∈ ℕ ≥ 0 s_{j},\forall j\in\mathbb{N}_{\geq 0} assigns values to variables y 1 , … , y n y_{1},\ldots,y_{n} . For a state s j s_{j} , we write s j ​ ( y 1 ) , … , s j ​ ( y n ) s_{j}(y_{1}),\ldots,s_{j}(y_{n}) to denote the values of variables y 1 , y 2 , … , y n y_{1},y_{2},\ldots,y_{n} in state s i s_{i} . The satisfaction relation ( σ , j ) ⊧ ϕ (\sigma,j)\models\phi (read as “ σ \sigma satisfies ϕ \phi at position j j ”) is defined recursively as follows: [[TABLE_2]]  [[TABLE_3]]  We say that a sequence σ \sigma satisfies an LTL P formula ϕ \phi (denoted σ ⊧ ϕ \sigma\models\phi ) if σ , 0 ⊧ ϕ \sigma,0\models\phi . Consider the following LTL P formula involving two variables y 1 y_{1} and y 2 y_{2} (where y 1 y_{1} is temperature x x in Celsius and y 2 y_{2} is voltage v v in volts): [[TABLE_4]]  That is, ϕ \phi is true in a state if 2 2 times the temperature minus the voltage is at least 10 10 . Now, suppose we have an LTL P trace σ = s 0 , s 1 , s 2 , … \sigma=s_{0},s_{1},s_{2},\ldots where each state assigns values to these variables. Take as an example the state s 5 s_{5} with s 5 ​ ( y 1 ) = 15 s_{5}(y_{1})=15 and s 5 ​ ( y 2 ) = 18 s_{5}(y_{2})=18 . Substituting these values into the formula, we have: [[TABLE_5]]  Since 12 ≥ 10 12\geq 10 , the formula ϕ \phi holds at state s 5 s_{5} , i.e., ( σ , 5 ) ⊧ ϕ (\sigma,5)\models\phi .