"""
Generate generic and equipment-specific Grafana dashboards.

The script reads:

- config/wrapper.yaml
- config/dashboard.yaml
- config/channels.csv

It generates:

- generated/dashboards/<equipment>_generic.json
- generated/dashboards/<equipment>_specific.json
- generated/dashboards/generation_report.json

The generated dashboards contain:

- an introductory text panel explaining what is plotted
- one time-series panel for each configured semantic property
- one SQL target for each matching equipment channel

Equipment-specific properties, datasource settings, and dashboard
settings must be defined in config/dashboard.yaml. This script must not
contain equipment-specific namespaces, properties, or table names.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
WRAPPER_CONFIG_FILE = REPOSITORY_ROOT / "config" / "wrapper.yaml"

REQUIRED_CHANNEL_COLUMNS = {
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

GRAFANA_UNIT_BY_ONTOLOGY_UNIT = {
    "https://w3id.org/emmo#DegreeCelsius": "celsius",
    "https://w3id.org/emmo#Kelvin": "kelvin",
    "https://w3id.org/emmo#MetrePerSecond": "velocityms",
    "https://w3id.org/emmo#MilliMetre": "lengthmm",
    "https://w3id.org/emmo#Metre": "lengthm",
    "https://w3id.org/emmo#Newton": "forceN",
    "https://w3id.org/emmo#RevolutionPerMinute": "rotrpm",
    "https://w3id.org/emmo#Watt": "watt",
    "https://w3id.org/emmo#KiloWatt": "kwatt",
    "https://w3id.org/emmo#Pascal": "pressurepa",
    "https://w3id.org/emmo#Percent": "percent",
}


def load_yaml_file(file_path: Path) -> dict[str, Any]:
    """Load a YAML file and verify that it contains a mapping."""
    if not file_path.is_file():
        raise FileNotFoundError(
            f"Configuration file does not exist: {file_path}"
        )

    with file_path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError(
            f"Configuration file must contain a YAML mapping: {file_path}"
        )

    return data


def require_mapping(
    config: dict[str, Any],
    field: str,
    source_name: str,
) -> dict[str, Any]:
    """Return a required mapping from a configuration dictionary."""
    value = config.get(field)

    if not isinstance(value, dict):
        raise ValueError(
            f"'{field}' must be a mapping in {source_name}."
        )

    return value


def require_string(
    config: dict[str, Any],
    field: str,
    source_name: str,
) -> str:
    """Return a required non-empty string."""
    value = config.get(field)

    if not isinstance(value, str) or not value.strip():
        raise ValueError(
            f"'{field}' must be a non-empty string in {source_name}."
        )

    return value.strip()


def resolve_repository_path(path_value: str) -> Path:
    """Resolve a configured path relative to the repository root."""
    path = Path(path_value)

    if path.is_absolute():
        return path

    return REPOSITORY_ROOT / path


def load_channels(csv_file: Path) -> pd.DataFrame:
    """Load and validate config/channels.csv."""
    if not csv_file.is_file():
        raise FileNotFoundError(
            f"Channel configuration does not exist: {csv_file}"
        )

    channels = pd.read_csv(
        csv_file,
        sep=";",
        dtype=str,
        keep_default_na=False,
    )

    channels.columns = [
        column.strip() for column in channels.columns
    ]

    missing_columns = REQUIRED_CHANNEL_COLUMNS - set(channels.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Missing required columns in {csv_file}: {missing}"
        )

    for column in REQUIRED_CHANNEL_COLUMNS:
        channels[column] = channels[column].str.strip()

        empty_rows = channels.index[
            channels[column] == ""
        ].tolist()

        if empty_rows:
            row_numbers = ", ".join(
                str(index + 2) for index in empty_rows
            )
            raise ValueError(
                f"Empty '{column}' values in {csv_file} "
                f"at rows: {row_numbers}"
            )

    duplicate_labels = sorted(
        channels.loc[
            channels["label"].duplicated(keep=False),
            "label",
        ].unique()
    )

    if duplicate_labels:
        duplicates = ", ".join(duplicate_labels)
        raise ValueError(
            f"Duplicate channel labels in {csv_file}: {duplicates}"
        )

    invalid_categories = sorted(
        set(channels["category"]) - SUPPORTED_CATEGORIES
    )

    if invalid_categories:
        invalid = ", ".join(invalid_categories)
        raise ValueError(
            f"Unsupported channel categories in {csv_file}: {invalid}"
        )

    return channels


def read_property_list(
    section: dict[str, Any],
    section_name: str,
) -> list[str]:
    """Read and validate a dashboard semantic-property list."""
    properties = section.get("properties")

    if not isinstance(properties, list):
        raise ValueError(
            f"'properties' must be a list in dashboard section "
            f"'{section_name}'."
        )

    normalized: list[str] = []

    for property_identifier in properties:
        if (
            not isinstance(property_identifier, str)
            or not property_identifier.strip()
        ):
            raise ValueError(
                f"Every property in dashboard section '{section_name}' "
                "must be a non-empty string."
            )

        normalized.append(property_identifier.strip())

    if len(normalized) != len(set(normalized)):
        raise ValueError(
            f"Duplicate properties found in dashboard section "
            f"'{section_name}'."
        )

    return normalized


def normalize_ontology_identifier(identifier: str) -> str:
    """Remove surrounding angle brackets from an RDF identifier."""
    normalized = identifier.strip()

    if normalized.startswith("<") and normalized.endswith(">"):
        return normalized[1:-1]

    return normalized


def local_name(identifier: str) -> str:
    """Return the local name of a full or prefixed RDF identifier."""
    normalized = normalize_ontology_identifier(identifier)

    if "#" in normalized:
        return normalized.rsplit("#", maxsplit=1)[1]

    if "/" in normalized:
        return normalized.rstrip("/").rsplit("/", maxsplit=1)[1]

    if ":" in normalized:
        return normalized.split(":", maxsplit=1)[1]

    return normalized


def humanize_identifier(identifier: str) -> str:
    """Convert an RDF or dotted identifier into a readable label."""
    value = local_name(identifier)

    for separator in (".", "_", "-"):
        value = value.replace(separator, " ")

    characters: list[str] = []

    for index, character in enumerate(value):
        if (
            index > 0
            and character.isupper()
            and value[index - 1].islower()
        ):
            characters.append(" ")

        characters.append(character)

    return " ".join(
        word.capitalize()
        for word in "".join(characters).split()
    )


def grafana_unit(unit_identifier: str) -> str:
    """Map an ontology unit identifier to a Grafana unit."""
    normalized = normalize_ontology_identifier(unit_identifier)

    return GRAFANA_UNIT_BY_ONTOLOGY_UNIT.get(
        normalized,
        "short",
    )


def quote_postgresql_identifier(identifier: str) -> str:
    """Quote a PostgreSQL identifier safely."""
    return '"' + identifier.replace('"', '""') + '"'


def create_sql_query(
    table_name: str,
    time_column: str,
    value_column: str,
    series_name: str,
) -> str:
    """Create a Grafana PostgreSQL time-series query."""
    quoted_table = quote_postgresql_identifier(table_name)
    quoted_time = quote_postgresql_identifier(time_column)
    quoted_value = quote_postgresql_identifier(value_column)
    quoted_series = quote_postgresql_identifier(series_name)

    return (
        "SELECT\n"
        f"  {quoted_time} AS \"time\",\n"
        f"  {quoted_value} AS {quoted_series}\n"
        f"FROM {quoted_table}\n"
        f"WHERE $__timeFilter({quoted_time})\n"
        f"ORDER BY {quoted_time}"
    )


def create_reference_id(index: int) -> str:
    """Create Grafana reference IDs such as A, B, and AA."""
    value = index + 1
    result = ""

    while value:
        value, remainder = divmod(value - 1, 26)
        result = chr(65 + remainder) + result

    return result


def create_query_target(
    channel: dict[str, str],
    index: int,
    datasource: dict[str, str],
    time_column: str,
    value_column: str,
) -> dict[str, Any]:
    """Create one Grafana SQL query target."""
    series_name = channel["name"]

    return {
        "datasource": datasource,
        "editorMode": "code",
        "format": "time_series",
        "rawQuery": True,
        "rawSql": create_sql_query(
            table_name=channel["label"],
            time_column=time_column,
            value_column=value_column,
            series_name=series_name,
        ),
        "refId": create_reference_id(index),
    }


def create_text_panel(
    panel_id: int,
    equipment_name: str,
    dashboard_kind: str,
    description: str,
    property_count: int,
    channel_count: int,
) -> dict[str, Any]:
    """Create a text panel explaining what the dashboard plots."""
    content = (
        f"## {equipment_name}: {dashboard_kind} dashboard\n\n"
        f"{description}\n\n"
        f"This dashboard plots **{channel_count} channel(s)** grouped "
        f"under **{property_count} semantic property/properties**.\n\n"
        "Each time-series panel represents one semantic property. "
        "Signals that use the same semantic property and physical unit "
        "are displayed together so that related equipment values can be "
        "compared.\n\n"
        "The data is read from the equipment time-series tables. "
        "Each table contains a `time` column and a `value` column."
    )

    return {
        "datasource": {
            "type": "grafana",
            "uid": "-- Grafana --",
        },
        "gridPos": {
            "h": 7,
            "w": 24,
            "x": 0,
            "y": 0,
        },
        "id": panel_id,
        "options": {
            "code": {
                "language": "plaintext",
                "showLineNumbers": False,
                "showMiniMap": False,
            },
            "content": content,
            "mode": "markdown",
        },
        "pluginVersion": "11.0.0",
        "title": "About this dashboard",
        "type": "text",
    }


def create_timeseries_panel(
    panel_id: int,
    property_identifier: str,
    unit_identifier: str,
    channels: list[dict[str, str]],
    datasource: dict[str, str],
    time_column: str,
    value_column: str,
    grid_x: int,
    grid_y: int,
    grid_width: int,
) -> dict[str, Any]:
    """Create a time-series panel for one property and unit."""
    targets = [
        create_query_target(
            channel=channel,
            index=index,
            datasource=datasource,
            time_column=time_column,
            value_column=value_column,
        )
        for index, channel in enumerate(channels)
    ]

    channel_names = ", ".join(
        channel["name"] for channel in channels
    )

    categories = ", ".join(
        sorted({channel["category"] for channel in channels})
    )

    description = (
        f"Plots channels associated with `{property_identifier}`. "
        f"Channels: {channel_names}. "
        f"Category: {categories}. "
        f"Unit: {normalize_ontology_identifier(unit_identifier)}."
    )

    return {
        "datasource": datasource,
        "description": description,
        "fieldConfig": {
            "defaults": {
                "color": {
                    "mode": "palette-classic",
                },
                "custom": {
                    "axisBorderShow": False,
                    "axisCenteredZero": False,
                    "axisColorMode": "text",
                    "axisLabel": "",
                    "axisPlacement": "auto",
                    "barAlignment": 0,
                    "drawStyle": "line",
                    "fillOpacity": 10,
                    "gradientMode": "none",
                    "hideFrom": {
                        "legend": False,
                        "tooltip": False,
                        "viz": False,
                    },
                    "insertNulls": False,
                    "lineInterpolation": "linear",
                    "lineWidth": 1,
                    "pointSize": 5,
                    "scaleDistribution": {
                        "type": "linear",
                    },
                    "showPoints": "auto",
                    "spanNulls": False,
                    "stacking": {
                        "group": "A",
                        "mode": "none",
                    },
                    "thresholdsStyle": {
                        "mode": "off",
                    },
                },
                "mappings": [],
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {
                            "color": "green",
                            "value": None,
                        },
                        {
                            "color": "red",
                            "value": 80,
                        },
                    ],
                },
                "unit": grafana_unit(unit_identifier),
            },
            "overrides": [],
        },
        "gridPos": {
            "h": 9,
            "w": grid_width,
            "x": grid_x,
            "y": grid_y,
        },
        "id": panel_id,
        "options": {
            "legend": {
                "calcs": [],
                "displayMode": "list",
                "placement": "bottom",
                "showLegend": True,
            },
            "tooltip": {
                "hideZeros": False,
                "mode": "multi",
                "sort": "none",
            },
        },
        "targets": targets,
        "title": humanize_identifier(property_identifier),
        "type": "timeseries",
    }


def group_channels(
    channels: pd.DataFrame,
    selected_properties: list[str],
) -> tuple[
    dict[tuple[str, str], list[dict[str, str]]],
    list[str],
]:
    """
    Group selected channels by semantic property and physical unit.

    Returns the grouped channels and configured properties for which no
    matching channel was found.
    """
    grouped: dict[
        tuple[str, str],
        list[dict[str, str]],
    ] = defaultdict(list)

    available_properties = set(channels["property"])
    missing_properties = sorted(
        set(selected_properties) - available_properties
    )

    selected = channels[
        channels["property"].isin(selected_properties)
    ]

    for row in selected.to_dict(orient="records"):
        key = (
            row["property"],
            row["unit"],
        )
        grouped[key].append(row)

    return dict(grouped), missing_properties


def create_dashboard(
    equipment_identifier: str,
    equipment_name: str,
    dashboard_kind: str,
    title: str,
    description: str,
    grouped_channels: dict[
        tuple[str, str],
        list[dict[str, str]],
    ],
    datasource: dict[str, str],
    time_column: str,
    value_column: str,
    refresh: str,
    default_from: str,
    default_to: str,
    tags: list[str],
    editable: bool,
    schema_version: int,
) -> dict[str, Any]:
    """Create a complete Grafana dashboard."""
    channel_count = sum(
        len(channels)
        for channels in grouped_channels.values()
    )

    panels: list[dict[str, Any]] = [
        create_text_panel(
            panel_id=1,
            equipment_name=equipment_name,
            dashboard_kind=dashboard_kind,
            description=description,
            property_count=len(grouped_channels),
            channel_count=channel_count,
        )
    ]

    panel_id = 2
    panel_index = 0

    for property_and_unit in sorted(grouped_channels):
        property_identifier, unit_identifier = property_and_unit
        channels = grouped_channels[property_and_unit]

        grid_width = 12
        grid_x = (panel_index % 2) * grid_width
        grid_y = 7 + (panel_index // 2) * 9

        panels.append(
            create_timeseries_panel(
                panel_id=panel_id,
                property_identifier=property_identifier,
                unit_identifier=unit_identifier,
                channels=channels,
                datasource=datasource,
                time_column=time_column,
                value_column=value_column,
                grid_x=grid_x,
                grid_y=grid_y,
                grid_width=grid_width,
            )
        )

        panel_id += 1
        panel_index += 1

    slug_kind = dashboard_kind.lower().replace(" ", "-")

    return {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": {
                        "type": "grafana",
                        "uid": "-- Grafana --",
                    },
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations and alerts",
                    "type": "dashboard",
                }
            ]
        },
        "editable": editable,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "liveNow": False,
        "panels": panels,
        "refresh": refresh,
        "schemaVersion": schema_version,
        "tags": tags,
        "templating": {
            "list": [],
        },
        "time": {
            "from": default_from,
            "to": default_to,
        },
        "timepicker": {},
        "timezone": "browser",
        "title": title,
        "uid": f"{equipment_identifier}-{slug_kind}",
        "version": 1,
        "weekStart": "",
    }


def write_json_file(
    output_file: Path,
    content: dict[str, Any],
) -> None:
    """Write formatted JSON content to a file."""
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as file:
        json.dump(
            content,
            file,
            indent=2,
            ensure_ascii=False,
        )
        file.write("\n")


def validate_dashboard_properties(
    generic_properties: list[str],
    specific_properties: list[str],
) -> None:
    """Ensure a property is not assigned to both dashboards."""
    overlap = sorted(
        set(generic_properties) & set(specific_properties)
    )

    if overlap:
        overlapping = ", ".join(overlap)
        raise ValueError(
            "The following properties are configured as both generic "
            f"and equipment-specific: {overlapping}"
        )


def main() -> None:
    """Generate the generic and equipment-specific dashboards."""
    wrapper_config = load_yaml_file(
        WRAPPER_CONFIG_FILE
    )

    wrapper = require_mapping(
        wrapper_config,
        "wrapper",
        "config/wrapper.yaml",
    )

    files = require_mapping(
        wrapper_config,
        "files",
        "config/wrapper.yaml",
    )

    equipment_identifier = require_string(
        wrapper,
        "identifier",
        "config/wrapper.yaml",
    )

    equipment_name = require_string(
        wrapper,
        "name",
        "config/wrapper.yaml",
    )

    channels_file = resolve_repository_path(
        require_string(
            files,
            "channels",
            "config/wrapper.yaml",
        )
    )

    dashboard_config_path = resolve_repository_path(
        files.get(
            "dashboard_config",
            "config/dashboard.yaml",
        )
    )

    dashboard_config = load_yaml_file(
        dashboard_config_path
    )

    datasource_config = require_mapping(
        dashboard_config,
        "datasource",
        "config/dashboard.yaml",
    )

    database_config = require_mapping(
        dashboard_config,
        "database",
        "config/dashboard.yaml",
    )

    dashboard_settings = require_mapping(
        dashboard_config,
        "dashboard",
        "config/dashboard.yaml",
    )

    generic_config = require_mapping(
        dashboard_config,
        "generic",
        "config/dashboard.yaml",
    )

    specific_config = require_mapping(
        dashboard_config,
        "equipment_specific",
        "config/dashboard.yaml",
    )

    datasource = {
        "type": require_string(
            datasource_config,
            "type",
            "config/dashboard.yaml",
        ),
        "uid": require_string(
            datasource_config,
            "uid",
            "config/dashboard.yaml",
        ),
    }

    time_column = require_string(
        database_config,
        "time_column",
        "config/dashboard.yaml",
    )

    value_column = require_string(
        database_config,
        "value_column",
        "config/dashboard.yaml",
    )

    generic_properties = read_property_list(
        generic_config,
        "generic",
    )

    specific_properties = read_property_list(
        specific_config,
        "equipment_specific",
    )

    validate_dashboard_properties(
        generic_properties,
        specific_properties,
    )

    channels = load_channels(channels_file)

    generic_groups, missing_generic_properties = group_channels(
        channels,
        generic_properties,
    )

    specific_groups, missing_specific_properties = group_channels(
        channels,
        specific_properties,
    )

    refresh = str(
        dashboard_settings.get("refresh", "10s")
    )

    default_from = str(
        dashboard_settings.get(
            "default_from",
            "now-6h",
        )
    )

    default_to = str(
        dashboard_settings.get(
            "default_to",
            "now",
        )
    )

    editable = bool(
        dashboard_settings.get("editable", True)
    )

    schema_version = int(
        dashboard_settings.get("schema_version", 39)
    )

    configured_tags = dashboard_settings.get(
        "tags",
        ["BATMACHINE", "equipment-wrapper"],
    )

    if not isinstance(configured_tags, list) or not all(
        isinstance(tag, str) for tag in configured_tags
    ):
        raise ValueError(
            "'dashboard.tags' must be a list of strings in "
            "config/dashboard.yaml."
        )

    generic_title = str(
        generic_config.get(
            "title",
            f"{equipment_name}: Generic dashboard",
        )
    )

    generic_description = str(
        generic_config.get(
            "description",
            "This dashboard plots channels represented by semantic "
            "properties shared across compatible equipment.",
        )
    )

    specific_title = str(
        specific_config.get(
            "title",
            f"{equipment_name}: Equipment-specific dashboard",
        )
    )

    specific_description = str(
        specific_config.get(
            "description",
            "This dashboard plots channels represented by semantic "
            "properties specific to this equipment.",
        )
    )

    generic_dashboard = create_dashboard(
        equipment_identifier=equipment_identifier,
        equipment_name=equipment_name,
        dashboard_kind="Generic",
        title=generic_title,
        description=generic_description,
        grouped_channels=generic_groups,
        datasource=datasource,
        time_column=time_column,
        value_column=value_column,
        refresh=refresh,
        default_from=default_from,
        default_to=default_to,
        tags=[
            *configured_tags,
            "generic",
            equipment_identifier,
        ],
        editable=editable,
        schema_version=schema_version,
    )

    specific_dashboard = create_dashboard(
        equipment_identifier=equipment_identifier,
        equipment_name=equipment_name,
        dashboard_kind="Equipment-specific",
        title=specific_title,
        description=specific_description,
        grouped_channels=specific_groups,
        datasource=datasource,
        time_column=time_column,
        value_column=value_column,
        refresh=refresh,
        default_from=default_from,
        default_to=default_to,
        tags=[
            *configured_tags,
            "equipment-specific",
            equipment_identifier,
        ],
        editable=editable,
        schema_version=schema_version,
    )

    output_directory = resolve_repository_path(
        files.get(
            "dashboards",
            "generated/dashboards",
        )
    )

    generic_output = output_directory / (
        f"{equipment_identifier}_generic.json"
    )

    specific_output = output_directory / (
        f"{equipment_identifier}_specific.json"
    )

    report_output = output_directory / (
        "generation_report.json"
    )

    write_json_file(
        generic_output,
        generic_dashboard,
    )

    write_json_file(
        specific_output,
        specific_dashboard,
    )

    used_properties = (
        set(generic_properties)
        | set(specific_properties)
    )

    unclassified_properties = sorted(
        set(channels["property"]) - used_properties
    )

    report = {
        "equipment": {
            "identifier": equipment_identifier,
            "name": equipment_name,
        },
        "input": {
            "channels": str(
                channels_file.relative_to(REPOSITORY_ROOT)
            ),
            "dashboard_config": str(
                dashboard_config_path.relative_to(
                    REPOSITORY_ROOT
                )
            ),
            "channel_count": len(channels),
        },
        "generic_dashboard": {
            "file": str(
                generic_output.relative_to(
                    REPOSITORY_ROOT
                )
            ),
            "configured_properties": generic_properties,
            "matched_channel_count": sum(
                len(group)
                for group in generic_groups.values()
            ),
            "missing_properties": missing_generic_properties,
        },
        "equipment_specific_dashboard": {
            "file": str(
                specific_output.relative_to(
                    REPOSITORY_ROOT
                )
            ),
            "configured_properties": specific_properties,
            "matched_channel_count": sum(
                len(group)
                for group in specific_groups.values()
            ),
            "missing_properties": missing_specific_properties,
        },
        "unclassified_properties": unclassified_properties,
    }

    write_json_file(
        report_output,
        report,
    )

    print(f"Created generic dashboard: {generic_output}")
    print(
        "Created equipment-specific dashboard: "
        f"{specific_output}"
    )
    print(f"Created generation report: {report_output}")

    if missing_generic_properties:
        print()
        print("Generic properties without matching channels:")

        for property_identifier in missing_generic_properties:
            print(f" - {property_identifier}")

    if missing_specific_properties:
        print()
        print(
            "Equipment-specific properties without matching channels:"
        )

        for property_identifier in missing_specific_properties:
            print(f" - {property_identifier}")

    if unclassified_properties:
        print()
        print("Channel properties not assigned to a dashboard:")

        for property_identifier in unclassified_properties:
            print(f" - {property_identifier}")


if __name__ == "__main__":
    main()