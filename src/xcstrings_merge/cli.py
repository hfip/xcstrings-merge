"""Command line interface for xcstrings-merge."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional

from . import __version__
from .catalog import MergeError, load_catalog, merge, write_catalog
from .strings import load_strings

GREEN = "32"
RED = "31"
YELLOW = "33"
DIM = "2"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xcm",
        description="Merge legacy .strings translations into an Xcode String Catalog.",
    )
    subparsers = parser.add_subparsers(dest="command")
    merge_parser = subparsers.add_parser("merge", help="merge a .strings file into a catalog")
    merge_parser.add_argument("catalog", help="path to Localizable.xcstrings")
    merge_parser.add_argument("strings", help="path to Localizable.strings")
    merge_parser.add_argument("--lang", required=True, help="language code of the .strings file")
    merge_parser.add_argument(
        "--write", action="store_true", help="write the result (default: dry run)"
    )
    merge_parser.add_argument(
        "--overwrite", action="store_true", help="replace existing translations"
    )
    merge_parser.add_argument(
        "--add-new", action="store_true", help="insert keys missing from the catalog"
    )
    merge_parser.add_argument("--sort", action="store_true", help="sort keys alphabetically")
    merge_parser.add_argument("--no-backup", action="store_true")
    merge_parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "-V", "--version", action="version", version="xcstrings-merge " + __version__
    )
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command != "merge":
        parser.print_help()
        return 2

    catalog_path = Path(args.catalog)
    strings_path = Path(args.strings)
    try:
        payload = load_catalog(catalog_path)
        translations = load_strings(str(strings_path))
    except (MergeError, OSError) as error:
        print("error: %s" % error, file=sys.stderr)
        return 2

    report = merge(
        payload,
        translations,
        args.lang,
        overwrite=args.overwrite,
        add_new=args.add_new,
    )

    if args.write:
        if not args.no_backup:
            shutil.copy2(catalog_path, catalog_path.with_name(catalog_path.name + ".bak"))
        write_catalog(payload, catalog_path, sort_keys=args.sort)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return 0

    print("%s · %s" % (catalog_path.name, args.lang))
    print("  filled     %d" % report.filled)
    print("  added      %d" % report.added)
    print("  replaced   %d" % report.replaced)
    print("  unchanged  %d" % report.unchanged)
    if report.conflicts:
        print("  conflicts  %d (existing translations; use --overwrite)" % len(report.conflicts))
        for key in report.conflicts[:10]:
            print("               %s" % key)
    if report.unknown_keys:
        print("  unknown    %d keys not in the catalog (use --add-new)" % len(report.unknown_keys))
        for key in report.unknown_keys[:10]:
            print("               %s" % key)
    print("  coverage   %.0f%%" % report.coverage)
    print()
    print("dry run." if not args.write else "written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
