# label-generator

Outil en Python pour générer des étiquettes au format LaTeX à partir d'un fichier Excel ou CSV.

Les étiquettes sont conçues pour être imprimées sur du papier autocollant non acide avec un cadre visible pour faciliter de découpe. Le document produit est compatible avec LaTeX et peut être compilé vers PDF.

## Fonctionnalités

- Lecture d'un fichier Excel (.xlsx, .xls) ou CSV
- Import des colonnes de type :
  - Boîte / Box / Number
  - Début / Start / From
  - Fin / End / To
- Génération d'un document LaTeX avec 6 étiquettes par page A4 (2 colonnes x 3 rangées)
- Cadre visible autour de chaque étiquette pour découpage manuel
- Libellés centrés :
  - Boîte XXX
  - Dossiers de XXX à ZZZ
- Option facultative de compilation automatique en PDF si LaTeX est disponible

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

### Générer le fichier LaTeX

```bash
python label_generator.py examples/sample_labels.csv --output labels.tex
```

### Générer directement un PDF (si pdflatex est installé)

```bash
python label_generator.py examples/sample_labels.csv --output labels.pdf --pdf
```

### Spécifier les colonnes manuellement

```bash
python label_generator.py data.xlsx --box-column Box --start-column De --end-column A --output labels.tex
```

## Structure attendue du fichier Excel

Le fichier doit contenir des colonnes telles que :

| Box | De | A |
|-----|-----|---|
| 101 | 120 | 145 |
| 102 | 200 | 210 |
| 103 | 301 | 315 |

Les libellés générés seront :

- Boîte 101
- Dossiers de 120 à 145

## Modèle de visuel

Chaque étiquette est créée avec un cadre visible :

- 2 colonnes
- 3 lignes
- 6 étiquettes par page A4
- texte centré
- format prêt à l'impression sur support autocollant non acide

## Exemple fourni

Le dépôt contient un fichier d'exemple dans `examples/sample_labels.csv`.
