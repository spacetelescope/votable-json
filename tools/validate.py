"""Validate JSON VOTable documents against schema/votable.schema.json."""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "votable.schema.json"


def main(paths):
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    failed = 0
    for path in paths:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        errors = list(validator.iter_errors(doc))
        print(f"{'FAIL' if errors else 'OK  '} {path}")
        for err in errors:
            print(f"     {'/'.join(map(str, err.absolute_path))}: {err.message}")
        failed += bool(errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
