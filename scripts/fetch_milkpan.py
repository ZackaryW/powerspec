"""Download the pinned milkpan for this platform, verify it, and print the executable path.

Used by CI for integration tests (export the path as MILKPAN_TEST_BINARY).
Usage: uv run python scripts/fetch_milkpan.py <directory>
"""
import sys
from pathlib import Path

from powerspec.milkpan_binary import MILKPAN, download, extract


def main(directory: str) -> None:
    target_dir = Path(directory).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    name, digest = MILKPAN.asset(MILKPAN.target())
    archive = target_dir / name
    download(f'{MILKPAN.download_base}/{MILKPAN.tag}/{name}', archive, digest)
    print(extract(archive, target_dir / 'extracted'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.milkpan-test')
