"""Intent routing: pure regex, no API key needed."""

from ai.rag.intent import (FACTUAL, GREETING, META, THANKS, classify_intent,
                           conversational_reply, is_administrative)


def test_greetings_thanks_and_meta():
    assert classify_intent("Bonjour !") == GREETING
    assert classify_intent("salut ça va ?") == GREETING
    assert classify_intent("مرحبا") == GREETING
    assert classify_intent("Merci beaucoup") == THANKS
    assert classify_intent("شكرا") == THANKS
    assert classify_intent("Que peux-tu faire ?") == META
    assert classify_intent("bonjour, qui es-tu ?") == META


def test_real_questions_go_to_rag():
    assert classify_intent("") == FACTUAL
    assert classify_intent("bonjour, quelles licences propose la FSB ?") == FACTUAL
    assert classify_intent("merci, et pour le master ?") == FACTUAL


def test_administrative_vocabulary():
    assert is_administrative("Comment obtenir une attestation de présence ?")
    assert is_administrative("Date limite de réinscription ?")
    assert not is_administrative("Quels sont les débouchés de la licence en informatique ?")
    assert not is_administrative("")


def test_replies_only_for_conversational_intents():
    assert conversational_reply(GREETING).startswith("Bonjour")
    assert conversational_reply(FACTUAL) is None
