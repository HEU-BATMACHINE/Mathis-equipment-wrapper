"""
Generate an HTML visualization of an equipment-wrapper ontology.

The script reads the generated ontology path and visualization output path
from config/wrapper.yaml.
"""

from pathlib import Path

import yaml

from fuseki.check_consistency import load_graph_limited_imports
from fuseki.visualize import KnowledgeGraph
from fuseki.visualize_v2 import build_graph, fetch_nodes


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPOSITORY_ROOT / "config" / "wrapper.yaml"


def load_wrapper_config(config_file: Path) -> dict:
    """
    Load and validate the equipment-wrapper configuration.

    Parameters
    ----------
    config_file:
        Path to the wrapper YAML configuration.

    Returns
    -------
    dict
        Parsed wrapper configuration.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    ValueError
        If required configuration sections or fields are missing.
    """
    if not config_file.is_file():
        raise FileNotFoundError(
            f"Wrapper configuration file does not exist: {config_file}"
        )

    with config_file.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError(
            f"Wrapper configuration must contain a YAML mapping: {config_file}"
        )

    files_config = config.get("files")

    if not isinstance(files_config, dict):
        raise ValueError(
            "The wrapper configuration must contain a 'files' section."
        )

    required_fields = {
        "generated_ontology",
        "visualization",
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


def create_visualization(
    ontology_file: Path,
    output_file: Path,
    max_import_layers: int = 4,
) -> None:
    """
    Generate an HTML visualization from an equipment-wrapper ontology.

    Parameters
    ----------
    ontology_file:
        Path to the generated Turtle ontology.

    output_file:
        Path where the HTML visualization will be written.

    max_import_layers:
        Maximum number of ontology import layers to load.

    Raises
    ------
    FileNotFoundError
        If the generated ontology does not exist.
    """
    if not ontology_file.is_file():
        raise FileNotFoundError(
            "Generated ontology does not exist. "
            f"Run generate_wrapper.py first: {ontology_file}"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    graph = load_graph_limited_imports(
        str(ontology_file),
        file_format="turtle",
        max_layers=max_import_layers,
    )

    print(f"Loaded graph has {len(graph)} triples.")

    # The visualization functions require a KnowledgeGraph object,
    # not an rdflib Graph object.
    knowledge_graph = KnowledgeGraph(graph=graph)

    nodes, edges = fetch_nodes(knowledge_graph)

    build_graph(
        nodes,
        edges,
        outfile=str(output_file),
    )

    print(f"Created visualization: {output_file}")


def main() -> None:
    """Generate the equipment-wrapper knowledge-graph visualization."""
    config = load_wrapper_config(CONFIG_FILE)

    files_config = config["files"]

    ontology_file = resolve_repository_path(
        files_config["generated_ontology"]
    )
    output_file = resolve_repository_path(
        files_config["visualization"]
    )

    create_visualization(
        ontology_file=ontology_file,
        output_file=output_file,
    )


if __name__ == "__main__":
    main()