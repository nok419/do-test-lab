#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path
import sys


TEMPLATES = {
    "python-fastapi": "templates/python-fastapi",
    "node-express-ws": "templates/node-express-ws",
}


def cmd_new(args: argparse.Namespace) -> int:
    # 目的：
    # - 「テンプレをコピーして始める」を機械化して、運用コストとミスを減らします。
    here = Path(__file__).resolve().parent.parent
    src_rel = TEMPLATES.get(args.template)
    if not src_rel:
        print(f"unknown template: {args.template}", file=sys.stderr)
        return 2

    src = here / src_rel
    dst = Path(args.output).resolve()

    if dst.exists() and any(dst.iterdir()) and not args.force:
        print(f"output dir is not empty: {dst} (use --force to overwrite)", file=sys.stderr)
        return 2

    if dst.exists() and args.force:
        shutil.rmtree(dst)

    shutil.copytree(src, dst)
    print(f"created: {dst}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="labctl", description="Lab platform helper CLI (starter kit)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_new = sub.add_parser("new", help="create a new project from a template")
    p_new.add_argument("--template", required=True, choices=sorted(TEMPLATES.keys()))
    p_new.add_argument("--output", required=True, help="output directory")
    p_new.add_argument("--force", action="store_true", help="overwrite output directory if exists")
    p_new.set_defaults(func=cmd_new)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
