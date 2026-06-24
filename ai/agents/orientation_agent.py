"""Orientation Agent — programs, admission, campus life, post-Bac guidance.

Primary agent for prospective / newcomer students.
"""

from ai.agents.base_agent import BaseAgent
from ai.prompts.system_prompts import ORIENTATION_AGENT_PROMPT  # noqa: F401


class OrientationAgent(BaseAgent):
    """Agent d'Orientation de la FSB."""

    agent_type = "orientation"
