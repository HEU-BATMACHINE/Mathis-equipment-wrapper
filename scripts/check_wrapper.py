"""
Check the consistency of an equipment wrapper.

The script verifies that the device individuals and ontology properties
referenced in config/channels.csv are present in the equipment ontology
or one of its imported ontologies.

Configuration and file paths are read from config/wrapper.yaml.
"""

from pathlib import Path
from typing import Any

import yaml

from fuseki.check_consistency import (
    check_individuals_in_graph,
    check_properties_in_graph,
    get_list_individuals_from_csv,
    get_list_properties_from_csv,
    load_graph_limited_imports,
)


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPOSITORY_ROOT / "config" / "wrapper.yaml"


def load_wrapper_config(config_file: Path) -> dict[str, Any]:
    """
    Load and validate the equipment-wrapper configuration.

    Parameters
    ----------
    config_file:
        Path to config/wrapper.yaml.

    Returns
    -------
    dict[str, Any]
        Parsed wrapper configuration.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.

    ValueError
        If the configuration is invalid or required fields are missing.
    """
    if not config_file.is_file():
        raise FileNotFoundError(
            f"Wrapper configuration does not exist: {config_file}"
        )

    with config_file.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(
            "Wrapper configuration must contain a YAML mapping."
        )

    files_config = config.get("files")

    if not isinstance(files_config, dict):
        raise ValueError(
            "Wrapper configuration must contain a 'files' section."
        )

    required_fields = {
        "channels",
        "individuals",
    }

    missing_fields = required_fields - files_config.keys()

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(
            f"Missing required fields in the 'files' section: {missing}"
        )

    return config


def resolve_repository_path(path_value: str) -> Path:
    """
    Resolve a configured path relative to the repository root.

    Absolute paths are preserved.

    Parameters
    ----------
    path_value:
        Absolute path or path relative to the repository root.

    Returns
    -------
    Path
        Resolved filesystem path.
    """
    path = Path(path_value)

    if path.is_absolute():
        return path

    return REPOSITORY_ROOT / path


def print_missing_items(
    heading: str,
    items: list[str],
) -> None:
    """
    Print a collection of missing ontology resources.

    Parameters
    ----------
    heading:
        Heading displayed before the items.

    items:
        Missing resource identifiers.
    """
    print(heading)

    for item in items:
        print(f" - {item}")


def main() -> None:
    """Run the equipment-wrapper consistency checks."""
    config = load_wrapper_config(CONFIG_FILE)
    files_config = config["files"]

    channels_file = resolve_repository_path(
        files_config["channels"]
    )
    individuals_file = resolve_repository_path(
        files_config["individuals"]
    )

    if not channels_file.is_file():
        raise FileNotFoundError(
            f"Channel configuration does not exist: {channels_file}"
        )

    if not individuals_file.is_file():
        raise FileNotFoundError(
            f"Equipment-individuals ontology does not exist: "
            f"{individuals_file}"
        )

    max_import_layers = (
        config.get("validation", {}).get("max_import_layers", 4)
    )

    graph = load_graph_limited_imports(
        str(individuals_file),
        file_format="turtle",
        max_layers=max_import_layers,
    )

    print(f"Loaded graph has {len(graph)} triples.")

    individuals = get_list_individuals_from_csv(
        channels_file,
        sep=";",
    )

    missing_individuals = check_individuals_in_graph(
        graph,
        individuals,
    )

    properties = get_list_properties_from_csv(
        channels_file,
        sep=";",
    )

    missing_properties = check_properties_in_graph(
        graph,
        properties,
    )

    print()

    if missing_individuals:
        print_missing_items(
            "Missing equipment individuals:",
            missing_individuals,
        )
    else:
        print(
            "All equipment individuals referenced in channels.csv "
            "are present in the ontology graph."
        )

    print()

    if missing_properties:
        print_missing_items(
            "Missing ontology properties:",
            missing_properties,
        )
    else:
        print(
            "All ontology properties referenced in channels.csv "
            "are present in the ontology graph."
        )

    if missing_individuals or missing_properties:
        print()
        print("Equipment-wrapper consistency check failed.")
        raise SystemExit(1)

    print()
    print("Equipment-wrapper consistency check passed.")


if __name__ == "__main__":
    main()