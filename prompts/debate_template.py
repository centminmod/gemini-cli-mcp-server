"""
AI debate collaboration templates.

This module provides templates for debate mode in gemini_ai_collaboration.
"""
from typing import Optional
from .base_template import BaseTemplate


def get_debate_prompt(
    content: str,
    round_number: int,
    total_rounds: int,
    debate_style: str = "constructive",
    previous_arguments: Optional[str] = None,
    focus: Optional[str] = None
) -> str:
    """
    Generate a debate round prompt.

    Args:
        content: Topic or content to debate
        round_number: Current round number
        total_rounds: Total number of rounds
        debate_style: Style of debate
        previous_arguments: Arguments from previous rounds
        focus: Focus area

    Returns:
        Complete prompt string
    """
    style_instructions = {
        "constructive": """
Debate Style: Constructive
- Build upon previous points
- Seek common ground while presenting your view
- Offer balanced analysis
- Acknowledge valid points from other perspectives""",
        "adversarial": """
Debate Style: Adversarial
- Challenge assumptions rigorously
- Present counter-arguments
- Identify weaknesses in opposing views
- Defend your position strongly""",
        "collaborative": """
Debate Style: Collaborative
- Work together to explore the topic
- Build on others' ideas
- Synthesize different viewpoints
- Seek comprehensive understanding""",
        "socratic": """
Debate Style: Socratic
- Use questioning to explore ideas
- Challenge underlying assumptions
- Seek deeper understanding
- Guide through logical reasoning""",
        "devil_advocate": """
Debate Style: Devil's Advocate
- Deliberately argue against the prevailing view
- Present challenging scenarios
- Test the strength of arguments
- Expose potential weaknesses"""
    }.get(debate_style, "")

    previous_section = ""
    if previous_arguments:
        previous_section = f"""

Previous Arguments:
{previous_arguments}
"""

    focus_section = ""
    if focus:
        focus_section = f"\nFocus Area: {focus}"

    return f"""You are participating in a structured debate.

Round: {round_number} of {total_rounds}
{style_instructions}{focus_section}{previous_section}

Topic/Content:
{content}

Instructions:
1. Present your perspective on the topic
2. Address points raised in previous rounds (if any)
3. Provide evidence or reasoning for your arguments
4. Identify areas of agreement and disagreement
5. Suggest areas for further exploration

Please provide your response in the following structure:

## Main Argument
[Your primary position and reasoning]

## Supporting Points
- Point 1: [Evidence/reasoning]
- Point 2: [Evidence/reasoning]
- Point 3: [Evidence/reasoning]

## Response to Previous Arguments (if applicable)
[Address specific points from other participants]

## Concessions
[Valid points you acknowledge from other perspectives]

## Questions for Further Discussion
[Questions to advance the debate]

## Summary Position
[Brief statement of your stance after this round]"""


def get_debate_synthesis_prompt(
    topic: str,
    all_arguments: str,
    debate_style: str,
    total_rounds: int
) -> str:
    """
    Generate a debate synthesis prompt.

    Args:
        topic: Original debate topic
        all_arguments: All arguments from the debate
        debate_style: Style used in debate
        total_rounds: Number of rounds completed

    Returns:
        Synthesis prompt string
    """
    return f"""Synthesize the following debate into a comprehensive summary.

Topic: {topic}
Debate Style: {debate_style}
Rounds Completed: {total_rounds}

All Arguments:
{all_arguments}

Please provide:

## 1. Executive Summary
Brief overview of the debate outcome

## 2. Key Arguments

### Points of Agreement
- Consensus areas
- Shared conclusions

### Points of Contention
- Unresolved disagreements
- Competing perspectives

## 3. Argument Analysis

| Participant | Main Position | Strengths | Weaknesses |
|-------------|---------------|-----------|------------|
| [model] | [position] | [strengths] | [weaknesses] |

## 4. Evolution of Discussion
How the debate progressed through rounds

## 5. Conclusions
- Areas with strong consensus
- Areas requiring further discussion
- Recommended next steps

## 6. Final Synthesis
Balanced conclusion incorporating all perspectives"""


class DebateTemplate(BaseTemplate):
    """Template class for debate prompts."""

    @staticmethod
    def get_round_prompt(
        content: str,
        round_number: int,
        total_rounds: int,
        debate_style: str = "constructive",
        previous_arguments: Optional[str] = None,
        focus: Optional[str] = None
    ) -> str:
        """Get the debate round prompt."""
        return get_debate_prompt(
            content, round_number, total_rounds, debate_style, previous_arguments, focus
        )

    @staticmethod
    def get_synthesis_prompt(
        topic: str,
        all_arguments: str,
        debate_style: str,
        total_rounds: int
    ) -> str:
        """Get the debate synthesis prompt."""
        return get_debate_synthesis_prompt(topic, all_arguments, debate_style, total_rounds)
