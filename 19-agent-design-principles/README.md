# Agent Design Principles — A Connected-Agent Algorithm

## Introduction

The earlier lessons teach the *patterns* of building agents. This lesson goes one
level deeper to the *principles* underneath those patterns — the philosophical and
strategic ideas that each force a concrete build decision — and then shows how to
**wire all ten principles into a single network of connected agents** that runs as
one [OODA loop](#category-2--the-loop-and-the-goal).

The principles are ranked by **load-bearing-ness**: how directly the idea converts
into an actual design decision when you build an agent. The top ten each force a
concrete choice (a scoring rule, a loop, a memory split, a reward signal).

## Learning Goals

After completing this lesson you will be able to:

* Map ten design principles onto ten concrete agent roles.
* Connect those roles into one data-flow graph with a single control loop.
* Run a dependency-free reference implementation and read what each node did.
* Identify where an LLM-backed reasoner plugs into the network (System 2).

## The Ten Principles and Their Agent Roles

Each principle becomes one node. The "agent translation" is the build decision the
principle forces.

### Category 1 — The Rational Core (how the agent decides)

| Principle | Strategist | Agent role | Build decision it forces |
|---|---|---|---|
| Decision Theory / Expected Utility | Von Neumann, Savage | `DecisionTheoryAgent` | The scoring rule: pick the action with the best expected payoff. |
| Bounded Rationality | Herbert Simon | `BoundedRationalityAgent` | Budgets, early stopping, and *satisficing* ("good enough", not perfect). |
| Bayesian Epistemology | Bayes, Pearl | `BayesianBeliefAgent` | Beliefs as probabilities; revise on every observation. |

### Category 2 — The Loop and the Goal (how the agent operates)

| Principle | Strategist | Agent role | Build decision it forces |
|---|---|---|---|
| Cybernetics + OODA Loop | Wiener; Boyd | `OODAController` | The control skeleton: sense → decide → act → observe → correct → repeat. |
| Teleology / Means-Ends | Aristotle → STRIPS | `TeleologyPlanner` | Start from the goal, work backward to candidate actions (decomposition). |
| Belief–Desire–Intention | Bratman | `BDIState` | Split what the agent *knows*, *wants*, and has *committed to*. |

### Category 3 — Learning and Thinking (how it improves and reasons)

| Principle | Strategist | Agent role | Build decision it forces |
|---|---|---|---|
| Reinforcement Learning | Skinner; Sutton & Barto | `ReinforcementLearner` | Reward good outcomes; credit assignment tunes what the agent values. |
| Dual-Process (System 1/2) | Kahneman | `DualProcessRouter` | When to "think harder": fast reaction vs. deliberate reasoning. |
| Dialectic + Pragmatism | Hegel; Socrates; Peirce/Dewey | `DialecticCritic` | Generator-vs-critic: test an idea against its opposite, keep what works. |

### Category 4 — Strategy Among Others (multi-agent)

| Principle | Strategist | Agent role | Build decision it forces |
|---|---|---|---|
| Game Theory | Nash; Schelling | `GameTheoryAgent` | Best response when other agents act strategically; avoid collisions. |

## The Connected-Agent Algorithm

The nodes are connected into a directed data-flow graph. One full pass = one OODA
cycle.

```
                 ┌─────────────────────────── Environment ───────────────────────────┐
                 │ evidence/likelihoods                              realized reward   │
                 ▼                                                          ▲          │
       BayesianBeliefAgent ──beliefs──► BDIState ──goal+beliefs──► TeleologyPlanner    │
                 ▲                          │                              │           │
   loop back     │                          │ committed intention         │ candidate │
  (observe       │                          ▼                             actions      │
   outcome)      │                    OODAController ◄───────────┐         │           │
                 │                          │                    │         ▼           │
                 │                          │ action       best-response  DecisionTheory│
                 │                          ▼                    │     (Expected Utility)│
                 └────────────────────  Environment        GameTheoryAgent   │  ▲       │
                                                                 ▲            │  │ learned
                                            DialecticCritic ◄────┘            │  │ rewards
                                                 ▲   ▲                        │  │       │
                                  system2 escalate│   │budget/satisfice       │  │       │
                                   DualProcessRouter   BoundedRationalityAgent │  │       │
                                                 ▲___________________________ │  │       │
                                                        ranked actions + EU ◄──┘  │       │
                                                                ReinforcementLearner ◄────┘
```

### Pseudocode

```
repeat until budget exhausted or goal met:        # OODAController (Cybernetics/OODA)

    # 1. OBSERVE
    evidence    = environment.observe()
    beliefs     = BayesianBeliefAgent.update(evidence)        # Bayes / Pearl

    # 2. ORIENT / PLAN
    actions     = TeleologyPlanner.plan(desire, beliefs)      # Aristotle / STRIPS

    # 3. DECIDE
    ranked      = DecisionTheoryAgent.score(actions, beliefs) # Von Neumann / Savage
                                                              #  uses RL-learned rewards
    mode        = DualProcessRouter.route(beliefs, ranked)    # Kahneman: S1 vs S2
    charge budget (S2 costs more)                             # Simon: bounded rationality

    if mode == system2:
        chosen  = DialecticCritic.critique(ranked)            # Hegel/Socrates/Peirce
    else:
        chosen  = ranked[0]                                   # fast path

    chosen      = GameTheoryAgent.best_response(chosen, others)# Nash / Schelling
    BDIState.commit(chosen)                                    # Bratman: form intention

    # 4. ACT + 5. FEEDBACK
    outcome, reward = environment.act(chosen)
    ReinforcementLearner.update(outcome, reward)              # Skinner / Sutton&Barto
```

Why this ordering: beliefs must be current before you plan; planning produces the
menu Decision Theory scores; the router and budget decide *how much* deliberation
that scoring earns; the critic and game-theory node refine the pick before it
becomes a commitment; and the realized reward feeds learning so the next loop is
sharper. Separating belief / desire / intention (BDI) is what stops the agent from
re-deciding everything from scratch every step.

## Running the Reference Implementation

The implementation is pure standard library — no API key, no install.

```bash
cd code_samples
python connected_agents.py
```

It prints the connection graph, then runs a toy "cross the strait" task with a
hidden weather state. You will see the agent try the high-value `sail` action,
wreck in a storm, update its beliefs and learned values, and switch to the robust
`harbor` action — every node visibly doing its job.

### Plugging in an LLM (System 2)

`DialecticCritic` accepts a `reasoner` callable. The default is a deterministic
pragmatic rule so the demo runs offline. To make System 2 a real
generator-vs-critic debate, pass a function that calls your model of choice and
returns the name of the action it prefers:

```python
def llm_reasoner(phase, ranked):
    # call your LLM with the ranked candidates + their outcome models,
    # run a thesis/antithesis critique, return the chosen action's name.
    ...

controller = build_network(env, reasoner=llm_reasoner)
```

Only System 2 calls the model, so the cheap reactive path (System 1) stays fast —
exactly the Kahneman split the router is built to exploit.

## Deliberately Excluded Principles (and Why)

These shape or constrain the ten above rather than create a node:

* **Occam's Razor** — a simplicity prior baked *inside* many methods, not a
  standalone node.
* **Stoic dichotomy of control** (Epictetus) — a boundary heuristic for scoping the
  action space and guardrails, not a decision engine.
* **Deontology vs. Consequentialism** (Kant vs. Mill) — a *values layer* for
  safety/alignment that sits on top of the agent. Add it as a constraint filter
  before `BDIState.commit` if constraint enforcement is your priority.
* **Free Energy Principle / Active Inference** (Friston) — an elegant unifying
  theory (minimize prediction error), but still more neuroscience than standard
  deployed practice.

## How This Connects to the Rest of the Course

* **Lesson 03 (Design Patterns)** and **07 (Planning)** — `TeleologyPlanner` is the
  principled root of goal decomposition.
* **Lesson 08 (Multi-Agent)** — `GameTheoryAgent` is the principle behind
  coordination and negotiation between agents.
* **Lesson 09 (Metacognition)** — `DualProcessRouter` + `DialecticCritic` are the
  reflection / self-critique machinery.
* **Lesson 06 (Trustworthy Agents)** — the excluded *values layer* is where
  deontological guardrails belong.
```
