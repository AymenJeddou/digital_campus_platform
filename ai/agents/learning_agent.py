"""Learning Agent — course material explanations and learning plans.

Scoped to the student's current academic_year.
"""

from ai.agents.base_agent import BaseAgent
from ai.prompts.system_prompts import LEARNING_AGENT_PROMPT  # noqa: F401


class LearningAgent(BaseAgent):
    """Agent d'Apprentissage de la FSB."""

    agent_type = "learning"
