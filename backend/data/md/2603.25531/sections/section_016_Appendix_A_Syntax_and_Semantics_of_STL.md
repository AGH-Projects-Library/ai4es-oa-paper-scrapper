## Appendix A Syntax and Semantics of STL

| (40) |  | φ \displaystyle\varphi | : := ⊤ ∣ x i w ( t ) ≥ 0 ∣ ¬ φ ∣ φ 1 ∧ φ 2 ∣ φ 1 𝒰 [ a , b ] φ 2 \displaystyle::=\top\mid x_{i}^{w}(t)\geq 0\mid\neg\varphi\mid\varphi_{1}\land\varphi_{2}\mid\varphi_{1}\mathcal{U}_{[a,b]}\varphi_{2} |  |
| --- | --- | --- | --- | --- |

|  | ( w , t ) ⊧ ⊤ ⇔ ⊤ is true \displaystyle(w,t)\models\top\iff\top\text{ is true} |  |
| --- | --- | --- |
|  | ( w , t ) ⊧ x i w ​ ( t ) ≥ 0 ⇔ x i w ​ ( t ) ≥ 0 \displaystyle(w,t)\models x_{i}^{w}(t)\geq 0\iff x_{i}^{w}(t)\geq 0 |  |
|  | ( w , t ) ⊧ ¬ φ ⇔ ( w , t ) ⊧̸ φ \displaystyle(w,t)\models\neg\varphi\iff(w,t)\not\models\varphi |  |
|  | ( w , t ) ⊧ φ 1 ∧ φ 2 ⇔ ( w , t ) ⊧ φ 1 ​ and ​ ( w , t ) ⊧ φ 2 \displaystyle(w,t)\models\varphi_{1}\land\varphi_{2}\iff(w,t)\models\varphi_{1}\text{ and }(w,t)\models\varphi_{2} |  |

|  | ( w , t ) ⊧ φ 1 ​ 𝒰 [ a , b ] ​ φ 2 ⇔ ∃ t 1 ∈ [ t + a , t + b ] : ( w , t 1 ) ⊧ φ 2 ​ and \displaystyle(w,t)\models\varphi_{1}\mathcal{U}_{[a,b]}\varphi_{2}\iff\exists t_{1}\in[t+a,t+b]:(w,t_{1})\models\varphi_{2}\text{ and } |  |
| --- | --- | --- |
|  | ∀ t 2 ∈ [ t , t 1 ) : ( w , t 2 ) ⊧ φ 1 \displaystyle\forall t_{2}\in[t,t_{1}):(w,t_{2})\models\varphi_{1} |  |

 (STL Trace) A STL trace w w is a function w : ℝ ≥ 0 → ℝ n w:\mathbb{R}_{\geq 0}\rightarrow\mathbb{R}^{n} that maps real-time to signal values. For a given trace w w and real-time t ∈ ℝ ≥ 0 t\in\mathbb{R}_{\geq 0} , x i w ​ ( t ) x^{w}_{i}(t) denotes the value of signal x i x_{i} at time t t in trace w w , for i = 1 , 2 , … , n i=1,2,\ldots,n . (STL Syntax) The syntax of STL formulas φ \varphi is defined as follows: [[TABLE_0]]  (STL Semantics) The semantics of STL formulas φ \varphi is defined as follows: [[TABLE_1]]  [[TABLE_2]] 