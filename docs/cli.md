# CLI Reference

The planned CLI command is:

```bash
securities
```

The CLI is organized around the package's public concepts. Universe operations
mirror `UniverseRegistry`; security and rule operations support resolver
inspection and configuration.

## Commands

```bash
securities universe create NAME --type TYPE
securities universe delete NAME
securities universe list
securities universe show NAME

securities universe add UNIVERSE SYMBOL --security-type TYPE
securities universe remove UNIVERSE SYMBOL
securities universe members UNIVERSE
securities universe contains UNIVERSE SYMBOL

securities universe resolve --include NAME --exclude NAME

securities security resolve SYMBOL --security-type TYPE

securities rules list
securities rules show OPTION_ROOT
securities rules validate PATH

securities store init
securities store info

securities import UNIVERSE PATH
securities export UNIVERSE PATH

securities doctor
```

## Examples

```bash
securities universe create restricted --type restricted
securities universe add restricted AAPL --security-type stock --reason "manual restriction"
securities universe members restricted
```

```bash
securities universe create sp500 --type index
securities universe add sp500 AAPL --security-type stock
securities universe resolve --include sp500 --exclude restricted
```

```bash
securities --db universe.db \
  --option-rules my_index_option_rules.yaml \
  universe add spx SPXW260619C06100000 --security-type option
```

```bash
securities security resolve SPXW260619C06100000 --security-type option --format json
```

```bash
securities rules validate my_index_option_rules.yaml
```

## Configuration

Global options:

- `--db PATH`
- `--option-rules PATH`
- `--format text|json`

The implementation should expose the final CLI entry point as `securities`.
