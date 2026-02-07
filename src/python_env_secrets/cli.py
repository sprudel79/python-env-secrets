"""
Command-line interface for python-env-secrets.

Usage::

    user-secrets init
    user-secrets set KEY VALUE
    user-secrets get KEY
    user-secrets list
    user-secrets delete KEY
    user-secrets clear
    user-secrets info
"""

import argparse
import sys
from pathlib import Path

from .manager import UserSecretsManager


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="user-secrets",
        description="Manage user secrets outside your project directory.",
    )
    parser.add_argument(
        "-p",
        "--project",
        type=Path,
        default=None,
        help="Project directory (defaults to current directory)",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialise user secrets for this project")
    sub.add_parser("list", help="List all stored secrets")
    sub.add_parser("info", help="Show configuration details")
    sub.add_parser("clear", help="Remove all secrets")

    p_set = sub.add_parser("set", help="Set a secret value")
    p_set.add_argument("key", help="Secret key")
    p_set.add_argument("value", help="Secret value")

    p_get = sub.add_parser("get", help="Get a secret value")
    p_get.add_argument("key", help="Secret key")

    p_del = sub.add_parser("delete", help="Delete a secret")
    p_del.add_argument("key", help="Secret key")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    manager = UserSecretsManager(project_dir=args.project, auto_init=True)

    if args.command == "init":
        uid = manager.user_secrets_id
        print(f"Initialised with USER_SECRETS_ID: {uid}")
        print(f"Secrets file: {manager.secrets_path}")

    elif args.command == "set":
        manager.set(args.key, args.value)
        print(f"Set secret: {args.key}")

    elif args.command == "get":
        value = manager.get(args.key)
        if value is None:
            print(f"Secret '{args.key}' not found.", file=sys.stderr)
            return 1
        print(value)

    elif args.command == "list":
        secrets = manager.list()
        if not secrets:
            print("No secrets stored.")
        else:
            for key, value in secrets.items():
                masked = value[:3] + "***" if len(value) > 3 else "***"
                print(f"  {key} = {masked}")

    elif args.command == "delete":
        if manager.delete(args.key):
            print(f"Deleted secret: {args.key}")
        else:
            print(f"Secret '{args.key}' not found.", file=sys.stderr)
            return 1

    elif args.command == "clear":
        count = manager.clear()
        print(f"Cleared {count} secret(s).")

    elif args.command == "info":
        info = manager.info()
        print(f"  Project directory : {info['project_dir']}")
        print(f"  .env file         : {info['env_file']}  (exists: {info['env_file_exists']})")
        print(f"  USER_SECRETS_ID   : {info['user_secrets_id']}")
        print(f"  Secrets file      : {info['secrets_file']}")
        print(f"  Secrets count     : {info['secrets_count']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
