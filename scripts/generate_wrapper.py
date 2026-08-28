"""
Generate the semantic and deployment resources for an equipment wrapper.

The script reads:

- config/wrapper.yaml
- config/channels.csv

It generates:

- generated/table_channels_<equipment>.ttl
- generated/nodelist.csv
- generated/init.sql

Equipment-specific values must be defined in config/wrapper.yaml or
config/channels.csv. This script should not contain equipment-specific
namespaces or identifiers.
"""

from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from rdflib import Graph


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPOSITORY_ROOT / "config" / "wrapper.yaml"

REQUIRED_CHANNEL_COLUMNS = {
    "ns",
    "label",
    "name",
    "category",
    "device",
    "property",
    "unit",
    "type",
}

SUPPORTED_CATEGORIES = {
    "measurement",
    "control",
}

NODELIST_TYPES = {
    "REAL": "float64",
    "INT": "int",
}

SQL_TYPES = {
    "float64": "REAL",
    "int": "INT",
}


def load_wrapper_config(config_file: Path) -> dict[str, Any]:
    """
    Load and validate the wrapper YAML configuration.

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
        If required configuration sections or values are missing.
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

    required_sections = {
        "wrapper",
        "ontology",
        "files",
        "semantic_model",
    }

    missing_sections = required_sections - config.keys()

    if missing_sections:
        missing = ", ".join(sorted(missing_sections))
        raise ValueError(
            f"Missing required configuration sections: {missing}"
        )

    validate_config_section(
        config=config,
        section="wrapper",
        required_fields={
            "identifier",
            "name",
            "description",
        },
    )

    validate_config_section(
        config=config,
        section="ontology",
        required_fields={
            "channel_prefix",
            "channel_namespace",
            "channel_ontology_iri",
            "individuals_prefix",
            "individuals_namespace",
            "individuals_ontology_iri",
            "domain_prefix",
            "domain_namespace",
            "domain_ontology_iri",
        },
    )

    validate_config_section(
        config=config,
        section="files",
        required_fields={
            "channels",
            "individuals",
            "generated_ontology",
            "nodelist",
            "database_schema",
            "visualization",
        },
    )

    validate_config_section(
        config=config,
        section="semantic_model",
        required_fields={
            "measurement_channel_class",
            "control_channel_class",
            "measurement_process_class",
            "control_process_class",
            "measurement_device_property",
            "control_device_property",
            "measurement_output_property",
            "control_input_property",
            "timestamp_property",
            "unit_property",
        },
    )

    return config


def validate_config_section(
    config: dict[str, Any],
    section: str,
    required_fields: set[str],
) -> None:
    """
    Validate that a configuration section contains all required fields.

    Parameters
    ----------
    config:
        Parsed wrapper configuration.

    section:
        Name of the configuration section.

    required_fields:
        Fields required in the section.

    Raises
    ------
    ValueError
        If the section is invalid or required fields are missing.
    """
    section_config = config.get(section)

    if not isinstance(section_config, dict):
        raise ValueError(
            f"The wrapper configuration section '{section}' "
            "must contain a YAML mapping."
        )

    missing_fields = required_fields - section_config.keys()

    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(
            f"Missing required fields in '{section}': {missing}"
        )

    empty_fields = [
        field
        for field in required_fields
        if section_config.get(field) is None
        or str(section_config.get(field)).strip() == ""
    ]

    if empty_fields:
        empty = ", ".join(sorted(empty_fields))
        raise ValueError(
            f"Empty required fields in '{section}': {empty}"
        )


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


def load_channels(csv_file: Path) -> pd.DataFrame:
    """
    Load and validate the channel configuration.

    Parameters
    ----------
    csv_file:
        Path to the semicolon-separated channel configuration.

    Returns
    -------
    pandas.DataFrame
        Validated channel configuration.

    Raises
    ------
    FileNotFoundError
        If the channel configuration does not exist.

    ValueError
        If required columns or supported values are missing.
    """
    if not csv_file.is_file():
        raise FileNotFoundError(
            f"Channel configuration file does not exist: {csv_file}"
        )

    dataframe = pd.read_csv(
        filepath_or_buffer=csv_file,
        sep=";",
        dtype=str,
        keep_default_na=False,
    )

    missing_columns = REQUIRED_CHANNEL_COLUMNS - set(dataframe.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Missing required columns in {csv_file}: {missing}"
        )

    if dataframe.empty:
        raise ValueError(
            f"The channel configuration contains no channels: {csv_file}"
        )

    dataframe = dataframe.copy()

    for column in REQUIRED_CHANNEL_COLUMNS:
        dataframe[column] = dataframe[column].str.strip()

    empty_values = []

    for column in REQUIRED_CHANNEL_COLUMNS:
        empty_rows = dataframe.index[dataframe[column] == ""].tolist()

        if empty_rows:
            row_numbers = [index + 2 for index in empty_rows]
            empty_values.append(
                f"{column} at CSV rows {row_numbers}"
            )

    if empty_values:
        details = "; ".join(empty_values)
        raise ValueError(
            f"The channel configuration contains empty values: {details}"
        )

    duplicate_labels = dataframe.loc[
        dataframe["label"].duplicated(keep=False),
        "label",
    ].unique()

    if len(duplicate_labels) > 0:
        duplicates = ", ".join(sorted(duplicate_labels))
        raise ValueError(
            f"Duplicate channel labels found: {duplicates}"
        )

    unsupported_categories = sorted(
        set(dataframe["category"]) - SUPPORTED_CATEGORIES
    )

    if unsupported_categories:
        categories = ", ".join(unsupported_categories)
        raise ValueError(
            "Unsupported channel categories: "
            f"{categories}. Supported categories are: "
            f"{', '.join(sorted(SUPPORTED_CATEGORIES))}"
        )

    unsupported_types = sorted(
        set(dataframe["type"]) - NODELIST_TYPES.keys()
    )

    if unsupported_types:
        types = ", ".join(unsupported_types)
        raise ValueError(
            f"Unsupported channel data types: {types}. "
            f"Supported types are: {', '.join(sorted(NODELIST_TYPES))}"
        )

    return dataframe


def create_prefixes(config: dict[str, Any]) -> str:
    """
    Create the Turtle prefix and ontology header section.

    Parameters
    ----------
    config:
        Parsed wrapper configuration.

    Returns
    -------
    str
        Turtle prefix and ontology header content.
    """
    wrapper_config = config["wrapper"]
    ontology_config = config["ontology"]
    files_config = config["files"]

    channel_prefix = ontology_config["channel_prefix"]
    channel_namespace = ontology_config["channel_namespace"]
    channel_ontology_iri = ontology_config["channel_ontology_iri"]

    individuals_prefix = ontology_config["individuals_prefix"]
    individuals_namespace = ontology_config["individuals_namespace"]

    domain_prefix = ontology_config["domain_prefix"]
    domain_namespace = ontology_config["domain_namespace"]

    individuals_file = Path(files_config["individuals"]).name

    wrapper_name = wrapper_config["name"]
    wrapper_description = wrapper_config["description"]

    return f"""@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix emmo: <https://w3id.org/emmo#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix battinfo: <http://w3id.org/battinfo#> .
@prefix chameo: <https://w3id.org/emmo/domain/characterisation-methodology/chameo#> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix vann: <http://purl.org/vocab/vann/> .
@prefix csvw: <http://www.w3.org/ns/csvw#> .

@prefix equipment: <https://w3id.org/batteryequipment/public/ontology#> .
@prefix coater: <https://w3id.org/coater/public/ontology#> .
@prefix {domain_prefix}: <{domain_namespace}> .
@prefix {individuals_prefix}: <{individuals_namespace}> .
@prefix {channel_prefix}: <{channel_namespace}> .

<{channel_ontology_iri}> rdf:type owl:Ontology ;
    owl:imports <../ontology/{individuals_file}> ;
    rdfs:label "Channel and table ontology for {wrapper_name}" ;
    rdfs:comment "{wrapper_description}" .


# -------------------------------------------------------------------
# Channel and schema definitions
# -------------------------------------------------------------------

"""


def create_ttl(
    channels: pd.DataFrame,
    config: dict[str, Any],
) -> str:
    """
    Create the complete generated channel ontology.

    Parameters
    ----------
    channels:
        Validated channel configuration.

    config:
        Parsed wrapper configuration.

    Returns
    -------
    str
        Generated Turtle ontology content.
    """
    content = create_prefixes(config)

    namespace = config["ontology"]["channel_prefix"]

    for _, row in channels.iterrows():
        content += create_table_description(
            namespace=namespace,
            label=row["label"],
            name=row["name"],
            property_identifier=row["property"],
            unit=row["unit"],
            category=row["category"],
            device=row["device"],
            semantic_model=config["semantic_model"],
        )

    return content


def create_table_description(
    namespace: str,
    label: str,
    name: str,
    property_identifier: str,
    unit: str,
    category: str,
    device: str,
    semantic_model: dict[str, str],
) -> str:
    """
    Create the channel and CSVW table-schema description.

    Parameters
    ----------
    namespace:
        Turtle prefix used for generated channel resources.

    label:
        Stable channel identifier.

    name:
        Source-system identifier or descriptive channel name.

    property_identifier:
        Semantic property represented by the value column.

    unit:
        RDF identifier of the value unit.

    category:
        Channel category, either measurement or control.

    device:
        RDF identifier of the associated equipment or device.

    semantic_model:
        Semantic concepts and properties defined in wrapper.yaml.

    Returns
    -------
    str
        Generated Turtle content for one channel.
    """
    category_concepts = {
        "measurement": semantic_model["measurement_channel_class"],
        "control": semantic_model["control_channel_class"],
    }

    category_concept = category_concepts[category]

    content = f"""
{namespace}:{label} a {category_concept} .
{namespace}:{label} dc:title "{escape_turtle_string(name)}" .
{namespace}:{label} csvw:tableSchema {namespace}:{label}_schema .

{namespace}:{label}_schema a csvw:Schema .
{namespace}:{label}_schema csvw:columns {namespace}:{label}_schema_col1 .
{namespace}:{label}_schema csvw:columns {namespace}:{label}_schema_col2 .
{namespace}:{label}_schema csvw:primaryKey "time" .
"""

    content += create_process_context(
        namespace=namespace,
        label=label,
        category=category,
        device=device,
        semantic_model=semantic_model,
    )

    content += create_time_column(
        namespace=namespace,
        label=label,
        timestamp_property=semantic_model["timestamp_property"],
    )

    content += create_value_column(
        namespace=namespace,
        label=label,
        property_identifier=property_identifier,
        unit=unit,
        unit_property=semantic_model["unit_property"],
    )

    return content


def create_process_context(
    namespace: str,
    label: str,
    category: str,
    device: str,
    semantic_model: dict[str, str],
) -> str:
    """
    Create the process context for a measurement or control channel.

    Parameters
    ----------
    namespace:
        Turtle prefix used for generated resources.

    label:
        Stable channel identifier.

    category:
        Channel category, either measurement or control.

    device:
        RDF identifier of the associated equipment or device.

    semantic_model:
        Semantic concepts and properties from wrapper.yaml.

    Returns
    -------
    str
        Generated process-context Turtle content.

    Raises
    ------
    ValueError
        If the category is unsupported.
    """
    if category == "measurement":
        process_class = semantic_model["measurement_process_class"]
        device_property = semantic_model["measurement_device_property"]
        channel_property = semantic_model["measurement_output_property"]

    elif category == "control":
        process_class = semantic_model["control_process_class"]
        device_property = semantic_model["control_device_property"]
        channel_property = semantic_model["control_input_property"]

    else:
        raise ValueError(
            f"Unknown channel category in create_process_context: {category}"
        )

    return f"""
{namespace}:{label}_process a {process_class} ;
    {device_property} {device} ;
    {channel_property} {namespace}:{label} .
"""


def create_time_column(
    namespace: str,
    label: str,
    timestamp_property: str,
) -> str:
    """
    Create the timestamp column description.

    Parameters
    ----------
    namespace:
        Turtle prefix used for generated resources.

    label:
        Stable channel identifier.

    timestamp_property:
        Semantic property represented by the timestamp column.

    Returns
    -------
    str
        Generated timestamp-column Turtle content.
    """
    return f"""
{namespace}:{label}_schema_col1 a csvw:Column .
{namespace}:{label}_schema_col1 csvw:propertyUrl {timestamp_property} .
{namespace}:{label}_schema_col1 csvw:datatype xsd:dateTime .
{namespace}:{label}_schema_col1 csvw:name "time" .
{namespace}:{label}_schema_col1 csvw:required true .
"""


def create_value_column(
    namespace: str,
    label: str,
    property_identifier: str,
    unit: str,
    unit_property: str,
) -> str:
    """
    Create the value column description.

    Parameters
    ----------
    namespace:
        Turtle prefix used for generated resources.

    label:
        Stable channel identifier.

    property_identifier:
        Semantic property represented by the value column.

    unit:
        RDF identifier of the physical unit.

    unit_property:
        Semantic property connecting the column to its unit.

    Returns
    -------
    str
        Generated value-column Turtle content.
    """
    return f"""
{namespace}:{label}_schema_col2 a csvw:Column .
{namespace}:{label}_schema_col2 csvw:propertyUrl {property_identifier} .
{namespace}:{label}_schema_col2 csvw:datatype xsd:decimal .
{namespace}:{label}_schema_col2 {unit_property} {unit} .
{namespace}:{label}_schema_col2 csvw:name "value" .
{namespace}:{label}_schema_col2 csvw:required true .

"""


def create_nodelist(
    channels: pd.DataFrame,
    output_file: Path,
) -> None:
    """
    Create the OPC-UA node-list configuration.

    Parameters
    ----------
    channels:
        Validated channel configuration.

    output_file:
        Path where nodelist.csv will be written.
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)

    length = channels.shape[0]

    dataframe = pd.DataFrame(
        {
            "name": channels["label"],
            "type": [
                NODELIST_TYPES[type_identifier]
                for type_identifier in channels["type"].tolist()
            ],
            "namespace": channels["ns"],
            "identifier_type": ["s"] * length,
            "identifier": channels["name"],
            "sampling_interval": [None] * length,
            "queue_size": [None] * length,
            "discard_oldest": [None] * length,
            "trigger": [None] * length,
            "deadband_type": [None] * length,
            "deadband_value": [None] * length,
        }
    )

    dataframe.to_csv(
        output_file,
        sep=",",
        index=False,
    )


def create_init_sql(
    nodelist_file: Path,
    output_file: Path,
) -> None:
    """
    Create the TimescaleDB initialization script.

    Parameters
    ----------
    nodelist_file:
        Path to the generated OPC-UA node list.

    output_file:
        Path where init.sql will be written.
    """
    dataframe = pd.read_csv(
        nodelist_file,
        sep=",",
    )

    create_tables = (
        "-- init.sql\n"
        "CREATE EXTENSION IF NOT EXISTS timescaledb;\n\n"
        "-- Create channel tables\n"
    )

    create_hypertables = (
        "\n-- Convert the channel tables into hypertables\n"
    )

    types = dataframe["type"].tolist()

    for index, name in enumerate(dataframe["name"].tolist()):
        node_type = types[index]
        sql_type = SQL_TYPES[node_type]

        create_tables += (
            f"CREATE TABLE IF NOT EXISTS {name} "
            f"(time TIMESTAMPTZ NOT NULL, "
            f"value {sql_type} NOT NULL);\n"
        )

        create_hypertables += (
            f"SELECT create_hypertable('{name}', 'time');\n"
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    output_file.write_text(
        create_tables + create_hypertables,
        encoding="utf-8",
    )


def validate_generated_ontology(ontology_file: Path) -> int:
    """
    Parse the generated Turtle ontology.

    Parameters
    ----------
    ontology_file:
        Path to the generated Turtle file.

    Returns
    -------
    int
        Number of triples parsed from the generated ontology.

    Raises
    ------
    Exception
        RDFLib parsing errors are allowed to propagate.
    """
    graph = Graph()
    graph.parse(ontology_file, format="turtle")

    return len(graph)


def escape_turtle_string(value: str) -> str:
    """
    Escape a value used as a Turtle string literal.

    Parameters
    ----------
    value:
        Unescaped string.

    Returns
    -------
    str
        Escaped Turtle string.
    """
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def main() -> None:
    """Generate all equipment-wrapper outputs."""
    config = load_wrapper_config(CONFIG_FILE)

    files_config = config["files"]

    channels_file = resolve_repository_path(
        files_config["channels"]
    )
    individuals_file = resolve_repository_path(
        files_config["individuals"]
    )
    ontology_file = resolve_repository_path(
        files_config["generated_ontology"]
    )
    nodelist_file = resolve_repository_path(
        files_config["nodelist"]
    )
    database_schema_file = resolve_repository_path(
        files_config["database_schema"]
    )

    if not individuals_file.is_file():
        raise FileNotFoundError(
            "Equipment-individuals ontology does not exist: "
            f"{individuals_file}"
        )

    channels = load_channels(channels_file)

    ontology_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    content = create_ttl(
        channels=channels,
        config=config,
    )

    ontology_file.write_text(
        content,
        encoding="utf-8",
    )

    print(f"Created ontology: {ontology_file}")

    create_nodelist(
        channels=channels,
        output_file=nodelist_file,
    )

    print(f"Created node list: {nodelist_file}")

    create_init_sql(
        nodelist_file=nodelist_file,
        output_file=database_schema_file,
    )

    print(f"Created database schema: {database_schema_file}")

    triple_count = validate_generated_ontology(ontology_file)

    print(
        f"Validated generated ontology with {triple_count} triples."
    )


if __name__ == "__main__":
    main()
    