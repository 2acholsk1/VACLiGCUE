import os
from pathlib import Path
import subprocess
import click

@click.command()
@click.argument('folder', type=click.Path(exists=True, file_okay=False))
def extract_exif(folder):
    folder = Path(folder)
    script_path = folder / "run_exif_extraction.sh"

    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write("cd \"" + str(folder) + "\"\n")
        f.write("for img in *.JPG; do\n")
        f.write("    exiftool \"$img\" > \"meta_${img%.JPG}.txt\"\n")
        f.write("done\n")

    os.chmod(script_path, 0o755)
    click.echo(f"GENERATED SCRIPT: {script_path}")

    subprocess.run([str(script_path)], shell=True)
    click.echo("EXIF GENERATED")

if __name__ == "__main__":
    extract_exif()
