"""Command line interface for security-universes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from pydantic import BaseModel

from security_universes.exceptions import SecurityUniversesError
from security_universes.models import Security, SecurityType
from security_universes.registry import UniverseRegistry
from security_universes.resolvers import OCCSecurityIdResolver, load_default_option_rules
from security_universes.stores import SQLiteUniverseStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="securities")
    parser.add_argument("--db", default="security-universes.db", help="SQLite database path")
    parser.add_argument("--option-rules", help="YAML option-root rule override path")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    commands = parser.add_subparsers(dest="command", required=True)

    universe = commands.add_parser("universe", help="Manage universes")
    universe_commands = universe.add_subparsers(dest="universe_command", required=True)

    universe_create = universe_commands.add_parser("create")
    universe_create.add_argument("name")
    universe_create.add_argument("--type", default="custom")
    universe_create.add_argument("--description")

    universe_delete = universe_commands.add_parser("delete")
    universe_delete.add_argument("name")

    universe_commands.add_parser("list")

    universe_show = universe_commands.add_parser("show")
    universe_show.add_argument("name")

    universe_add = universe_commands.add_parser("add")
    universe_add.add_argument("universe")
    universe_add.add_argument("symbol")
    universe_add.add_argument("--security-type", default="unknown")
    universe_add.add_argument("--weight")
    universe_add.add_argument("--source")
    universe_add.add_argument("--reason")
    universe_add.add_argument("--added-by")

    universe_remove = universe_commands.add_parser("remove")
    universe_remove.add_argument("universe")
    universe_remove.add_argument("symbol")

    universe_members = universe_commands.add_parser("members")
    universe_members.add_argument("universe")
    universe_members.add_argument("--all", action="store_true")

    universe_contains = universe_commands.add_parser("contains")
    universe_contains.add_argument("universe")
    universe_contains.add_argument("symbol")

    universe_resolve = universe_commands.add_parser("resolve")
    universe_resolve.add_argument("--include", action="append", required=True)
    universe_resolve.add_argument("--exclude", action="append")

    security = commands.add_parser("security", help="Inspect securities")
    security_commands = security.add_subparsers(dest="security_command", required=True)
    security_resolve = security_commands.add_parser("resolve")
    security_resolve.add_argument("symbol")
    security_resolve.add_argument("--security-type", default="unknown")

    rules = commands.add_parser("rules", help="Inspect option-root rules")
    rules_commands = rules.add_subparsers(dest="rules_command", required=True)
    rules_commands.add_parser("list")
    rules_show = rules_commands.add_parser("show")
    rules_show.add_argument("option_root")
    rules_validate = rules_commands.add_parser("validate")
    rules_validate.add_argument("path")

    store = commands.add_parser("store", help="Manage local storage")
    store_commands = store.add_subparsers(dest="store_command", required=True)
    store_commands.add_parser("init")
    store_commands.add_parser("info")

    import_command = commands.add_parser("import", help="Import universe members")
    import_command.add_argument("universe")
    import_command.add_argument("path")

    export_command = commands.add_parser("export", help="Export universe members")
    export_command.add_argument("universe")
    export_command.add_argument("path")
    export_command.add_argument("--all", action="store_true")

    commands.add_parser("doctor", help="Check local configuration")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = dispatch(args)
    except (SecurityUniversesError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print_result(result, output_format=args.format)
    return 0


def dispatch(args: argparse.Namespace) -> Any:
    if args.command == "universe":
        return dispatch_universe(args)
    if args.command == "security":
        return dispatch_security(args)
    if args.command == "rules":
        return dispatch_rules(args)
    if args.command == "store":
        return dispatch_store(args)
    if args.command == "import":
        return dispatch_import(args)
    if args.command == "export":
        return dispatch_export(args)
    if args.command == "doctor":
        SQLiteUniverseStore(args.db).close()
        return {"ok": True, "db": args.db}
    raise ValueError(f"Unknown command: {args.command}")


def dispatch_universe(args: argparse.Namespace) -> Any:
    registry = build_registry(
        args,
        use_resolver=(
            args.universe_command == "add"
            and SecurityType(args.security_type) == SecurityType.OPTION
        ),
    )

    if args.universe_command == "create":
        return registry.create_universe(
            args.name,
            universe_type=args.type,
            description=args.description,
        )
    if args.universe_command == "delete":
        registry.delete_universe(args.name)
        return {"deleted": args.name}
    if args.universe_command == "list":
        return registry.list_universes()
    if args.universe_command == "show":
        universe = registry.get_universe(args.name)
        if universe is None:
            raise ValueError(f"Universe not found: {args.name}")
        return universe
    if args.universe_command == "add":
        return registry.add_member(
            args.universe,
            args.symbol,
            security_type=args.security_type,
            weight=args.weight,
            source=args.source,
            reason=args.reason,
            added_by=args.added_by,
        )
    if args.universe_command == "remove":
        registry.remove_member(args.universe, args.symbol)
        return {"removed": args.symbol, "universe": args.universe}
    if args.universe_command == "members":
        return registry.list_members(args.universe, active_only=not args.all)
    if args.universe_command == "contains":
        return {"contains": registry.contains(args.universe, args.symbol)}
    if args.universe_command == "resolve":
        return registry.resolve(include=args.include, exclude=args.exclude)
    raise ValueError(f"Unknown universe command: {args.universe_command}")


def dispatch_security(args: argparse.Namespace) -> Any:
    security = Security(symbol=args.symbol, security_type=SecurityType(args.security_type))
    if security.security_type == SecurityType.OPTION:
        return build_resolver(args).resolve(security)
    return security


def dispatch_rules(args: argparse.Namespace) -> Any:
    if args.rules_command == "list":
        return sorted(load_default_option_rules())
    if args.rules_command == "show":
        root = args.option_root.upper()
        rules = load_default_option_rules()
        if root not in rules:
            raise ValueError(f"Option-root rule not found: {root}")
        return {root: rules[root]}
    if args.rules_command == "validate":
        resolver = OCCSecurityIdResolver.from_yaml(args.path, include_defaults=False)
        return {"valid": True, "rules": sorted(resolver.option_rules)}
    raise ValueError(f"Unknown rules command: {args.rules_command}")


def dispatch_store(args: argparse.Namespace) -> Any:
    store = SQLiteUniverseStore(args.db)
    store.close()
    if args.store_command == "init":
        return {"initialized": args.db}
    if args.store_command == "info":
        return {"db": str(Path(args.db)), "exists": Path(args.db).exists()}
    raise ValueError(f"Unknown store command: {args.store_command}")


def dispatch_import(args: argparse.Namespace) -> Any:
    registry = build_registry(args, use_resolver=True)
    members = registry.import_members(args.universe, args.path)
    return {"imported": len(members), "universe": args.universe}


def dispatch_export(args: argparse.Namespace) -> Any:
    registry = build_registry(args)
    members = registry.export_members(args.universe, args.path, active_only=not args.all)
    return {"exported": len(members), "path": args.path, "universe": args.universe}


def build_registry(
    args: argparse.Namespace,
    *,
    use_resolver: bool = False,
) -> UniverseRegistry:
    resolver = build_resolver(args) if use_resolver else None
    return UniverseRegistry.sqlite(args.db, security_id_resolver=resolver)


def build_resolver(args: argparse.Namespace) -> OCCSecurityIdResolver:
    if args.option_rules:
        return OCCSecurityIdResolver.from_yaml(args.option_rules)
    return OCCSecurityIdResolver.default()


def print_result(result: Any, *, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))
        return

    if isinstance(result, list):
        for item in result:
            print(format_text(item))
        return
    print(format_text(result))


def format_text(value: Any) -> str:
    if isinstance(value, BaseModel):
        if isinstance(value, Security):
            return value.display_name
        name = getattr(value, "name", None)
        if name:
            return str(name)
        symbol = getattr(getattr(value, "security", None), "symbol", None)
        if symbol:
            return str(symbol)
        return json.dumps(to_jsonable(value), sort_keys=True)
    if isinstance(value, dict):
        return json.dumps(to_jsonable(value), sort_keys=True)
    return str(value)


def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
