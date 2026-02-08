import json
from aircraft_design.server import app
from fastapi.openapi.utils import get_openapi


def export_openapi():
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    with open("openapi.json", "w") as f:
        json.dump(openapi_schema, f, indent=2)
    print("Exported openapi.json")


if __name__ == "__main__":
    export_openapi()
