"""Garante a regra de dependência do DDD: as setas sempre apontam para o domínio."""

import ast
from pathlib import Path

import pytest

import salacerta

PACKAGE_ROOT = Path(salacerta.__file__).parent

FORBIDDEN = {
    "domain": (
        "salacerta.application",
        "salacerta.infrastructure",
        "salacerta.api",
        "fastapi",
        "sqlalchemy",
        "pydantic",
    ),
    "application": ("salacerta.infrastructure", "salacerta.api", "fastapi", "sqlalchemy"),
    "infrastructure": ("salacerta.api", "fastapi"),
}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


@pytest.mark.parametrize("layer", FORBIDDEN)
def test_layer_respects_dependency_rule(layer: str) -> None:
    files = list((PACKAGE_ROOT / layer).rglob("*.py"))
    assert files

    violations = [
        f"{path.name} importa {module}"
        for path in files
        for module in imported_modules(path)
        if any(module == bad or module.startswith(f"{bad}.") for bad in FORBIDDEN[layer])
    ]
    assert violations == []
