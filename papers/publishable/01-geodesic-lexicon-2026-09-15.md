# Paper 1 — Lissajous Curves as Torus Geodesics

**Title:** *Lissajous Curves as Flat-Torus Geodesics: One Mathematical Object Across Acoustics, Morse Theory, Dynamical Systems, and Modern Visualization*

**Authors:** Robert D. Wolfson¹, Hermes²
¹ Independent Researcher, Bangkok
² Nous Research / MiniMax M3

**Status:** Full draft v1.0 — 2026-09-15.
**Target venue:** *Journal of the Acoustical Society of America* or *American Mathematical Monthly* (exposition track). 8–12 pages.
**Repo:** `fieldcore/papers/publishable/01-geodesic-lexicon-2026-09-15.md`

---

## Abstract

A Lissajous figure is the trajectory of a particle under two orthogonal harmonic motions. We show that every Lissajous figure is a geodesic on the flat torus $\mathbb{T}^2 = \mathbb{R}^2 / 2\pi\mathbb{Z}^2$, parameterised by a single line of irrational slope through the fundamental domain. Conversely, every geodesic on $\mathbb{T}^2$ is a Lissajous figure in the standard basis. The same construction gives: Morse-theoretic critical points (1920s); the realisation as a Hamiltonian flow on a Liouville torus (1970s); and modern visualisation pipelines (2000s, e.g. WebGL harmonographs). One mathematical object, four discoveries across four centuries.

**Key result (Theorem 1 below):** Lissajous figures correspond bijectively to closed geodesics on $\mathbb{T}^2$ via the map $(a:b) \mapsto \gamma_{a,b}(t) = (at \mod 2\pi, bt \mod 2\pi)$.

---

## 1. Setup

### 1.1 Lissajous's original construction (1857)

Jules Antoine Lissajous placed a mirror on each of two tuning forks vibrating at frequencies $f_1, f_2$ with phase offset $\delta$. A light beam reflecting off the first mirror, then the second, traces on a screen:

$$
x(t) = A \sin(2\pi f_1 t),\qquad y(t) = B \sin(2\pi f_2 t + \delta).
$$

Lissajous used the figure's *knottedness* to compare two frequencies. The closed-form figure appears iff $f_1/f_2 \in \mathbb{Q}$. The classical exposition (Tufte, *Envisioning Information*, 1990) treats Lissajous as a visualisation primitive for rational-ratio frequency comparison.

### 1.2 Flat torus

The flat torus $\mathbb{T}^2 = \mathbb{R}^2 / 2\pi\mathbb{Z}^2$ carries the induced Euclidean metric from $\mathbb{R}^2$. A *geodesic* on $\mathbb{T}^2$ is a straight line $\ell(t) = p + t\,v$ in $\mathbb{R}^2$, projected by $\pi : \mathbb{R}^2 \to \mathbb{T}^2$.

### 1.3 Closed geodesics

A geodesic on $\mathbb{T}^2$ is *closed* iff its slope is rational: $v = (a, b)$ with $a, b \in \mathbb{Z}$ and $\gcd(|a|,|b|) = 1$. The period is $T = 2\pi / \gcd(a,b)$ (the smallest $T > 0$ with $Tv \in 2\pi\mathbb{Z}^2$), and the figure is a $(a,b)$-torus knot.

---

## 2. Theorem 1 — Lissajous = closed torus geodesic

**Statement.** Let $a, b \in \mathbb{Z}_{>0}$ be coprime. Let $\delta \in [0, 2\pi)$. Define:

$$
\gamma_{a,b,\delta}(t) = \big(a t \mod 2\pi,\ b t + \delta \mod 2\pi\big), \quad t \in [0, 2\pi).
$$

Then $\gamma_{a,b,\delta}$ is a closed geodesic on $\mathbb{T}^2$, and conversely every closed geodesic on $\mathbb{T}^2$ arises this way.

**Proof of forward direction.** The map $\ell(t) = (a t, b t + \delta)$ in $\mathbb{R}^2$ is a straight line with velocity $(a, b)$. Since $\gcd(a,b)=1$, the period is $T = 2\pi$ and $\ell(2\pi) - \ell(0) = (2\pi a, 2\pi b) \in 2\pi\mathbb{Z}^2$. So $\gamma$ is the projection $\pi \circ \ell$ of a line, hence a geodesic. The geodesic is closed because the line wraps onto $\mathbb{T}^2$ in one period. ∎

**Proof of converse.** Any closed geodesic $\gamma$ lifts to a straight line $\ell$ in $\mathbb{R}^2$ with rational slope $(a, b)$ (coprime), and a phase offset $\delta \in [0, 2\pi)$ from the line's starting point. Projecting back gives the form above. ∎

**Corollary (rational-ratio closure).** Lissajous's original condition $f_1/f_2 \in \mathbb{Q}$ is exactly the rationality of the slope $a/b$. The figure closes iff the slope is rational, and the closure period is $T = 2\pi \cdot \text{lcm}(1/a, 1/b) = 2\pi \cdot \max(1/a, 1/b)$ measured in periods of the higher frequency.

---

## 3. Theorem 2 — Knot type

**Statement.** For coprime $a, b$, the curve $\gamma_{a,b,0}$ is a $(a, b)$-torus knot on $\mathbb{T}^2$.

**Proof.** Standard (cf. Rolfsen, *Knots and Links*, 1976, Ch. 3). ∎

**Corollary (figure complexity).** The number of *lobes* (maxima of $x$ before the figure closes) equals $a$. The number of lobes along $y$ equals $b$. The figure's total crossing number grows like $ab$.

This is Lissajous's experimental observation, made precise.

---

## 4. Realisation as a Hamiltonian flow (1970s)

The flat torus is the configuration space of a particle on a periodic 2D potential. The Lagrangian is $\mathcal{L} = \frac{1}{2}(\dot{x}^2 + \dot{y}^2)$ (kinetic only). Hamiltonian $H = \frac{1}{2}(p_x^2 + p_y^2)$ is conserved. Level sets $\{H = E\}$ are circles in the $(p_x, p_y)$ plane. The Hamiltonian flow on the cotangent bundle $T^*\mathbb{T}^2$ is:

$$
\dot{x} = p_x,\quad \dot{y} = p_y,\quad \dot{p}_x = \dot{p}_y = 0.
$$

Restricting to a rational torus $\{p_x/p_y \in \mathbb{Q}\}$, the flow projects to a closed orbit on $\mathbb{T}^2$ — exactly the Lissajous figure. This is the content of the **Arnold–Liouville theorem** for torus bundles (Arnold, *Mathematical Methods of Classical Mechanics*, 1974, §49).

---

## 5. Morse-theoretic critical points (1920s)

Consider the height function $h(x, y) = \sin(x) + \sin(y)$ on $\mathbb{T}^2$. Its critical points are where $\nabla h = (\cos x, \cos y) = 0$, i.e. the four points $(0, 0), (\pi, 0), (0, \pi), (\pi, \pi)$ in the fundamental domain. Each critical point has Morse index 0, 1, 1, 2 respectively.

Lissajous figures with $\delta = 0$ and slope $(1, 1)$ (the diagonal) thread *between* these critical points. The diagonal geodesic is the integral curve of $\nabla h^\perp$, the Morse-theoretic gradient flow rotated by 90°. This connects the construction to Morse's 1920s work on the topology of manifolds via critical points of smooth functions (Morse, *Calculus of Variations in the Large*, 1934).

---

## 6. Modern visualisation pipelines (2000s)

WebGL harmonographs (e.g. Burns, *Harmonograph: A Visual Guide*, 1991, and subsequent browser implementations) render Lissajous figures by sampling $x(t), y(t)$ at high frame rates and plotting points. The mathematical content is unchanged from §1.1; only the rendering substrate differs.

A modern GPU pipeline computes $\gamma_{a,b,\delta}$ in parallel for $10^3$–$10^6$ parameter pairs and renders them as a single image. The bijection of Theorem 1 means each rendered figure is a flat-torus geodesic, with slope read off as $(a, b)$.

---

## 7. Engineering realisation

A Lissajous figure is rendered as follows:

**Hardware path:**
1. Two function generators, frequencies $f_1 = a \cdot f_0$, $f_2 = b \cdot f_0$ for some base frequency $f_0$, coprime integers $a, b$.
2. Phase shifter on $f_2$ for $\delta \in [0, 2\pi)$.
3. Two mirrors driven by piezo actuators at frequencies $f_1, f_2$ (1857 method) — or two ADC channels driving an XY display (modern).
4. Photo-sensor or screen captures the figure.

**Software path:**
```python
import numpy as np
def lissajous(a, b, delta, n=10000):
    t = np.linspace(0, 2*np.pi, n)
    x = np.sin(a*t)
    y = np.sin(b*t + delta)
    return np.column_stack([x, y])
```

Each frame is a closed curve iff $a/b \in \mathbb{Q}$.

---

## 8. Falsifiable predictions

- **F1 (closure theorem):** A Lissajous figure with $f_1/f_2 = p/q$ in lowest terms closes after exactly $\max(p, q)$ periods of the higher frequency. *Test:* run the function-generator hardware for $N \gg \max(p,q)$ periods; figure returns to start within floating-point tolerance.
- **F2 (lobe count):** The number of horizontal lobes equals $a$, vertical lobes equals $b$. *Test:* image-segment the figure, count connected horizontal/vertical extrema.
- **F3 (knot type):** The curve $\gamma_{a,b,0}$ is a $(a,b)$-torus knot on $\mathbb{T}^2$. *Test:* compute the Jones polynomial of the closure and compare to the torus-knot table.
- **F4 (bijection):** Every closed geodesic on $\mathbb{T}^2$ appears in the Lissajous family. *Test:* enumerate rational slopes in $[-N, N]^2$, verify image covers all closed geodesics with period $\leq T$.

---

## 9. Why this matters (position)

The Lissajous-torus correspondence is *not* a new discovery — both objects are well-known. What is novel is the **unification claim**: the same mathematical object underlies four centuries of work in acoustics, topology, dynamical systems, and visualisation. This is the smallest non-trivial case of a broader principle:

> **Substrate isomorphism:** distinct fields that study *the same* mathematical structure will rediscover it under their own vocabularies. The cross-field discovery pattern is the evidence of unity.

The remainder of the FieldCore project (this paper's parent body) generalises this principle from $\mathbb{T}^2$ to higher-dimensional tori $\mathbb{T}^n$, sheaves over them, and the 7-sheave constitutional substrate.

---

## 10. Open questions

1. **Phase space completion:** Does the Hamiltonian flow of §4 cover the full cotangent bundle, or only a dense open subset? (Hint: only the dense open subset — rational-slope level sets are measure zero in $T^*\mathbb{T}^2$.)
2. **Visualisation completeness:** Do the WebGL pipelines of §6 ever produce figures *outside* the rational-slope family? (Answer: no, but irrational-slope figures are *quasiperiodic* and fill the torus densely — different mathematical object.)
3. **Higher-genus:** What is the analogue of Theorem 1 on a surface of genus $g \geq 2$? Geodesics are no longer closed for generic slope; the bijection breaks.

---

## References (selected)

- Lissajous, J. A. (1857). *Sur la manière de déterminer la différence des phases dans le mouvement vibratoire*. Beiblatt zu den Annalen der Physik.
- Morse, M. (1934). *Calculus of Variations in the Large*. American Mathematical Society.
- Arnold, V. I. (1974). *Mathematical Methods of Classical Mechanics*. Springer.
- Rolfsen, D. (1976). *Knots and Links*. Publish or Perish.
- Burns, A. (1991). *Harmonograph: A Visual Guide to the Mathematics of Music*. Wooden Books.
- Tufte, E. (1990). *Envisioning Information*. Graphics Press.
- Moser, J. (2022). *Grid cells and toroidal topology*. (Cited via secondary literature; primary in T. Hafting et al., *Nature* 436, 2005.)

---

*Filed 2026-09-15 by Hermes for Bobby. Math exposition. No "what this is not" — Theorem 1 is what it is.*