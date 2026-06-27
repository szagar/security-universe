import json

from security_universe.cli import main


def test_cli_store_init(tmp_path, capsys) -> None:
    db = tmp_path / "universe.db"

    exit_code = main(["--db", str(db), "store", "init"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert db.exists()
    assert "initialized" in output


def test_cli_universe_create_add_members_json(tmp_path, capsys) -> None:
    db = tmp_path / "universe.db"

    assert main(["--db", str(db), "universe", "create", "restricted", "--type", "restricted"]) == 0
    assert (
        main(
            [
                "--db",
                str(db),
                "universe",
                "add",
                "restricted",
                "AAPL",
                "--security-type",
                "stock",
                "--reason",
                "manual restriction",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert (
        main(
            [
                "--db",
                str(db),
                "--format",
                "json",
                "universe",
                "members",
                "restricted",
            ]
        )
        == 0
    )

    members = json.loads(capsys.readouterr().out)
    assert members[0]["security"]["symbol"] == "AAPL"
    assert members[0]["reason"] == "manual restriction"


def test_cli_universe_resolve_include_exclude(tmp_path, capsys) -> None:
    db = tmp_path / "universe.db"
    assert main(["--db", str(db), "universe", "create", "sp500", "--type", "index"]) == 0
    assert (
        main(["--db", str(db), "universe", "create", "restricted", "--type", "restricted"])
        == 0
    )
    assert main(["--db", str(db), "universe", "add", "sp500", "AAPL"]) == 0
    assert main(["--db", str(db), "universe", "add", "sp500", "MSFT"]) == 0
    assert main(["--db", str(db), "universe", "add", "restricted", "AAPL"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "--db",
                str(db),
                "--format",
                "json",
                "universe",
                "resolve",
                "--include",
                "sp500",
                "--exclude",
                "restricted",
            ]
        )
        == 0
    )

    securities = json.loads(capsys.readouterr().out)
    assert [security["symbol"] for security in securities] == ["MSFT"]


def test_cli_security_resolve_occ_json(capsys) -> None:
    assert (
        main(
            [
                "--format",
                "json",
                "security",
                "resolve",
                "SPXW260619C06100000",
                "--security-type",
                "option",
            ]
        )
        == 0
    )

    security = json.loads(capsys.readouterr().out)
    assert security["security_id"] == "option:SPXW:2026-06-19:call:6100"
    assert security["underlying"] == "SPX"


def test_cli_rules_validate(tmp_path, capsys) -> None:
    rules = tmp_path / "rules.yaml"
    rules.write_text(
        "\n".join(
            [
                "TEST:",
                "  underlying: TEST",
                "  expiration_session: pm",
                "  settlement_type: cash",
            ]
        ),
        encoding="utf-8",
    )

    assert main(["--format", "json", "rules", "validate", str(rules)]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output == {"rules": ["TEST"], "valid": True}


def test_cli_import_export_json(tmp_path, capsys) -> None:
    db = tmp_path / "universe.db"
    import_path = tmp_path / "members.json"
    export_path = tmp_path / "exported.json"
    import_path.write_text(
        json.dumps(
            [
                {
                    "security": {"symbol": "AAPL", "security_type": "stock"},
                    "reason": "manual restriction",
                }
            ]
        ),
        encoding="utf-8",
    )

    assert main(["--db", str(db), "universe", "create", "restricted"]) == 0
    assert main(["--db", str(db), "import", "restricted", str(import_path)]) == 0
    assert main(["--db", str(db), "export", "restricted", str(export_path)]) == 0

    capsys.readouterr()
    exported = json.loads(export_path.read_text(encoding="utf-8"))
    assert exported[0]["security"]["symbol"] == "AAPL"
    assert exported[0]["reason"] == "manual restriction"
