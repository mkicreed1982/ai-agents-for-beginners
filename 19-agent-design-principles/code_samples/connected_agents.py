"""
Connected Agents — a reference implementation of the 10 agent-design principles.

This module turns the *philosophy* of agent design into a *runnable* network of
connected agents. Each of the four categories from the lesson maps to concrete
nodes, and the nodes are wired into a single OODA loop:

    Category 1 — The Rational Core (how the agent decides)
        * DecisionTheoryAgent      (Von Neumann, Savage)   — expected utility
        * BoundedRationalityAgent  (Herbert Simon)         — budgets / satisficing
        * BayesianBeliefAgent      (Bayes, Pearl)          — beliefs as probabilities

    Category 2 — The Loop and the Goal (how the agent operates)
        * OODAController           (Wiener; Boyd)          — sense->decide->act->observe
        * TeleologyPlanner         (Aristotle; STRIPS)     — goal -> backward decomposition
        * BDIState                 (Bratman)               — belief / desire / intention

    Category 3 — Learning and Thinking (how it improves and reasons)
        * ReinforcementLearner     (Skinner; Sutton&Barto) — reward -> action values
        * DualProcessRouter        (Kahneman)              — System 1 vs System 2
        * DialecticCritic          (Hegel; Socrates; Peirce)— generator vs critic

    Category 4 — Strategy Among Others (multi-agent)
        * GameTheoryAgent          (Nash; Schelling)       — best response to others

The implementation is intentionally dependency-free (pure standard library) so it
runs anywhere. The "reasoning" used by System 2 is behind a pluggable `reasoner`
callable; the default is a deterministic stub so the demo runs with no API key. In
a real build you would pass an LLM-backed reasoner there.

Run it:  python connected_agents.py
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Shared data structures
# ---------------------------------------------------------------------------

@dataclass
class Action:
    """A candidate action the agent can take.

    `outcomes` maps a world-hypothesis -> {outcome_label: probability}. This lets
    Decision Theory compute an *expected* utility that depends on what the agent
    currently believes about the hidden state of the world.
    """
    name: str
    outcomes: Dict[str, Dict[str, float]]
    score: float = 0.0  # filled in by DecisionTheoryAgent


@dataclass
class Decision:
    """The committed result of one orient->decide pass."""
    action: Action
    mode: str                 # "system1" or "system2"
    expected_utility: float
    critique: str
    revised: bool


# ---------------------------------------------------------------------------
# Category 1 — The Rational Core
# ---------------------------------------------------------------------------

class BayesianBeliefAgent:
    """Bayesian Epistemology (Bayes, Pearl).

    Holds beliefs as a probability distribution over hypotheses about the hidden
    state of the world, and revises them with each observation via Bayes' rule:

        P(H | e)  proportional to  P(e | H) * P(H)
    """

    def __init__(self, priors: Dict[str, float]):
        total = sum(priors.values())
        self.beliefs: Dict[str, float] = {h: p / total for h, p in priors.items()}

    def update(self, likelihoods: Dict[str, float]) -> Dict[str, float]:
        """`likelihoods` = P(evidence | H) for each hypothesis H."""
        posterior = {h: self.beliefs[h] * likelihoods.get(h, 1e-9) for h in self.beliefs}
        z = sum(posterior.values()) or 1e-12
        self.beliefs = {h: p / z for h, p in posterior.items()}
        return self.beliefs

    def most_likely(self) -> str:
        return max(self.beliefs, key=self.beliefs.get)


class DecisionTheoryAgent:
    """Decision Theory / Expected Utility (Von Neumann, Savage).

    The literal textbook definition of an agent: pick the action with the best
    expected payoff. Expected utility for an action is the belief-weighted average
    of the reward of each possible outcome.
    """

    def __init__(self, reward_fn: Callable[[str], float]):
        self.reward_fn = reward_fn  # outcome_label -> scalar reward (supplied by RL)

    def score(self, actions: List[Action], beliefs: Dict[str, float]) -> List[Action]:
        for a in actions:
            eu = 0.0
            for hypothesis, p_h in beliefs.items():
                dist = a.outcomes.get(hypothesis, {})
                eu += p_h * sum(p_o * self.reward_fn(o) for o, p_o in dist.items())
            a.score = eu
        return sorted(actions, key=lambda a: a.score, reverse=True)


class BoundedRationalityAgent:
    """Bounded Rationality (Herbert Simon).

    No infinite time or compute, so aim for "good enough" not "perfect". Owns the
    compute budget and the satisficing rule (stop at the first option that clears
    an aspiration level instead of exhaustively optimizing).
    """

    def __init__(self, budget: int, aspiration: float):
        self.budget = budget
        self.aspiration = aspiration
        self.spent = 0

    def charge(self, cost: int = 1) -> None:
        self.spent += cost

    def exhausted(self) -> bool:
        return self.spent >= self.budget

    def satisfice(self, ranked: List[Action]) -> Tuple[Action, bool]:
        """Return the first action that clears the aspiration level.

        Returns (chosen_action, optimized) where `optimized` is True only if we
        had to fall back to the global best because nothing satisfied.
        """
        for a in ranked:
            if a.score >= self.aspiration:
                return a, False
        return ranked[0], True  # nothing good enough -> take the best available


# ---------------------------------------------------------------------------
# Category 3 — Learning and Thinking
# ---------------------------------------------------------------------------

class ReinforcementLearner:
    """Reinforcement Learning / Behaviorism (Skinner; Sutton & Barto).

    Learns the value of outcomes by trial and error and does credit assignment via
    an incremental running average (a one-state Q update):

        Q(o) <- Q(o) + alpha * (reward - Q(o))

    Decision Theory queries this as its `reward_fn`, so what the agent *values*
    improves as it acts.
    """

    def __init__(self, initial: Dict[str, float], alpha: float = 0.3):
        self.q: Dict[str, float] = dict(initial)
        self.alpha = alpha

    def value(self, outcome: str) -> float:
        return self.q.get(outcome, 0.0)

    def update(self, outcome: str, reward: float) -> None:
        old = self.q.get(outcome, 0.0)
        self.q[outcome] = old + self.alpha * (reward - old)


class DualProcessRouter:
    """Dual-Process Thinking, System 1 / System 2 (Kahneman).

    Decides when to "think harder". Cheap, confident, low-stakes decisions go to
    System 1 (just take the top-ranked action). Novel, uncertain, or high-stakes
    decisions are escalated to System 2 (deliberate critique + reasoning).
    """

    def __init__(self, uncertainty_threshold: float = 0.65, stakes_threshold: float = 1.5):
        self.uncertainty_threshold = uncertainty_threshold
        self.stakes_threshold = stakes_threshold

    @staticmethod
    def _entropy(beliefs: Dict[str, float]) -> float:
        return -sum(p * math.log(p + 1e-12) for p in beliefs.values())

    def route(self, beliefs: Dict[str, float], ranked: List[Action]) -> str:
        # Normalised entropy: how unsure are we about the world?
        max_entropy = math.log(len(beliefs)) or 1.0
        uncertainty = self._entropy(beliefs) / max_entropy
        # Stakes: how close are the top two options? A near-tie is worth deliberating.
        gap = ranked[0].score - (ranked[1].score if len(ranked) > 1 else ranked[0].score)
        high_stakes = abs(ranked[0].score) >= self.stakes_threshold and gap < 0.5
        if uncertainty >= self.uncertainty_threshold or high_stakes:
            return "system2"
        return "system1"


class DialecticCritic:
    """Dialectic + Pragmatism (Hegel; Socrates; Peirce/Dewey).

    The generator-vs-critic engine. Given a proposed action (thesis), it argues the
    strongest objection (antithesis) and either keeps it or revises (synthesis).
    The `reasoner` hook is where an LLM debate / self-critique would plug in; the
    default stub uses a pragmatic rule: if a rival action is within `margin`, switch
    to it when it is more robust across hypotheses (lower variance of outcomes).
    """

    def __init__(self, reasoner: Optional[Callable[[str, List[Action]], Optional[str]]] = None,
                 margin: float = 0.4):
        self.reasoner = reasoner
        self.margin = margin

    @staticmethod
    def _robustness(a: Action) -> float:
        """Higher is better: penalize actions whose payoff swings wildly by hypothesis."""
        per_h = []
        for dist in a.outcomes.values():
            per_h.append(sum(dist.values()))  # mass present per hypothesis
        if not per_h:
            return 0.0
        mean = sum(per_h) / len(per_h)
        var = sum((x - mean) ** 2 for x in per_h) / len(per_h)
        return -var

    def critique(self, ranked: List[Action]) -> Tuple[Action, str, bool]:
        thesis = ranked[0]
        if len(ranked) < 2:
            return thesis, "No rival to challenge; accepting thesis.", False
        antithesis = ranked[1]
        # Optional LLM-style reasoning hook (System 2 deliberation).
        if self.reasoner is not None:
            choice = self.reasoner("critique", ranked)
            if choice and choice != thesis.name:
                rev = next((a for a in ranked if a.name == choice), thesis)
                return rev, f"Reasoner preferred '{rev.name}' over '{thesis.name}'.", True
        # Pragmatic default: if the rival is close in EU but clearly more robust, switch.
        close = (thesis.score - antithesis.score) <= self.margin
        if close and self._robustness(antithesis) > self._robustness(thesis):
            return (antithesis,
                    f"Synthesis: '{antithesis.name}' is nearly as valuable but more robust "
                    f"across hypotheses than '{thesis.name}'.", True)
        return thesis, f"Thesis '{thesis.name}' survived critique.", False


# ---------------------------------------------------------------------------
# Category 4 — Strategy Among Others
# ---------------------------------------------------------------------------

class GameTheoryAgent:
    """Game Theory (Nash; Schelling).

    When other agents act strategically, the best move depends on theirs. This node
    adjusts the chosen action toward a best response: if a competitor is expected to
    take an action that collides with ours, fall back to a Schelling-style focal
    alternative to avoid a costly clash.
    """

    def __init__(self, collision_penalty: float = 1.0):
        self.collision_penalty = collision_penalty

    def best_response(self, chosen: Action, ranked: List[Action],
                      competitor_action: Optional[str]) -> Tuple[Action, str]:
        if competitor_action is None or competitor_action != chosen.name:
            return chosen, "No collision with other agents."
        # Collision: our top pick clashes with a competitor. Take the best
        # non-colliding alternative (a focal point both can settle on).
        for a in ranked:
            if a.name != competitor_action:
                return a, (f"Avoided collision on '{competitor_action}'; "
                           f"best-responded with focal action '{a.name}'.")
        return chosen, "Collision unavoidable; holding position."


# ---------------------------------------------------------------------------
# Category 2 — The Loop and the Goal
# ---------------------------------------------------------------------------

@dataclass
class BDIState:
    """Belief-Desire-Intention (Bratman).

    Keeps three things separate so the agent does not re-decide everything every
    step: what it *knows* (belief, owned by the Bayesian agent), what it *wants*
    (desire = the goal), and what it has *committed to* (intention = active plan).
    """
    desire: str
    belief_agent: BayesianBeliefAgent
    intention: Optional[Decision] = None
    history: List[Decision] = field(default_factory=list)

    def commit(self, decision: Decision) -> None:
        self.intention = decision
        self.history.append(decision)


class TeleologyPlanner:
    """Teleology / Means-Ends Reasoning (Aristotle -> STRIPS).

    Start from the goal and work backward to the candidate actions that could
    achieve it, given current beliefs. Here it returns the menu of feasible actions
    for the decision core to score (goal decomposition / action generation).
    """

    def __init__(self, action_library: Callable[[str, Dict[str, float]], List[Action]]):
        self.action_library = action_library

    def plan(self, goal: str, beliefs: Dict[str, float]) -> List[Action]:
        return self.action_library(goal, beliefs)


class OODAController:
    """Cybernetics + OODA Loop (Wiener; Boyd).

    The skeleton that ties every other node together:
        Observe -> Orient(plan) -> Decide -> Act -> (feedback) -> repeat.
    Each pass produces a committed intention and feeds the outcome back into the
    belief and reward models so the next loop is better informed.
    """

    def __init__(self,
                 bdi: BDIState,
                 planner: TeleologyPlanner,
                 decision_theory: DecisionTheoryAgent,
                 bounded: BoundedRationalityAgent,
                 router: DualProcessRouter,
                 critic: DialecticCritic,
                 game: GameTheoryAgent,
                 learner: ReinforcementLearner,
                 environment: "Environment"):
        self.bdi = bdi
        self.planner = planner
        self.decision_theory = decision_theory
        self.bounded = bounded
        self.router = router
        self.critic = critic
        self.game = game
        self.learner = learner
        self.env = environment

    def step(self, verbose: bool = True) -> Optional[Decision]:
        if self.bounded.exhausted():
            if verbose:
                print("  [Bounded Rationality] Budget exhausted — stopping.")
            return None

        # 1. OBSERVE — pull evidence, update beliefs (Bayes).
        likelihoods = self.env.observe()
        beliefs = self.bdi.belief_agent.update(likelihoods)

        # 2. ORIENT / PLAN — work backward from the goal to candidate actions (Teleology).
        actions = self.planner.plan(self.bdi.desire, beliefs)

        # 3. DECIDE
        ranked = self.decision_theory.score(actions, beliefs)        # Expected Utility
        mode = self.router.route(beliefs, ranked)                    # System 1 / System 2
        self.bounded.charge(1 if mode == "system1" else 2)           # System 2 costs more

        if mode == "system2":
            chosen, critique, revised = self.critic.critique(ranked) # Dialectic
        else:
            chosen, critique, revised = ranked[0], "Fast path (System 1).", False

        chosen, note = self.game.best_response(                      # Game Theory
            chosen, ranked, self.env.competitor_action())

        decision = Decision(action=chosen, mode=mode,
                            expected_utility=chosen.score,
                            critique=f"{critique} {note}".strip(), revised=revised)
        self.bdi.commit(decision)                                    # BDI: form intention

        # 4. ACT — execute the committed intention; observe the real outcome.
        outcome, reward = self.env.act(chosen, beliefs)

        # 5. FEEDBACK — credit assignment (RL) so values improve next loop.
        self.learner.update(outcome, reward)

        if verbose:
            top = ", ".join(f"{a.name}:{a.score:.2f}" for a in ranked)
            print(f"  belief={ {h: round(p,2) for h,p in beliefs.items()} } "
                  f"mode={mode}")
            print(f"  ranked[{top}]")
            print(f"  -> chose '{chosen.name}'  EU={chosen.score:.2f}  "
                  f"outcome='{outcome}' reward={reward:+.2f}")
            print(f"  critique: {decision.critique}")
        return decision

    def run(self, max_cycles: int = 10, verbose: bool = True) -> List[Decision]:
        for i in range(max_cycles):
            if verbose:
                print(f"\n--- OODA cycle {i + 1} ---")
            if self.step(verbose) is None:
                break
        return self.bdi.history


# ---------------------------------------------------------------------------
# The connection graph (so the network is literally "a set of connected agents")
# ---------------------------------------------------------------------------

EDGES: List[Tuple[str, str, str]] = [
    # (source, target, what flows along the edge)
    ("Environment",          "BayesianBeliefAgent",  "evidence / likelihoods"),
    ("BayesianBeliefAgent",  "BDIState",             "updated beliefs"),
    ("BDIState",             "TeleologyPlanner",     "goal (desire) + beliefs"),
    ("TeleologyPlanner",     "DecisionTheoryAgent",  "candidate actions"),
    ("ReinforcementLearner", "DecisionTheoryAgent",  "learned outcome rewards"),
    ("DecisionTheoryAgent",  "DualProcessRouter",    "ranked actions + EU"),
    ("DecisionTheoryAgent",  "BoundedRationalityAgent", "ranked actions"),
    ("DualProcessRouter",    "DialecticCritic",      "system2 escalation"),
    ("BoundedRationalityAgent", "DialecticCritic",   "compute budget / satisfice"),
    ("DialecticCritic",      "GameTheoryAgent",      "critiqued action"),
    ("GameTheoryAgent",      "BDIState",             "best-response intention"),
    ("BDIState",             "OODAController",       "committed intention"),
    ("OODAController",       "Environment",          "action execution"),
    ("Environment",          "ReinforcementLearner", "realized reward"),
    ("OODAController",       "BayesianBeliefAgent",  "loop back (observe outcome)"),
]


def print_graph() -> None:
    print("Connected-agent network (data-flow graph):")
    for src, dst, payload in EDGES:
        print(f"  {src:>24}  --[{payload}]-->  {dst}")


# ---------------------------------------------------------------------------
# A toy environment so the network actually runs
# ---------------------------------------------------------------------------

class Environment:
    """A tiny uncertain world to exercise every node.

    There is a hidden state ("sunny" or "stormy"). The agent never sees it directly;
    it only gets noisy evidence. Actions pay off differently depending on the true
    state. A competitor occasionally grabs the same action, triggering Game Theory.
    """

    def __init__(self, seed: int = 7):
        self.rng = random.Random(seed)
        self.true_state = self.rng.choice(["sunny", "stormy"])

    def observe(self) -> Dict[str, float]:
        """Return P(evidence | hypothesis): noisy sensor reading of the weather."""
        if self.true_state == "sunny":
            reading = "bright" if self.rng.random() < 0.8 else "dim"
        else:
            reading = "dim" if self.rng.random() < 0.8 else "bright"
        if reading == "bright":
            return {"sunny": 0.8, "stormy": 0.2}
        return {"sunny": 0.2, "stormy": 0.8}

    def competitor_action(self) -> Optional[str]:
        # 30% of the time a rival agent commits to the high-value "sail" action.
        return "sail" if self.rng.random() < 0.3 else None

    def act(self, action: Action, beliefs: Dict[str, float]) -> Tuple[str, float]:
        """Sample a real outcome from the action's distribution under the TRUE state."""
        dist = action.outcomes.get(self.true_state, {"neutral": 1.0})
        labels, weights = zip(*dist.items())
        outcome = self.rng.choices(labels, weights=weights, k=1)[0]
        reward = OUTCOME_REWARDS.get(outcome, 0.0)
        return outcome, reward


# True rewards of the world (the RL agent learns estimates of these from experience).
OUTCOME_REWARDS = {"great": 2.0, "ok": 0.5, "neutral": 0.0, "bad": -1.0, "wreck": -2.0}


def build_action_library() -> Callable[[str, Dict[str, float]], List[Action]]:
    """Teleology's action generator: goal -> candidate actions with outcome models."""
    def generate(goal: str, beliefs: Dict[str, float]) -> List[Action]:
        return [
            Action("sail",   {"sunny":  {"great": 0.9, "ok": 0.1},
                              "stormy": {"wreck": 0.7, "bad": 0.3}}),
            Action("harbor", {"sunny":  {"ok": 0.6, "neutral": 0.4},
                              "stormy": {"ok": 0.7, "neutral": 0.3}}),
            Action("wait",   {"sunny":  {"neutral": 1.0},
                              "stormy": {"neutral": 1.0}}),
        ]
    return generate


# ---------------------------------------------------------------------------
# Wiring it all together
# ---------------------------------------------------------------------------

def build_network(env: Environment, reasoner=None, budget: int = 8) -> OODAController:
    learner = ReinforcementLearner(
        initial={k: 0.0 for k in OUTCOME_REWARDS}, alpha=0.4)
    belief_agent = BayesianBeliefAgent(priors={"sunny": 0.5, "stormy": 0.5})
    bdi = BDIState(desire="cross the strait with the best expected payoff",
                   belief_agent=belief_agent)
    planner = TeleologyPlanner(build_action_library())
    decision_theory = DecisionTheoryAgent(reward_fn=learner.value)
    bounded = BoundedRationalityAgent(budget=budget, aspiration=1.0)
    router = DualProcessRouter()
    critic = DialecticCritic(reasoner=reasoner)
    game = GameTheoryAgent()
    return OODAController(bdi, planner, decision_theory, bounded, router,
                          critic, game, learner, env)


def main() -> None:
    print("=" * 70)
    print("CONNECTED AGENTS — 10 design principles wired into one OODA loop")
    print("=" * 70)
    print_graph()

    env = Environment(seed=7)
    controller = build_network(env)
    print(f"\n(Hidden true world state for this run: {env.true_state})")
    history = controller.run(max_cycles=6)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    sys2 = sum(1 for d in history if d.mode == "system2")
    revised = sum(1 for d in history if d.revised)
    total = sum(OUTCOME_REWARDS.get(d.action.name, 0.0) for d in history)
    print(f"cycles run         : {len(history)}")
    print(f"System 2 escalations: {sys2}/{len(history)}")
    print(f"dialectic revisions : {revised}")
    print(f"final belief        : "
          f"{ {h: round(p,2) for h,p in controller.bdi.belief_agent.beliefs.items()} }")
    print(f"learned outcome Q   : "
          f"{ {k: round(v,2) for k,v in controller.learner.q.items()} }")


if __name__ == "__main__":
    main()
