"""
LLM-backed dialectic reasoner for the connected-agent network.

This turns `DialecticCritic`'s `reasoner` hook into a genuine multi-agent debate:
three model calls play *generator*, *critic*, and *judge* (thesis -> antithesis ->
synthesis, the Hegelian / Socratic / pragmatist engine from Category 3).

It follows this course's model convention — an OpenAI-compatible client pointed at
GitHub Models — so it works with just a `GITHUB_TOKEN`:

    export GITHUB_TOKEN=...        # https://github.com/settings/tokens
    pip install openai
    python llm_reasoner.py

If `openai` is not installed or no token is set, it falls back to a deterministic
"mock debate" so the file still runs and can be tested offline. The function it
returns is a drop-in for `DialecticCritic(reasoner=...)`, so the rest of the
network in connected_agents.py is unchanged.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional

from connected_agents import Action, Environment, build_network


# Course default (GitHub Models). Override with env vars to point elsewhere
# (e.g. Azure OpenAI or a local server) without touching the code.
DEFAULT_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://models.inference.ai.azure.com")
DEFAULT_MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")
DEFAULT_API_KEY = os.getenv("GITHUB_TOKEN") or os.getenv("OPENAI_API_KEY")


def _serialize(ranked: List[Action]) -> str:
    """Render the candidate actions (name, expected utility, outcome model) as JSON
    so the model can reason over them precisely."""
    return json.dumps(
        [{"name": a.name, "expected_utility": round(a.score, 3), "outcomes": a.outcomes}
         for a in ranked],
        indent=2,
    )


def make_llm_reasoner(client=None, model: str = DEFAULT_MODEL, verbose: bool = True):
    """Return a `reasoner(phase, ranked) -> Optional[str]` for DialecticCritic.

    Runs a three-role debate and returns the *name* of the winning action, or None
    to let the critic fall back to its deterministic pragmatic rule.
    """

    # Lazily build an OpenAI-compatible client unless one was injected.
    if client is None:
        try:
            from openai import OpenAI
            if not DEFAULT_API_KEY:
                raise RuntimeError("no API key (set GITHUB_TOKEN)")
            client = OpenAI(base_url=DEFAULT_BASE_URL, api_key=DEFAULT_API_KEY)
        except Exception as exc:  # offline / not installed -> mock debate
            if verbose:
                print(f"  [reasoner] LLM unavailable ({exc}); using mock debate.")
            return _mock_reasoner(verbose=verbose)

    def _ask(system: str, user: str) -> str:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.4,
        )
        return (resp.choices[0].message.content or "").strip()

    warned = {"done": False}

    def reasoner(phase: str, ranked: List[Action]) -> Optional[str]:
        if len(ranked) < 2:
            return None
        try:
            return _debate(ranked)
        except Exception as exc:  # network / auth / rate-limit -> safe fallback
            if verbose and not warned["done"]:
                print(f"  [reasoner] LLM call failed ({exc}); "
                      f"falling back to deterministic critique this run.")
                warned["done"] = True
            return None

    def _debate(ranked: List[Action]) -> Optional[str]:
        names = [a.name for a in ranked]
        candidates = _serialize(ranked)

        # 1. GENERATOR (thesis): argue for the top-ranked action.
        thesis = _ask(
            "You are the GENERATOR in an agent's deliberation. Argue concisely "
            "for why the first candidate action is the right choice.",
            f"Goal: maximize expected payoff under uncertainty.\n"
            f"Candidates (ranked, with outcome models):\n{candidates}\n"
            f"Argue FOR '{names[0]}' in 2-3 sentences.")

        # 2. CRITIC (antithesis): strongest objection + case for a rival.
        antithesis = _ask(
            "You are the CRITIC. Find the strongest objection to the generator's "
            "choice and argue for the best alternative.",
            f"Candidates:\n{candidates}\n\nGenerator argued:\n{thesis}\n\n"
            f"Give the strongest objection and argue for a rival action in 2-3 sentences.")

        # 3. JUDGE (synthesis): pick the winner, constrained to a real candidate name.
        verdict = _ask(
            "You are the JUDGE. Weigh both arguments and decide. Reply with ONLY a "
            f"JSON object: {{\"choice\": <one of {names}>, \"why\": <one short sentence>}}.",
            f"Candidates:\n{candidates}\n\nGENERATOR:\n{thesis}\n\nCRITIC:\n{antithesis}")

        choice = _parse_choice(verdict, names)
        if verbose:
            print(f"  [debate] thesis-> {names[0]} | judge-> {choice or '(unparsed)'}")
        return choice

    return reasoner


def _parse_choice(text: str, names: List[str]) -> Optional[str]:
    """Extract a valid action name from the judge's reply, defensively."""
    try:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            choice = json.loads(text[start:end + 1]).get("choice")
            if choice in names:
                return choice
    except Exception:
        pass
    # Fallback: first candidate name that appears verbatim in the reply.
    for n in names:
        if n in text:
            return n
    return None


def _mock_reasoner(verbose: bool = True):
    """Offline stand-in: a deterministic 'debate' that prefers the more robust rival
    when expected utilities are close — so the demo still exercises the S2 path."""
    def reasoner(phase: str, ranked: List[Action]) -> Optional[str]:
        if len(ranked) < 2:
            return None
        top, rival = ranked[0], ranked[1]
        # Robust = lower spread of total outcome mass across hypotheses.
        def spread(a: Action) -> float:
            masses = [sum(d.values()) for d in a.outcomes.values()] or [0.0]
            m = sum(masses) / len(masses)
            return sum((x - m) ** 2 for x in masses)
        if (top.score - rival.score) <= 0.4 and spread(rival) < spread(top):
            if verbose:
                print(f"  [mock debate] synthesis prefers robust '{rival.name}'")
            return rival.name
        return top.name
    return reasoner


def main() -> None:
    print("=" * 70)
    print("CONNECTED AGENTS with an LLM-backed dialectic critic (System 2)")
    print("=" * 70)
    env = Environment(seed=7)
    reasoner = make_llm_reasoner(verbose=True)
    controller = build_network(env, reasoner=reasoner)
    print(f"(Hidden true world state: {env.true_state})")
    history = controller.run(max_cycles=6)
    revised = sum(1 for d in history if d.revised)
    print(f"\nDialectic revisions made by the critic: {revised}/{len(history)}")


if __name__ == "__main__":
    main()
