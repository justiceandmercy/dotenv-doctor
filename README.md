# dotenv-doctor

A small command-line tool that lints `.env` files for common mistakes and drift from `.env.example`.

## Features

- Detects duplicate keys
- Finds keys missing from `.env` but present in `.env.example`
- Reports undocumented keys
- Flags empty values and obvious placeholder values
- Supports multiple env files and JSON output
- Uses only the Python standard library

## Install

```bash
pip install -e .
```

## Usage

Lint the default `.env` against `.env.example`:

```bash
dotenv-doctor
```

Lint several files:

```bash
dotenv-doctor .env .env.local --example .env.example
```

Treat warnings as errors:

```bash
dotenv-doctor --strict
```

Emit JSON:

```bash
dotenv-doctor --json
```

## Exit codes

- `0`: no errors
- `1`: one or more errors (or warnings with `--strict`)
- `2`: usage or file error

## License

MIT
