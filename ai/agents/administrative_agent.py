"""Administrative Agent — registration, scholarships, administrative deadlines.

Newcomer-specific procedures are shown only to prospective students.
"""

from ai.agents.base_agent import BaseAgent
from ai.prompts.system_prompts import ADMINISTRATIVE_AGENT_PROMPT  # noqa: F401


class AdministrativeAgent(BaseAgent):
    """Agent Administratif de la FSB."""

    agent_type = "administrative"
