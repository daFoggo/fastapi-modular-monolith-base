import ast
import importlib
import inspect
from collections import defaultdict
from pathlib import Path

from app.common import BaseModel

ROOT = Path(__file__).resolve().parents[1]
MODULES_ROOT = ROOT / "app" / "modules"

LAYER_ALLOWED_IMPORTS = {
    "models": set(),
    "repositories": {"models"},
    "services": {"models", "repositories", "schemas"},
    "schemas": set(),
    "routes": {"dependencies", "models", "schemas", "services"},
}


def _feature_modules() -> dict[str, Path]:
    return {
        path.name: path
        for path in MODULES_ROOT.iterdir()
        if path.is_dir() and (path / "__init__.py").exists()
    }


def _python_files(module_path: Path) -> list[Path]:
    return sorted(
        path for path in module_path.rglob("*.py") if "__pycache__" not in path.parts
    )


def _source_layer(path: Path, module_path: Path) -> str | None:
    relative_parts = path.relative_to(module_path).parts
    return relative_parts[0] if len(relative_parts) > 1 else None


def _module_package(path: Path) -> list[str]:
    relative = path.relative_to(ROOT).with_suffix("")
    parts = list(relative.parts)
    return parts[:-1]


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.level:
                package = _module_package(path)
                parent = package[: len(package) - node.level + 1]
                imports.append(".".join([*parent, *node.module.split(".")]))
            else:
                imports.append(node.module)
    return imports


def _module_import_target(import_name: str) -> tuple[str, list[str]] | None:
    parts = import_name.split(".")
    if len(parts) < 3 or parts[:2] != ["app", "modules"]:
        return None
    return parts[2], parts[3:]


def _service_dependency_graph() -> dict[str, set[str]]:
    modules = _feature_modules()
    graph: dict[str, set[str]] = defaultdict(set)
    for source_module, module_path in modules.items():
        service_path = module_path / "services"
        if not service_path.exists():
            continue
        for path in _python_files(service_path):
            for import_name in _imports(path):
                target = _module_import_target(import_name)
                if target and target[0] != source_module:
                    graph[source_module].add(target[0])
    return graph


def _find_cycle(graph: dict[str, set[str]]) -> list[str] | None:
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            start = visiting.index(node)
            return [*visiting[start:], node]
        if node in visited:
            return None

        visiting.append(node)
        for dependency in graph.get(node, set()):
            cycle = visit(dependency)
            if cycle:
                return cycle
        visiting.pop()
        visited.add(node)
        return None

    for node in graph:
        cycle = visit(node)
        if cycle:
            return cycle
    return None


def _all_model_classes() -> set[type[BaseModel]]:
    discovered: set[type[BaseModel]] = set()
    pending = list(BaseModel.__subclasses__())
    while pending:
        model = pending.pop()
        pending.extend(model.__subclasses__())
        if not inspect.isabstract(model):
            discovered.add(model)
    return discovered


def test_every_feature_module_declares_a_valid_public_api() -> None:
    for module_name in _feature_modules():
        package = importlib.import_module(f"app.modules.{module_name}")
        public_api = getattr(package, "__all__", None)

        assert isinstance(public_api, list), (
            f"app.modules.{module_name} must declare __all__ as a list"
        )
        assert len(public_api) == len(set(public_api)), (
            f"app.modules.{module_name} contains duplicate __all__ entries"
        )
        missing = [name for name in public_api if not hasattr(package, name)]
        assert not missing, (
            f"app.modules.{module_name} exports missing symbols: {missing}"
        )


def test_cross_module_imports_use_the_target_public_api() -> None:
    violations: list[str] = []
    for source_module, module_path in _feature_modules().items():
        for path in _python_files(module_path):
            if path == module_path / "__init__.py":
                continue
            for import_name in _imports(path):
                target = _module_import_target(import_name)
                if not target or target[0] == source_module:
                    continue
                target_module, internal_path = target
                if internal_path:
                    relative_path = path.relative_to(ROOT)
                    violations.append(
                        f"{relative_path}: import {import_name}; use "
                        f"'app.modules.{target_module}' instead"
                    )

    assert not violations, "Cross-module private imports found:\n" + "\n".join(
        violations
    )


def test_internal_imports_follow_layer_direction() -> None:
    violations: list[str] = []
    for module_name, module_path in _feature_modules().items():
        for path in _python_files(module_path):
            source_layer = _source_layer(path, module_path)
            if source_layer not in LAYER_ALLOWED_IMPORTS:
                continue

            for import_name in _imports(path):
                target = _module_import_target(import_name)
                if not target or target[0] != module_name or not target[1]:
                    continue

                target_layer = target[1][0]
                if (
                    target_layer in LAYER_ALLOWED_IMPORTS
                    and target_layer != source_layer
                    and target_layer not in LAYER_ALLOWED_IMPORTS[source_layer]
                ):
                    relative_path = path.relative_to(ROOT)
                    violations.append(
                        f"{relative_path}: {source_layer} imports {target_layer} "
                        f"through {import_name}"
                    )

    assert not violations, "Layer direction violations found:\n" + "\n".join(violations)


def test_service_dependency_graph_is_acyclic() -> None:
    graph = _service_dependency_graph()
    cycle = _find_cycle(graph)
    assert cycle is None, f"Cross-module service dependency cycle: {' -> '.join(cycle)}"


def test_all_discovered_models_are_registered_in_metadata() -> None:
    for module_path in _feature_modules().values():
        models_path = module_path / "models"
        if not models_path.exists():
            continue
        for path in _python_files(models_path):
            relative = path.relative_to(ROOT).with_suffix("")
            importlib.import_module(".".join(relative.parts))

    model_tables = {model.__tablename__ for model in _all_model_classes()}
    metadata_tables = set(BaseModel.metadata.tables)

    assert model_tables == metadata_tables, (
        "SQLAlchemy model/metadata mismatch: "
        f"models={sorted(model_tables)}, metadata={sorted(metadata_tables)}"
    )
