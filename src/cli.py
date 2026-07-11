"""Batch CLI: process a folder of PDFs, write per-doc JSON + summary report."""
import json
import sys
from pathlib import Path
import click
from dotenv import load_dotenv

load_dotenv()


@click.group()
def cli():
    pass


@cli.command()
@click.argument("folder", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", "-o", default="results", type=click.Path(path_type=Path),
              help="Directory to write output JSON files (default: results/)")
def process(folder: Path, output: Path):
    """Process all PDFs in FOLDER and write extracted JSON + summary report."""
    from src.pipeline import process_document

    pdfs = list(folder.glob("*.pdf"))
    if not pdfs:
        click.echo(f"No PDF files found in {folder}")
        sys.exit(1)

    output.mkdir(parents=True, exist_ok=True)
    summary: list[dict] = []

    click.echo(f"Processing {len(pdfs)} PDF(s) from {folder} → {output}\n")

    for pdf in sorted(pdfs):
        click.echo(f"  {pdf.name} ...", nl=False)
        try:
            result = process_document(pdf)
            status = "OK" if result["ok"] else f"FLAGGED ({len(result['flags'])} issue(s))"
            click.echo(f" {status}")

            out_data = {
                "path": result["path"],
                "doc_format": result["doc_format"],
                "doc_type": result["extracted"].get("doc_type"),
                "doc_number": result["extracted"].get("doc_number"),
                "flags": result["flags"],
                "ok": result["ok"],
                "extracted": result["extracted"],
            }
            out_path = output / (pdf.stem + ".json")
            out_path.write_text(json.dumps(out_data, indent=2, default=str), encoding="utf-8")

            summary.append({
                "file": pdf.name,
                "doc_type": out_data["doc_type"],
                "doc_number": out_data["doc_number"],
                "ok": out_data["ok"],
                "flags": out_data["flags"],
            })
        except Exception as exc:
            click.echo(f" ERROR: {exc}")
            summary.append({"file": pdf.name, "ok": False, "flags": [str(exc)]})

    summary_path = output / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    flagged = [s for s in summary if not s["ok"]]
    click.echo(f"\nDone. {len(pdfs) - len(flagged)}/{len(pdfs)} passed validation.")
    if flagged:
        click.echo(f"\nFlagged documents ({len(flagged)}):")
        for item in flagged:
            click.echo(f"  {item['file']}:")
            for flag in item.get("flags", []):
                click.echo(f"    - {flag}")

    click.echo(f"\nResults written to {output}/")


if __name__ == "__main__":
    cli()
