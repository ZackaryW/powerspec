"""Rewrite Powerspec's milkpan pin from a release's SHA256SUMS.

Usage: uv run python scripts/pin_milkpan.py v0.2.0
"""
import re
import sys
import urllib.request
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'src' / 'powerspec' / 'milkpan_binary.py'


def main(tag: str) -> None:
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        sys.exit('usage: pin_milkpan.py vX.Y.Z')
    url = f'https://github.com/ZackaryW/milkpan/releases/download/{tag}/SHA256SUMS'
    with urllib.request.urlopen(url, timeout=60) as response:
        sums = response.read().decode()
    entries = []
    for line in sums.splitlines():
        digest, name = line.split()
        if not re.fullmatch(r'[0-9a-f]{64}', digest):
            sys.exit(f'bad digest line: {line}')
        entries.append(f"    '{name}': '{digest}',")
    if len(entries) != 4:
        sys.exit(f'expected 4 assets, found {len(entries)}')
    block = f"MILKPAN = Release(tag='{tag}', digests={{\n" + '\n'.join(sorted(entries)) + '\n})'
    text = MODULE.read_text(encoding='utf-8')
    updated, count = re.subn(r"MILKPAN = Release\(tag='v[^']+', digests=\{\n.*?\n\}\)", lambda _: block, text, flags=re.S)
    if count != 1:
        sys.exit('could not find the MILKPAN pin')
    MODULE.write_text(updated, encoding='utf-8')
    print(f'pinned milkpan {tag}; also update SUPPORTED_LINES if the release line changed')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '')
