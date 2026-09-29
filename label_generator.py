#!/usr/bin/env python3
"""Generate printable label sheets from an Excel/CSV file using LaTeX."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd


def normalize_header(value: object) -> str:
    text = str(value).strip().lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def find_column(columns: list[str], aliases: list[str]) -> str | None:
    """Return the first matching column name for a list of aliases."""
    normalized = {normalize_header(name): name for name in columns}
    for alias in aliases:
        alias_norm = normalize_header(alias)
        for key, value in normalized.items():
            if alias_norm in key or key in alias_norm:
                return value
    return None


def read_labels(excel_path: Path | str) -> list[tuple[str, str, str]]:
    """Read labels from Excel or CSV file."""
    path = Path(excel_path)
    suffix = path.suffix.lower()

    if suffix in {".xlsx", ".xls", ".xlsm"}:
        df = pd.read_excel(path)
    elif suffix == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError("Format non supporté. Utilisez .xlsx, .xls ou .csv.")

    if df.empty:
        raise ValueError("Le fichier est vide.")

    cols = list(df.columns)

    box_col = find_column(cols, ["boîte", "boite", "box", "numero", "number"])
    start_col = find_column(cols, ["de", "from", "debut", "start"])
    end_col = find_column(cols, ["a", "to", "fin", "end"])

    if not box_col or not start_col or not end_col:
        if len(cols) >= 3:
            box_col, start_col, end_col = cols[0], cols[1], cols[2]
        else:
            raise ValueError(
                "Colonnes introuvables. Utilisez des noms comme : Boîte, De, À "
                "ou Box, From, To."
            )

    labels: list[tuple[str, str, str]] = []
    for _, row in df.iterrows():
        box = str(row.get(box_col, "")).strip()
        start = str(row.get(start_col, "")).strip()
        end = str(row.get(end_col, "")).strip()

        if not box:
            continue

        if not start:
            start = end
        if not end:
            end = start

        labels.append((box, start, end))

    if not labels:
        raise ValueError("Aucune étiquette n'a été détectée dans le fichier.")

    return labels


def render_latex(labels: list[tuple[str, str, str]], output_path: Path, top_margin: float = 2.0) -> None:
    """Generate LaTeX document with labels.
    
    Args:
        labels: List of (box, start, end) tuples
        output_path: Path to save the LaTeX file
        top_margin: Top margin in cm (default 2.0)
    """
    pages = [labels[i : i + 6] for i in range(0, len(labels), 6)]

    latex_lines = [
        r"\documentclass[11pt]{article}",
        r"\usepackage[a4paper,margin=0mm,top=" + f"{top_margin}cm" + r"]{geometry}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage[utf8]{inputenc}",
        r"\usepackage{helvet}",
        r"\renewcommand{\familydefault}{\sfdefault}",
        r"\usepackage{array}",
        r"\pagestyle{empty}",
        r"\setlength{\parindent}{0pt}",
        r"\setlength{\fboxsep}{3mm}",
        r"\setlength{\fboxrule}{0.5pt}",
        "",
        r"\newcommand{\labelcell}[3]{%",
        r"  \fbox{%",
        r"    \parbox[c][5.2cm][c]{0.42\textwidth}{%",
        r"      \centering",
        r"      \vspace{0.5cm}",
        r"      {\fontsize{22}{26}\selectfont \textbf{Boîte #1}}\\[0.9cm]",
        r"      {\fontsize{15}{18}\selectfont Dossiers de #2 à #3}\\[0.7cm]",
        r"      {\fontsize{12}{14}\selectfont Permis d'urbanisme --- Bouwvergunning}\\[0.5cm]",
        r"    }%",
        r"  }%",
        r"}",
        "",
        r"\begin{document}",
    ]

    for page_index, page in enumerate(pages):
        if page_index > 0:
            latex_lines.append(r"\newpage")

        latex_lines.append(r"\begin{center}")
        latex_lines.append(
            r"\begin{tabular}{@{}p{0.44\textwidth}p{0.44\textwidth}@{}}"
        )

        for i in range(0, len(page), 2):
            left = page[i]
            right = page[i + 1] if i + 1 < len(page) else None

            left_box = left[0]
            left_start = left[1]
            left_end = left[2]
            left_label = "\\labelcell{" + str(left_box) + "}{" + str(left_start) + "}{" + str(left_end) + "}"

            if right is not None:
                right_box = right[0]
                right_start = right[1]
                right_end = right[2]
                right_label = "\\labelcell{" + str(right_box) + "}{" + str(right_start) + "}{" + str(right_end) + "}"
                latex_lines.append(f"{left_label} & {right_label} \\\\[0.8cm]")
            else:
                latex_lines.append(f"{left_label} &  \\\\[0.8cm]")

        latex_lines.append(r"\end{tabular}")
        latex_lines.append(r"\end{center}")

    latex_lines.append(r"\end{document}")

    full_latex = "\n".join(latex_lines)
    output_path.write_text(full_latex, encoding="utf-8")
    print(f"Fichier LaTeX généré : {output_path}")


def compile_pdf(tex_path: Path) -> None:
    """Compile LaTeX file to PDF."""
    if not tex_path.exists():
        raise FileNotFoundError(f"Le fichier LaTeX n'existe pas : {tex_path}")

    try:
        subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                str(tex_path.name),
            ],
            cwd=str(tex_path.parent),
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"PDF généré : {tex_path.with_suffix('.pdf')}")
    except FileNotFoundError:
        raise RuntimeError(
            "pdflatex n'est pas installé ou n'est pas disponible dans le PATH."
        )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Génère des étiquettes LaTeX depuis un fichier Excel/CSV."
    )
    parser.add_argument(
        "input", help="Fichier Excel ou CSV contenant les étiquettes"
    )
    parser.add_argument(
        "-o", "--output", default="labels.tex", help="Nom du fichier LaTeX généré"
    )
    parser.add_argument(
        "--pdf", action="store_true", help="Compiler aussi en PDF (nécessite pdflatex)"
    )
    parser.add_argument(
        "--top-margin", type=float, default=2.0,
        help="Marge en haut de la page en cm (défaut: 2.0)"
    )

    args = parser.parse_args()

    try:
        labels = read_labels(args.input)
        render_latex(labels, Path(args.output), top_margin=args.top_margin)

        if args.pdf:
            try:
                compile_pdf(Path(args.output))
            except RuntimeError as exc:
                print(f"Attention : {exc}", file=sys.stderr)
                return 0

        return 0
    except Exception as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
