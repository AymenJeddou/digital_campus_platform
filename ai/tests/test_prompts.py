"""Tests for prompt formatting and agent routing.

These tests validate string formatting only — they never call the LLM, so they
pass without a real ``GEMINI_API_KEY``.

Run from the repository root:

    pytest ai/tests/
"""

import pytest

from ai.prompts.system_prompts import AGENT_TYPES, get_prompt
from ai.rag.generator import RAGGenerator


@pytest.mark.parametrize("agent_type", AGENT_TYPES)
def test_get_prompt_returns_non_empty_string(agent_type):
    prompt = get_prompt(
        agent_type=agent_type,
        student_status="prospective",
        student_academic_year="L2",
        context="Contexte de test.",
        question="Question de test ?",
    )
    assert isinstance(prompt, str)
    assert prompt.strip() != ""


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

    assert status in prompt
    assert year in prompt
    assert context in prompt
    assert question in prompt


def test_get_prompt_invalid_agent_raises():
    with pytest.raises(ValueError):
        get_prompt(
            agent_type="not_a_real_agent",
            student_status="prospective",
            student_academic_year="L1",
            context="ctx",
            question="q",
        )


def test_rag_generator_invalid_agent_raises():
    with pytest.raises(ValueError):
        RAGGenerator("not_a_real_agent")
