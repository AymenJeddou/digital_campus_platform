"""Academic Agent — courses, prerequisites, study plans, academic calendar.

Filters results by the student's academic_year by default.
"""

from ai.agents.base_agent import BaseAgent
from ai.prompts.system_prompts import ACADEMIC_AGENT_PROMPT  # noqa: F401


class AcademicAgent(BaseAgent):
    """Agent Académique de la FSB."""

    agent_type = "academic"
