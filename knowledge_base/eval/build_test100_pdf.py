"""Build the 100-question test report (HTML -> PDF via headless Chrome)."""
import html, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "knowledge_base" / "build" / "test100_results.json"
OUT_HTML = ROOT / "docs" / "FSB_Nexus_100_Question_Test.html"
OUT_PDF = ROOT / "docs" / "FSB_Nexus_100_Question_Test.pdf"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

CSS = """
@page { size: A4; margin: 14mm 12mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 9.2pt; line-height: 1.45; color: #1c2430; margin: 0; }
h1,h2 { color: #143c6e; margin: 0 0 .3em; }
h1 { font-size: 24pt; }
h2 { font-size: 13pt; margin-top: 1.3em; border-bottom: 2px solid #143c6e; padding-bottom: .2em; }
.cover { text-align:center; padding: 16mm 0 6mm; border-bottom: 3px solid #143c6e; margin-bottom: .8em; }
.cover .sub { font-size: 12pt; color:#44536b; margin-top:.4em; }
.meta { margin-top:1.2em; font-size:9.5pt; color:#44536b; }
.kpi { display:flex; gap:6px; margin:1em 0; }
.kpi div { flex:1; border:1px solid #cfd8e3; border-top:3px solid #143c6e; border-radius:4px; padding:7px 4px; text-align:center; background:#fbfcfe; }
.kpi .v { font-size:15pt; font-weight:700; color:#143c6e; display:block; }
.kpi .l { font-size:7pt; color:#56657d; text-transform:uppercase; letter-spacing:.3px; }
.callout { border-left:4px solid #143c6e; background:#f2f6fb; padding:7px 10px; margin:.7em 0; border-radius:0 4px 4px 0; }
.warn { border-left-color:#c77700; background:#fff8ec; }
table.sum { border-collapse:collapse; width:100%; margin:.6em 0; font-size:9pt; }
table.sum th, table.sum td { border:1px solid #cfd8e3; padding:4px 6px; }
table.sum th { background:#143c6e; color:#fff; }
.q { border:1px solid #d8e0ea; border-radius:5px; margin:7px 0; page-break-inside:avoid; overflow:hidden; }
.qh { background:#eef3f9; padding:5px 8px; font-weight:600; color:#143c6e; display:flex; justify-content:space-between; gap:8px; border-bottom:1px solid #d8e0ea; }
.qh .id { color:#7a8699; font-weight:400; font-size:8pt; white-space:nowrap; }
.qb { padding:6px 8px; }
.lbl { font-size:7.2pt; text-transform:uppercase; letter-spacing:.4px; color:#7a8699; font-weight:700; margin-bottom:1px; }
.exp { background:#f3f9f4; border-left:3px solid #1a7a41; padding:4px 7px; margin-bottom:5px; border-radius:0 3px 3px 0; }
.got { background:#f7f9fc; border-left:3px solid #2a6bb0; padding:4px 7px; border-radius:0 3px 3px 0; }
.got.ref { background:#fdf3f3; border-left-color:#b3261e; }
.tag { font-size:7.2pt; font-weight:700; padding:1px 6px; border-radius:9px; color:#fff; white-space:nowrap; }
.CORRECT { background:#1a7a41; } .INCOMPLET { background:#c77700; } .INCORRECT { background:#b3261e; }
.DISCUTABLE { background:#c77700; } .CONFLIT { background:#7c4dbd; } .REFUS { background:#6b7280; }
.cite { font-size:7.6pt; color:#56657d; margin-top:3px; font-style:italic; }
.note { background:#fffbe9; border-left:3px solid #c77700; padding:4px 7px; margin-top:5px; font-size:8.4pt; border-radius:0 3px 3px 0; }
.pagebreak { page-break-before:always; }
"""


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    s, rows = d["summary"], d["results"]
    m = s["manual"]
    e = html.escape
    pct = lambda n: f"{round(100*n/s['total'])}%"

    # group by category
    cats = {}
    for r in rows:
        cats.setdefault(r["cat"], []).append(r)

    body = []
    for cat, items in cats.items():
        body.append(f'<h2>{e(cat)} <span style="font-size:9pt;color:#7a8699;font-weight:400">({len(items)} questions)</span></h2>')
        for r in items:
            cls = "got ref" if r["refused"] else "got"
            cites = ", ".join(f'{e(c.get("document",""))} p.{c.get("page","?")}' for c in r["citations"]) or "aucune"
            note = f'<div class="note"><strong>Revue manuelle :</strong> {e(r["manual_note"])}</div>' if r.get("manual_note") else ""
            body.append(f"""
<div class="q">
  <div class="qh"><span>{e(r['q'])}</span>
    <span style="display:flex;gap:6px;align-items:center">
      <span class="tag {r['manual']}">{r['manual']}</span><span class="id">#{r['id']}</span></span></div>
  <div class="qb">
    <div class="exp"><div class="lbl">Réponse attendue (source: {e(r['source'])})</div>{e(r['expected'])}</div>
    <div class="{cls}"><div class="lbl">Réponse du modèle</div>{e(r['answer'])}
      <div class="cite">Citations : {cites}</div></div>
    {note}
  </div>
</div>""")

    doc = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<title>FSB Nexus — Test de 100 questions</title><style>{CSS}</style></head><body>
<div class="cover">
  <h1>FSB Nexus</h1>
  <div class="sub">Test du modèle sur 100 questions</div>
  <div class="sub" style="font-size:10pt">Question · Réponse du modèle · Réponse attendue</div>
  <div class="meta"><strong>Faculté des Sciences de Bizerte</strong> · Assistant IA / RAG<br>
  Généré le {d['generated'][:10]} · 100 questions fondées sur les documents officiels</div>
</div>

<h2>Résumé</h2>
<div class="kpi">
  <div><span class="v">{m['CORRECT']}/100</span><span class="l">Réponses correctes</span></div>
  <div><span class="v">{s['with_citations']}/{s['answered']}</span><span class="l">Réponses citées</span></div>
  <div><span class="v">{m['INCORRECT']}</span><span class="l">Erreur factuelle</span></div>
  <div><span class="v">{m['REFUS']}</span><span class="l">Refus</span></div>
</div>
<table class="sum">
  <tr><th>Verdict (revue manuelle)</th><th>Nombre</th><th>Signification</th></tr>
  <tr><td><strong>CORRECT</strong></td><td>{m['CORRECT']}</td><td>La réponse est conforme aux documents sources</td></tr>
  <tr><td><strong>INCOMPLET</strong></td><td>{m['INCOMPLET']}</td><td>Exacte mais partielle (#6 : un seul département cité sur six)</td></tr>
  <tr><td><strong>INCORRECT</strong></td><td>{m['INCORRECT']}</td><td>Contredit les documents (#55 : deux mastères confondus)</td></tr>
  <tr><td><strong>DISCUTABLE</strong></td><td>{m['DISCUTABLE']}</td><td>Ne répond pas vraiment à la question posée (#78)</td></tr>
  <tr><td><strong>CONFLIT</strong></td><td>{m['CONFLIT']}</td><td>La base contient deux sources contradictoires (#74, #75)</td></tr>
  <tr><td><strong>REFUS</strong></td><td>{m['REFUS']}</td><td>Le modèle a décliné alors que l'information existe</td></tr>
</table>

<div class="callout"><strong>Comment lire ce rapport.</strong> Chaque question montre la
<strong>réponse attendue</strong> (extraite des documents officiels de la FSB) puis la
<strong>réponse réelle du modèle</strong> avec ses citations. Les 100 questions portent
uniquement sur des informations réellement présentes dans la base documentaire — aucune
question piège. Chaque verdict a été <strong>vérifié à la main</strong>.</div>

<div class="callout warn"><strong>Pourquoi les verdicts sont manuels.</strong> Un score automatique
avait d'abord été calculé (présence des faits clés attendus dans la réponse). Il s'est révélé faux
<em>dans les deux sens</em> : il marquait « échec » des réponses correctes écrites autrement
(« 3 428 » vs « 3428 », « 12 septembre 2024 » vs « 12/09/2024 », « 4 mois » vs « quatre mois »),
et il a marqué « réussite » une réponse hors sujet (#78) sur un simple jeton commun. Il a donc été
écarté : <strong>les 100 réponses ont été relues une par une face à leurs documents sources</strong>.
Chaque question ci-après porte son verdict vérifié et sa justification.</div>

<h2>Analyse</h2>
<h3 style="color:#1a7a41">Ce qui fonctionne</h3>
<ul>
  <li><strong>80 réponses correctes sur les 85 fournies</strong>, et <strong>{s['with_citations']}/{s['answered']} portent une citation</strong> vers le document source.</li>
  <li><strong>Une seule erreur factuelle sur 100 questions</strong> (#55).</li>
  <li><strong>Aucune information inventée.</strong> Quand le modèle ne trouve pas, il refuse au lieu d'improviser — c'est le comportement voulu pour un assistant officiel.</li>
  <li>Le modèle restitue fidèlement des données précises : dates d'inscription, montants, postes téléphoniques, procédures en plusieurs étapes.</li>
</ul>

<h3 style="color:#b3261e">Les 15 refus : un seul document en cause</h3>
<p><strong>8 des 15 refus remontent au même fichier</strong> : <code>liste_des_coordinateurs</code>
(#54, #56–#60 directement, plus #45 et #53 qui en dépendent). L'information existe pourtant — ce
fichier contient les 22 coordinateurs — mais c'est un <strong>tableau compact en un seul bloc</strong>,
que la recherche retrouve mal. C'est exactement le problème déjà rencontré, et résolu, pour les licences.</p>
<div class="callout warn"><strong>Nuance importante :</strong> l'échec n'est pas systématique mais
<strong>instable</strong>. Sur le même document, #61 (coordinateur du MP EEA) a été
<strong>correctement répondu</strong>, tandis que #55 a produit la seule erreur factuelle du test en
confondant deux mastères voisins du même tableau. Un bloc unique et dense ne « disparaît » pas : il
devient imprévisible — parfois trouvé, parfois manqué, parfois confondu avec sa ligne voisine.</div>
<div class="callout"><strong>Correctif identifié :</strong> découper le tableau des coordinateurs en
fiches courtes (une par mastère), comme cela a été fait pour les licences — correctif qui avait fait
passer les questions « licence » du rang 11 au rang 1. Cela corrigerait d'un coup les 8 refus
<em>et</em> l'erreur #55. Les refus #3, #10 et #51 relèvent du même schéma : des fiches
en bloc unique (<code>dep_*</code>, <code>fsb_presentation_about</code>).</div>

<h3 style="color:#7c4dbd">Un problème de qualité des sources (#74, #75, #76, #80)</h3>
<p>La base contient un <strong>article de blog commercial</strong> (rédigé par une agence web) sur les
bourses, dont les montants <strong>contredisent le document officiel de l'Office des Œuvres
Universitaires</strong>. Interrogé, le modèle a cité les <strong>montants officiels de l'OOUN</strong> —
donc la source la plus fiable — et c'est la « réponse attendue » qui était tirée de l'article commercial.
<strong>Le modèle a eu raison contre notre référence.</strong></p>
<div class="callout warn"><strong>Recommandation :</strong> retirer cet article de la base documentaire.
Une source non officielle qui contredit un document ministériel est un risque : sur une autre question,
le modèle pourrait citer le mauvais chiffre en toute confiance.</div>

<h3>Limite connue</h3>
<p>Aucun document ne liste les six départements ensemble (#6) : l'information est éclatée entre les
fiches de chaque département. Une fiche de synthèse « départements de la FSB » corrigerait ce point.</p>

<div class="pagebreak"></div>

<div class="pagebreak"></div>
{''.join(body)}
</body></html>"""

    OUT_HTML.write_text(doc, encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={OUT_PDF}", OUT_HTML.as_uri()],
                   capture_output=True, timeout=180)
    print("HTML ->", OUT_HTML)
    print("PDF  ->", OUT_PDF, OUT_PDF.exists() and f"({OUT_PDF.stat().st_size} bytes)" or "FAILED")


if __name__ == "__main__":
    main()
