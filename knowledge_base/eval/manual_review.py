"""Attach a MANUALLY VERIFIED verdict + justification to ALL 100 questions.

Every one of the 100 model answers was read against its source documents by hand.
The automated matcher was discarded: it proved wrong in both directions (false
negatives on number formatting; a false positive on #78 matching an incidental token).

Verdicts:
  CORRECT    - agrees with the source documents
  INCOMPLET  - true but misses part of the expected answer
  INCORRECT  - contradicts the source documents
  DISCUTABLE - does not really address the question asked
  CONFLIT    - corpus holds contradictory sources; model followed the other one
  REFUS      - model declined although the information exists in the corpus
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge_base" / "build" / "test100_results.json"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

R = {
    1:  ("CORRECT", "1990 et loi n°106 du 26 novembre 1990 : exact."),
    2:  ("CORRECT", "Université de Carthage : exact."),
    3:  ("REFUS", "L'information (École Normale Supérieure, 1956) figure pourtant dans fsb_presentation_about."),
    4:  ("CORRECT", "3 428 étudiants : exact. L'indice automatique l'avait marqué à tort (format 3428 vs 3 428)."),
    5:  ("CORRECT", "Présentation conforme : tutelle ministérielle, Université de Carthage, création en 1990."),
    6:  ("INCOMPLET", "Ne cite qu'un seul département sur six. Aucun document ne liste les six départements ensemble : l'information est éclatée entre les fiches dep_*."),
    7:  ("CORRECT", "Centre de Carrières et de Certification des Compétences : exact."),
    8:  ("CORRECT", "IDEA LAB correctement identifié, trouvé via la fiche du cycle informatique."),
    9:  ("CORRECT", "MAHNAOUI MOHAMED : exact."),
    10: ("REFUS", "KHELIFI ABDESSATAR figure dans dep_mathematiques, fiche en bloc unique peu retrouvable."),
    11: ("CORRECT", "DHIFAOUI BELGACEM et poste 154 : exact."),
    12: ("CORRECT", "BOUGHDIRI Mabrouk : exact."),
    13: ("CORRECT", "Fadi KACEM : exact."),
    14: ("CORRECT", "Poste 227 : exact."),
    15: ("CORRECT", "Poste 312 : exact."),
    16: ("CORRECT", "Afef GHAZOUANI : exact."),
    17: ("CORRECT", "Monia BOUKMIS : exact."),
    18: ("CORRECT", "Poste 155 : exact."),
    19: ("CORRECT", "Bloc chimie : exact."),
    20: ("CORRECT", "Licences et mastères du département correctement listés."),
    21: ("CORRECT", "Liste des licences par département conforme aux fiches sources."),
    22: ("CORRECT", "Les deux licences d'informatique (GLSI et Systèmes Embarqués & IoT) : exact."),
    23: ("CORRECT", "Licence Mathématiques et Licence Mathématiques Appliquées (Math-Info) : exact."),
    24: ("CORRECT", "Chimie Industrielle, Chimie Fine, Chimie Recherche : exact."),
    25: ("CORRECT", "Les sept licences du département de Physique : exact."),
    26: ("CORRECT", "Les quatre licences de biologie : exact."),
    27: ("CORRECT", "Géo-ressources et environnement / Sciences et techniques de géologie : exact."),
    28: ("CORRECT", "Licence Physique-Chimie confirmée."),
    29: ("CORRECT", "Définition de la licence GLSI : exact."),
    30: ("CORRECT", "Formation Systèmes Embarqués & IoT identifiée (via la mention Computer Engineering)."),
    31: ("CORRECT", "Définition de la licence EEA : exact."),
    32: ("CORRECT", "Licence Biotechnologie confirmée."),
    33: ("CORRECT", "Licence Génie Énergétique, parcours Froid et climatisation : exact."),
    34: ("CORRECT", "Formations du département de Chimie correctement listées."),
    35: ("CORRECT", "Cycle ingénieur en Génie Logiciel confirmé."),
    36: ("CORRECT", "Distinction mastères de recherche / professionnels et liste : conforme."),
    37: ("CORRECT", "Liste des mastères de recherche conforme."),
    38: ("CORRECT", "MP Data Sciences et MP Mathématiques et Data Science : exact."),
    39: ("CORRECT", "Mastère de Recherche en Sciences Informatiques confirmé."),
    40: ("CORRECT", "Les quatre mastères professionnels de physique : exact."),
    41: ("CORRECT", "MP Chimie Industrielle et Pétrochimie : exact."),
    42: ("CORRECT", "SSA = Sécurité Sanitaire des Aliments : exact."),
    43: ("CORRECT", "Mastère de Recherche en Hydrogéosciences et Environnement : exact."),
    44: ("CORRECT", "Mastères liés à l'environnement correctement identifiés."),
    45: ("REFUS", "L'abréviation ESRV n'est développée que dans le tableau des coordinateurs, non retrouvé."),
    46: ("CORRECT", "Master co-construit Management & Innovation : exact."),
    47: ("CORRECT", "Géologie appliquée et Géo-ressources et Applications : exact."),
    48: ("CORRECT", "Contenu du M1 (géométrie différentielle, analyse complexe, etc.) conforme."),
    49: ("CORRECT", "Voie doctorale ou professionnalisante : exact."),
    50: ("CORRECT", "Mastère BMC-Biotech et ses deux parcours : exact."),
    51: ("REFUS", "Les mastères du département de Physique figurent dans dep_physique, fiche en bloc unique."),
    52: ("CORRECT", "Master de Recherche en Mathématiques : exact."),
    53: ("REFUS", "Le MP Mathématiques Appliquées figure dans le tableau des coordinateurs, non retrouvé."),
    54: ("REFUS", "BELGASEM SELMI figure dans liste_des_coordinateurs, tableau non retrouvé."),
    55: ("INCORRECT", "ERREUR RÉELLE — seule erreur factuelle du test. La question portait sur le MP Data Sciences (coordinateur ANIS BELAICHA) ; le modèle répond sur le MP Mathématiques Appliquées (Chaouki Aouiti). Deux mastères proches ont été confondus dans le même tableau."),
    56: ("REFUS", "MOHAMED BARKEOUI figure dans liste_des_coordinateurs, tableau non retrouvé."),
    57: ("REFUS", "CHIRAZ ABBAS figure dans liste_des_coordinateurs, tableau non retrouvé."),
    58: ("REFUS", "MABROUK BOUGHDIRI figure dans liste_des_coordinateurs, tableau non retrouvé."),
    59: ("REFUS", "SADDOK JABRALLAH figure dans liste_des_coordinateurs, tableau non retrouvé."),
    60: ("REFUS", "RIM ABIDI / RIADH TERNANE figurent dans liste_des_coordinateurs, tableau non retrouvé."),
    61: ("CORRECT", "FETHI MEJRI : exact. À noter : cette question a réussi alors que #54–#60 ont été refusées sur le MÊME document — la recherche est instable sur ce tableau, elle n'échoue pas systématiquement."),
    62: ("CORRECT", "Procédure d'inscription via inscription.tn : conforme."),
    63: ("CORRECT", "www.inscription.tn : exact."),
    64: ("CORRECT", "15/08 – 30/08/2024 : exact. Écart de format uniquement (15 août vs 15/08)."),
    65: ("CORRECT", "12 septembre 2024 : exact. Écart de format uniquement."),
    66: ("CORRECT", "30 août – 10 septembre 2024 : exact. Écart de format uniquement."),
    67: ("CORRECT", "15 – 25 septembre 2024 : exact."),
    68: ("CORRECT", "Plateforme master.ucar.rnu.tn et délai du 10 juillet 2026 : conforme."),
    69: ("CORRECT", "10 juillet 2026 : exact."),
    70: ("REFUS", "La liste des pièces figure pourtant dans appel_candidature_masters_2026_2027."),
    71: ("CORRECT", "31 juillet 2026 pour la publication des listes : exact (la question portait sur la publication)."),
    72: ("CORRECT", "Procédure de dérogation (demande au doyen + attestations) : conforme."),
    73: ("CORRECT", "3 inscriptions et 1 dérogation : exact."),
    74: ("CONFLIT", "Le modèle cite les montants officiels de l'OOUN (arrêtés ministériels) ; la réponse attendue provenait d'un article de blog commercial présent dans la base. Les deux sources se contredisent — celle du modèle est la plus fiable. Le modèle a eu raison contre notre référence."),
    75: ("CONFLIT", "Même conflit de sources que #74 : montants officiels de l'OOUN contre article commercial."),
    76: ("REFUS", "Le tarif du foyer ne figure que dans l'article commercial, source peu fiable."),
    77: ("CORRECT", "Bourse de mérite : bénéficiaires et montant correctement restitués."),
    78: ("DISCUTABLE", "Le modèle cite une règle sur le cumul avec un AUTRE organisme, sans répondre directement au cumul bourse + prêt. L'indice automatique l'avait marqué MATCH à tort, sur le jeton « deux » présent par hasard."),
    79: ("CORRECT", "Publication fin novembre et notification : exact."),
    80: ("REFUS", "La procédure de recours ne figure que dans l'article commercial, source peu fiable."),
    81: ("CORRECT", "Réduction de 50 à 75 % sur les abonnements : exact."),
    82: ("CORRECT", "Réponse plus complète que l'attendu (périodes de dépôt détaillées)."),
    83: ("CORRECT", "2 septembre – 31 octobre 2025 : exact."),
    84: ("CORRECT", "1er octobre 2025 – 15 mai 2026, envoi jusqu'au 30 mai 2026 : exact."),
    85: ("CORRECT", "5 septembre – 30 novembre 2025 : exact."),
    86: ("CORRECT", "Caractère obligatoire du stage correctement restitué par niveau d'études."),
    87: ("CORRECT", "4 mois en licence appliquée, 6 mois en mastère professionnel : exact. L'attendu écrivait les nombres en lettres."),
    88: ("CORRECT", "Objectifs du stage conformes au document."),
    89: ("CORRECT", "Procédure via la plateforme « mim » (Stage-FSB) : exact."),
    90: ("CORRECT", "Hors calendrier pédagogique, avant le 15 septembre : exact."),
    91: ("CORRECT", "Liste des pièces du dossier de dépôt de thèse conforme."),
    92: ("CORRECT", "30 crédits : exact."),
    93: ("CORRECT", "Procédure de changement de parcours de thèse conforme."),
    94: ("CORRECT", "Pièces pour un changement d'encadrant : exact."),
    95: ("CORRECT", "Procédures de doctorat correctement listées."),
    96: ("REFUS", "Les pièces figurent dans le formulaire d'annulation de cotutelle, document très bruité (formulaire à champs vides)."),
    97: ("CORRECT", "20 décembre 2025 – 4 janvier 2026 : exact."),
    98: ("CORRECT", "14 mars – 29 mars 2026 : exact."),
    99: ("CORRECT", "Minimum de 28 semaines de cours effectifs : exact."),
    100: ("CORRECT", "Dépôt du dossier auprès du CEC (Direction des Stages) : conforme."),
}


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    missing = []
    for r in d["results"]:
        v = R.get(r["id"])
        if not v:
            missing.append(r["id"])
            continue
        r["manual"], r["manual_note"] = v
        # consistency check: a REFUS verdict must match an actual refusal
        if (v[0] == "REFUS") != bool(r["refused"]):
            print(f"  !! MISMATCH #{r['id']}: verdict={v[0]} refused={r['refused']}")

    res = d["results"]
    d["summary"]["manual"] = {
        v: sum(1 for r in res if r["manual"] == v)
        for v in ("CORRECT", "INCOMPLET", "INCORRECT", "DISCUTABLE", "CONFLIT", "REFUS")
    }
    d["summary"]["reviewed"] = "all 100 answers read against sources by hand"
    DATA.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    if missing:
        print("MISSING REVIEWS:", missing)
    print("MANUAL VERDICTS:", json.dumps(d["summary"]["manual"], ensure_ascii=False))
    print("notes attached:", sum(1 for r in res if r.get("manual_note")), "/ 100")


if __name__ == "__main__":
    main()
