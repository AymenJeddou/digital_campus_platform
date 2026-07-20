"""Lightweight intent routing for the chat assistant.

The RAG pipeline is a *sourced* path: it retrieves documents and answers only
from them. That is correct for factual questions but wrong for greetings, thanks,
and meta-questions ("what can you do?") — those have no supporting document, so
the pipeline refuses them, which reads as a broken chatbot.

This module classifies a message BEFORE the pipeline runs. It is deliberately
**conservative**: only high-confidence conversational patterns are short-circuited;
everything else (the ambiguous majority) falls through to the factual RAG path, so
routing can never turn a real question into a canned reply. No LLM call, no latency.
Multilingual (French + Arabic + a little English), matching the corpus.
"""

from __future__ import annotations

import re
import unicodedata

# Intent labels returned by classify_intent.
GREETING = "greeting"
THANKS = "thanks"
META = "meta"
FACTUAL = "factual"  # -> RAG pipeline


def _normalize(text: str) -> str:
    """Lowercase and strip accents so 'ça' / 'ca', 'à' / 'a' match uniformly."""
    text = text.strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


# Whole-message greetings (short, no factual payload). Anchored so
# "bonjour, quelles licences ..." is NOT caught (it carries a real question).
_GREETING_RE = re.compile(
    r"^(bonjour|bonsoir|salut|coucou|hello|hi|hey|cc|slt|salam|salamou|"
    r"assalamou|marhaba|ahlan)"
    r"[\s!.,]*(ca va|comment vas[ -]?tu|comment allez[ -]?vous|ca roule)?[\s!?.,]*$"
)

_ARABIC_GREETING_RE = re.compile(r"^(السلام|سلام|مرحبا|أهلا|اهلا|صباح|مساء)")

_THANKS_RE = re.compile(
    r"^(merci|merci beaucoup|thanks|thank you|thx|choukran|chokran|شكرا|بارك الله)"
    r"[\s!.,]*$"
)

# Meta / capability questions — kept tight so factual "aide-moi à trouver ..."
# is not swallowed.
_META_PATTERNS = (
    "que peux-tu faire",
    "que peux tu faire",
    "qu'est-ce que tu peux faire",
    "quest-ce que tu peux faire",
    "qu peux tu faire",
    "tu peux faire quoi",
    "tu sers a quoi",
    "a quoi tu sers",
    "qui es-tu",
    "qui es tu",
    "tu es qui",
    "comment ca marche",
    "what can you do",
    "who are you",
    "how do you work",
    "ماذا تستطيع",
    "من انت",
    "من أنت",
)


def classify_intent(message: str) -> str:
    """Return the conversational intent of a message.

    Returns one of GREETING / THANKS / META / FACTUAL. Anything that is not a
    high-confidence conversational pattern returns FACTUAL (-> RAG pipeline).
    """
    if not message or not message.strip():
        return FACTUAL

    raw = message.strip()
    norm = _normalize(raw)

    # Meta first: capability questions can contain a greeting word.
    if any(p in norm for p in _META_PATTERNS):
        return META
    if _THANKS_RE.match(norm):
        return THANKS
    if _GREETING_RE.match(norm) or _ARABIC_GREETING_RE.match(raw):
        return GREETING
    return FACTUAL


# --- Bounded, non-fabricating conversational replies (no retrieval) -----------

_CAPABILITIES = (
    "Je suis l'assistant de la Faculté des Sciences de Bizerte. Je peux répondre "
    "à tes questions sur la faculté : les licences et masters proposés, les "
    "départements, les procédures d'inscription et de bourse, le calendrier "
    "universitaire, et le contenu des cours. Mes réponses s'appuient sur les "
    "documents officiels de la faculté et sont accompagnées de leurs sources."
)

_RESPONSES = {
    GREETING: (
        "Bonjour ! " + _CAPABILITIES + " Que puis-je faire pour toi ?"
    ),
    THANKS: (
        "Avec plaisir ! N'hésite pas si tu as d'autres questions sur la faculté."
    ),
    META: _CAPABILITIES,
}


def conversational_reply(intent: str) -> str | None:
    """Return a canned reply for a conversational intent, or None if factual."""
    return _RESPONSES.get(intent)
