import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from openapi_document import export_openapi_document


def main() -> None:
    repo_root = BACKEND_ROOT.parent
    output_path = repo_root / "docs" / "reference" / "openapi.json"
    destination = export_openapi_document(output_path)
    print(destination)


if __name__ == "__main__":
    main()
