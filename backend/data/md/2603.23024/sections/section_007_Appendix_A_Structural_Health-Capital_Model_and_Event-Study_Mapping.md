## Appendix A: Structural Health-Capital Model and Event-Study Mapping

|  | H i , t + 1 = ( 1 − δ i , t ) ​ H i , t + ϕ t ​ ( g i ) ​ I i , t , H_{i,t+1}=(1-\delta_{i,t})\,H_{i,t}+\phi_{t}(g_{i})\,I_{i,t}, |  | (A1) |
| --- | --- | --- | --- |

|  | H i , t + 1 = [ 1 − δ i , t + γ 1 ​ n i , t ] ​ H i , t + ϕ t ​ ( g i ) ​ [ 1 + γ 2 ​ n i , t ] ​ I i , t , H_{i,t+1}=\bigl[1-\delta_{i,t}+\gamma_{1}n_{i,t}\bigr]H_{i,t}+\phi_{t}(g_{i})\bigl[1+\gamma_{2}n_{i,t}\bigr]I_{i,t}, |  | (A2) |
| --- | --- | --- | --- |

|  | h i , t + 1 = λ H ​ ( g i ) ​ h i , t + ξ ​ ( g i ) ​ n i , t + u i , t , h_{i,t+1}=\lambda_{H}(g_{i})\,h_{i,t}+\xi(g_{i})\,n_{i,t}+u_{i,t}, |  | (A3) |
| --- | --- | --- | --- |

|  | I i , t − I ¯ i = α H ​ h i , t + α N ​ n i , t + v i , t , I_{i,t}-\bar{I}_{i}=\alpha_{H}\,h_{i,t}+\alpha_{N}\,n_{i,t}+v_{i,t}, |  | (A4) |
| --- | --- | --- | --- |

|  | Y i , t ( m ) = α i ( m ) + λ t ( m ) + q m ​ h i , t + r m ​ n i , t + X i , t ′ ​ θ ( m ) + ε i , t ( m ) . Y^{(m)}_{i,t}=\alpha^{(m)}_{i}+\lambda^{(m)}_{t}+q_{m}\,h_{i,t}+r_{m}\,n_{i,t}+X^{\prime}_{i,t}\theta^{(m)}+\varepsilon^{(m)}_{i,t}. |  | (A5) |
| --- | --- | --- | --- |

|  | Y i , t ( E ​ R ) = α i ( E ​ R ) + λ t ( E ​ R ) + π 1 ​ h i , t − π 2 ​ n i , t + X i , t ′ ​ θ ( E ​ R ) + ε i , t ( E ​ R ) . Y^{(ER)}_{i,t}=\alpha^{(ER)}_{i}+\lambda^{(ER)}_{t}+\pi_{1}\,h_{i,t}-\pi_{2}\,n_{i,t}+X^{\prime}_{i,t}\theta^{(ER)}+\varepsilon^{(ER)}_{i,t}. |  | (A6) |
| --- | --- | --- | --- |

|  | h i , T i + k = ξ ​ ( g i ) ​ ∑ s = 0 k − 1 λ H ​ ( g i ) s = ξ ​ ( g i ) ​ 1 − λ H ​ ( g i ) k 1 − λ H ​ ( g i ) , k ≥ 0 , h_{i,T_{i}+k}=\xi(g_{i})\sum_{s=0}^{k-1}\lambda_{H}(g_{i})^{s}=\xi(g_{i})\,\frac{1-\lambda_{H}(g_{i})^{k}}{1-\lambda_{H}(g_{i})},\qquad k\geq 0, |  | (A7) |
| --- | --- | --- | --- |

|  | β k ( m ) = r m + q m ​ h i , T i + k , \beta^{(m)}_{k}=r_{m}+q_{m}\,h_{i,T_{i}+k}, |  | (A8) |
| --- | --- | --- | --- |

|  | β k ( E ​ R ) = ( − π 2 ) + π 1 ​ h i , T i + k . \beta^{(ER)}_{k}=(-\pi_{2})+\pi_{1}\,h_{i,T_{i}+k}. |  | (A9) |
| --- | --- | --- | --- |

 This appendix provides a concise link between a Grossman-style health-capital model and the event-study specification used in the paper. We show why an absorbing program like NPCP can generate dynamic effects on preventive investments (adherence, specialist visits, diagnostics) and potentially effects on ER use. Let H i , t H_{i,t} denote the health stock at the start of period t t . In the baseline, [[TABLE_0]]  where 0 < δ i , t < 1 0<\delta_{i,t}<1 is depreciation and I i , t I_{i,t} is a composite index of health investment (market inputs and patient effort). We model NPCP as an absorbing treatment n i , t ∈ { 0 , 1 } n_{i,t}\in\{0,1\} that can (i) reduce effective depreciation and (ii) raise input productivity: [[TABLE_1]]  with γ 1 > 0 \gamma_{1}>0 and γ 2 > 0 \gamma_{2}>0 . Let h i , t ≡ H i , t − H ¯ i h_{i,t}\equiv H_{i,t}-\bar{H}_{i} be the deviation from the no-program steady state. A first-order approximation of ( A2 ) around n i , t = 0 n_{i,t}=0 yields a stable linear law: [[TABLE_2]]  where | λ H ​ ( g i ) | < 1 |\lambda_{H}(g_{i})|<1 summarizes health persistence, ξ ​ ( g i ) \xi(g_{i}) is the composite shift in the health transition induced by NPCP, and u i , t u_{i,t} collects shocks/approximation error. Intuitively, ξ ​ ( g i ) \xi(g_{i}) bundles the “depreciation” channel ( γ 1 \gamma_{1} ) and the “productivity” channel ( γ 2 \gamma_{2} ), evaluated at baseline investment levels. The dynamic optimization problem (utility over consumption and health subject to the health law) implies diminishing returns to investment. Rather than carry the full solution, we use a reduced-form linearization consistent with the first-order condition: [[TABLE_3]]  where α H \alpha_{H} captures how investment responds to health and α N \alpha_{N} captures direct program effects on investment costs/productivity (e.g., lower informational/behavioral costs). Observable outcomes load on health and may also have a direct NPCP component. For an “investment” outcome Y ( m ) Y^{(m)} (adherence, visits, diagnostics), write: [[TABLE_4]]  For ER use, allow an ambiguous direct effect (e.g., monitoring/triage could increase precautionary ER visits even if health improves): [[TABLE_5]]  Let T i T_{i} be NPCP start time and define event time k = t − T i k=t-T_{i} . With absorbing treatment, n i , t = 1 ​ [ k ≥ 0 ] n_{i,t}=1[k\geq 0] . Under ( A3 ), normalizing h i , T i − 1 = 0 h_{i,T_{i}-1}=0 and ignoring shocks for intuition, the implied health path is [[TABLE_6]]  and h i , T i + k = 0 h_{i,T_{i}+k}=0 for k < 0 k<0 under no anticipation. Therefore, the event-study coefficient for an investment outcome satisfies, for k ≥ 0 k\geq 0 , [[TABLE_7]]  and for ER use, [[TABLE_8]]  This mapping implies dynamic effects that generally converge to a long-run impact (a new steady state) rather than mechanically widening over time. Lead coefficients ( k < 0 k<0 ) are predicted to be zero in the absence of anticipation/pre-trends.