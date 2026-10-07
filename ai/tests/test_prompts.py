"""Tests for prompt formatting and agent routing.

These tests validate string formatting only — they never call the LLM, so they
pass without a real ``GEMINI_API_KEY``.

Run from the repository root:

    pytest ai/tests/
"""

import pytest

from ai.prompts.system_prompts import AGENT_TYPES, get_prompt
from ai.rag.intent import is_administrative


@pytest.mark.parametrize("agent_type", AGENT_TYPES)
def test_get_prompt_returns_non_empty_string(agent_type):
    prompt = get_prompt(
        agent_type=agent_type,
        student_status="prospective",
        student_academic_year="L2",
        context="Contexte de test.",
        question="Question de test ?",
    )
    assert prompt["system"].strip() and prompt["user"].strip()


@pytest.mark.parametrize("agent_type", AGENT_TYPES)
def test_prompt_contains_injected_values(agent_type):
    status = "enrolled"
    year = "M1"
    context = "CHUNK_CONTEXT_SENTINEL"
    question = "QUESTION_SENTINEL"

    prompt = get_prompt(
        agent_type=agent_type,
        student_status=status,
        student_academic_year=year,
        context=context,
        question=question,
    )

    # Trusted values go in the system role, the student's text only in the user role.
    assert status in prompt["system"]
    assert year in prompt["system"]
    assert context in prompt["system"]
    assert question in prompt["user"]
    assert question not in prompt["system"]


def test_get_prompt_invalid_agent_raises():
    with pytest.raises(ValueError):
        get_prompt(
            agent_type="not_a_real_agent",
            student_status="prospective",
            student_academic_year="L1",
            context="ctx",
            question="q",
        )


def test_history_goes_in_user_role():
    prompt = get_prompt("orientation", "prospective", None, "ctx", "Q?", history="Étudiant: avant")
    assert "Étudiant: avant" in prompt["user"]
    assert "Étudiant: avant" not in prompt["system"]


@pytest.mark.parametrize("message,expected", [
    ("Comment faire une demande de bourse ?", True),
    ("Quels documents pour la réinscription en L2 ?", True),
    ("Je veux une attestation de présence", True),
    ("Quelles licences en informatique ?", False),
    ("Explique-moi les intégrales", False),
])
def test_is_administrative(message, expected):
    assert is_administrative(message) is expected
