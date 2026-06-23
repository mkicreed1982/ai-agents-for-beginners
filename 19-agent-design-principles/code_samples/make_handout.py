"""
Generate the one-page teaching handout (PDF) for the agent-design principles.

Lays the ten principles out as a FIVE-LEVEL learning ladder that climbs from a
single agent's decision up to multi-agent strategy and the values layer:

    L1 Decide  ->  L2 Operate  ->  L3 Improve & Reason  ->  L4 Strategize  ->  L5 Constrain

Usage:  pip install reportlab && python make_handout.py
Output: ../agent-design-principles-handout.pdf
"""

from __future__ import annotations

import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

OUT = os.path.join(os.path.dirname(__file__), "..", "agent-design-principles-handout.pdf")

# Five levels of the learning ladder. Each: (level, band colour, name, rows)
# where each row = (principle + strategist, agent role, build decision).
LEVELS = [
    ("L1", colors.HexColor("#1b4965"), "DECIDE — The Rational Core", [
        ("Bayesian Epistemology · Bayes, Pearl", "BayesianBeliefAgent",
         "Beliefs are probabilities; revise on every observation."),
        ("Expected Utility · Von Neumann, Savage", "DecisionTheoryAgent",
         "The scoring rule: pick the action with the best expected payoff."),
        ("Bounded Rationality · Simon", "BoundedRationalityAgent",
         "Budgets, early stopping, satisficing — 'good enough', not perfect."),
    ]),
    ("L2", colors.HexColor("#2a6f97"), "OPERATE — The Loop and the Goal", [
        ("OODA / Cybernetics · Wiener, Boyd", "OODAController",
         "The control skeleton: sense - decide - act - observe - repeat."),
        ("Teleology / Means-Ends · Aristotle, STRIPS", "TeleologyPlanner",
         "Start from the goal; work backward to candidate actions."),
        ("Belief-Desire-Intention · Bratman", "BDIState",
         "Split what it knows, wants, and has committed to."),
    ]),
    ("L3", colors.HexColor("#2c7da0"), "IMPROVE & REASON — Learning and Thinking", [
        ("Reinforcement Learning · Skinner, Sutton & Barto", "ReinforcementLearner",
         "Reward outcomes; credit assignment tunes what the agent values."),
        ("Dual-Process (System 1/2) · Kahneman", "DualProcessRouter",
         "Decide when to think harder: fast reaction vs. deliberation."),
        ("Dialectic + Pragmatism · Hegel, Socrates, Peirce", "DialecticCritic",
         "Generator-vs-critic: test an idea against its opposite; keep what works."),
    ]),
    ("L4", colors.HexColor("#468faf"), "STRATEGIZE — Strategy Among Others", [
        ("Game Theory · Nash, Schelling", "GameTheoryAgent",
         "Best response when other agents act strategically; avoid collisions."),
    ]),
    ("L5", colors.HexColor("#7d8597"), "CONSTRAIN — The Values Layer (add-on)", [
        ("Deontology vs. Consequentialism · Kant, Mill", "constraint filter",
         "Rules vs. outcomes — guardrails checked before an intention commits."),
        ("Stoic control · Epictetus  ·  Occam's Razor", "scoping / prior",
         "Boundary heuristic + simplicity prior that shape, not drive, decisions."),
    ]),
]


def build() -> str:
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=12 * mm, rightMargin=12 * mm,
        topMargin=10 * mm, bottomMargin=10 * mm,
        title="Agent Design Principles — Learning Ladder")

    ss = getSampleStyleSheet()
    h_title = ParagraphStyle("t", parent=ss["Title"], fontSize=18, spaceAfter=2,
                             textColor=colors.HexColor("#1b4965"))
    h_sub = ParagraphStyle("s", parent=ss["Normal"], fontSize=8.5, alignment=TA_CENTER,
                           textColor=colors.HexColor("#555555"), spaceAfter=6)
    band = ParagraphStyle("band", parent=ss["Normal"], fontSize=10, leading=12,
                          textColor=colors.white, fontName="Helvetica-Bold")
    cell_p = ParagraphStyle("p", parent=ss["Normal"], fontSize=7.6, leading=9)
    cell_role = ParagraphStyle("r", parent=ss["Normal"], fontSize=7.6, leading=9,
                               fontName="Courier-Bold", textColor=colors.HexColor("#1b4965"))
    foot = ParagraphStyle("f", parent=ss["Normal"], fontSize=7, leading=9,
                          textColor=colors.HexColor("#555555"), alignment=TA_LEFT)

    story = [
        Paragraph("Agent Design Principles — A Five-Level Learning Ladder", h_title),
        Paragraph("Ten principles ranked by load-bearing-ness (how directly each forces "
                  "a build decision), wired into one connected-agent OODA loop.", h_sub),
    ]

    col_widths = [14 * mm, 62 * mm, 38 * mm, 72 * mm]
    for level, colour, name, rows in LEVELS:
        # Band header row spanning all columns.
        data = [[Paragraph(f"{level} &nbsp; {name}", band), "", "", ""]]
        for principle, role, decision in rows:
            data.append([
                "",
                Paragraph(principle, cell_p),
                Paragraph(role, cell_role),
                Paragraph(decision, cell_p),
            ])
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), colour),
            ("LEFTPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 3),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 3),
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f2f5f8")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd8e0")),
            ("INNERGRID", (0, 1), (-1, -1), 0.4, colors.HexColor("#dde4ea")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 1), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 3),
        ]))
        story.append(t)
        story.append(Spacer(1, 3))

    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<b>How to read it:</b> climb the ladder. L1 makes one good decision; L2 wraps it "
        "in a loop with a goal and memory; L3 lets the agent learn and reason about when "
        "to think harder; L4 adds other strategic agents; L5 is the values/guardrail layer "
        "that constrains the rest. The runnable network lives in "
        "<font name='Courier'>code_samples/connected_agents.py</font>.", foot))

    doc.build(story)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"wrote {os.path.abspath(path)}")
