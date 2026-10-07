"""Official academic calendar dates, from the ministry circular in
knowledge_base/regulation/national/calendrier_universitaire_2025_2026.md.

Add the next year's dates here when the ministry publishes them; only dates
that appear in a source document belong in this list.
"""
from datetime import date

SOURCE = "Calendrier universitaire 2025-2026"

EVENTS = [
    (date(2025, 9, 12), "Rentrée universitaire"),
    (date(2025, 12, 20), "Début des vacances d'hiver"),
    (date(2026, 1, 5), "Reprise des cours après les vacances d'hiver"),
    (date(2026, 3, 14), "Début des vacances de printemps"),
    (date(2026, 3, 30), "Reprise des cours après les vacances de printemps"),
]
