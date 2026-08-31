# Equipment Wrapper Template

This repository is a template for developing a semantic wrapper for industrial or laboratory equipment.

An equipment wrapper connects equipment-specific data sources to a common semantic and storage representation. It describes the physical equipment, maps measurement and control channels to ontology concepts, defines data units and types, and generates configuration files for data collection, storage, and visualization.

Create a separate repository from this template for each equipment installation.

Examples of repositories created from this template includes:

```text
fom-equipment-wrapper
mathis-equipment-wrapper
```

Each equipment repository remains independently maintainable and can have its own versioning, release cycle, ownership, and access policy.

---

## Purpose

Equipment integrations commonly require several connected descriptions:

- The physical equipment and its devices
- Measurement and control channels
- Source-system identifiers, such as OPC-UA nodes
- Semantic properties represented by each channel
- Measurement units and data types
- Time-series database tables
- A machine-readable ontology
- A visualization of the resulting knowledge graph

The equipment wrapper keeps these descriptions together and generates consistent deployment resources from a small set of maintained source files.

The intended generation flow is:

```text
Wrapper configuration
        +
Channel configuration
        +
Equipment individuals ontology
        |
        v
Equipment-wrapper generator
        |
        +--> Channel ontology
        +--> OPC-UA node list
        +--> TimescaleDB initialization script
        +--> Knowledge-graph visualization
```

The maintained source files remain the authoritative representation of an equipment wrapper. Generated files should be reproducible from these source files.

---

## Repository structure

```text
.
├── config/
│   ├── wrapper.yaml
│   └── channels.csv
├── ontology/
│   └── equipment_individuals.ttl
├── generated/
│   └── .gitkeep
├── scripts/
│   ├── generate_wrapper.py
│   └── visualize_wrapper.py
├── tests/
│   └── .gitkeep
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

### Directory responsibilities

```text
config/
    Equipment-specific configuration maintained by the wrapper owner.

ontology/
    Manually maintained semantic description of the equipment,
    its devices, components, and processes.

scripts/
    Generic generation and visualization scripts.
fuseki/
    Reusable library code
generated/
    Reproducible files generated from the maintained wrapper inputs.

tests/
    Validation tests for the wrapper configuration and generated outputs.
```

---

## Maintained and generated files

The repository separates manually maintained input files from generated outputs.

### Manually maintained inputs

The following files define the equipment wrapper and should be reviewed and maintained by the equipment owner:

```text
config/wrapper.yaml
config/channels.csv
ontology/equipment_individuals.ttl
```

### Shared implementation

The following files contain the generic generation logic:

```text
scripts/generate_wrapper.py
scripts/visualize_wrapper.py
scripts/generate_dashboards.py
```

### Generated outputs

The following files are created by the generation scripts:

```text
generated/table_channels_<equipment>.ttl
generated/nodelist.csv
generated/init.sql
generated/visualization/graph.html
generated/dashboards/<equipment>_generic.json
generated/dashboards/<equipment>_specific.json
generated/dashboards/generation_report.json
```

Generated files should not normally be edited manually. Changes should be made in the wrapper configuration, channel configuration, equipment ontology, or generation logic. The outputs should then be regenerated.

---

# Wrapper configuration

The file `config/wrapper.yaml` contains the general identity and namespace configuration for the equipment wrapper.

An initial template is what is available in this repository. Replace all example values when creating an equipment repository.

---

# Equipment-individuals ontology

The file:

```text
ontology/equipment_individuals.ttl
```

describes the physical equipment represented by the wrapper.

This ontology is maintained manually because the structure of physical equipment cannot be inferred reliably from a channel list.

The ontology can describe:

- The main equipment
- Devices
- Components
- Subcomponents
- Equipment models
- Equipment parameters
- Manufacturing processes
- Process participants
- Process decomposition
- Process sequence
- Relationships between equipment and devices
- Relationships between devices and components

A minimal template is available under the folder ontology.

# How to Run Everything

## Flow

```text
generate_wrapper.py
    channels.csv
        -> generated channel ontology (.ttl)
        -> nodelist.csv
        -> init.sql

check_wrapper.py
    channels.csv + equipment_individuals.ttl
        -> checks referenced devices and properties

visualize_wrapper.py
    generated channel ontology + imports
        -> graph.html
```

## Quick Start

This repository provides a generic template for creating semantic equipment wrappers.

The wrapper generates:

- A channel ontology (`.ttl`)
- An OPC-UA node list (`nodelist.csv`)
- A TimescaleDB initialization script (`init.sql`)
- An interactive knowledge graph visualization (`graph.html`)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure the Wrapper

Edit the wrapper configuration:

```text
config/wrapper.yaml
```

Define the equipment channels:

```text
config/channels.csv
```

Define the equipment individuals:

```text
ontology/equipment_individuals.ttl
```

### 3. Generate Outputs

```bash
python scripts/generate_wrapper.py
```

Generated files:

```text
generated/
├── table_channels_<equipment>.ttl
├── nodelist.csv
└── init.sql
```

### 4. Validate the Wrapper

Verify that all devices and ontology properties referenced in `config/channels.csv` exist in the ontology graph.

```bash
python scripts/check_wrapper.py
```

A successful run reports:

```text
Equipment-wrapper consistency check passed.
```

### 5. Create a Visualization

```bash
python scripts/visualize_wrapper.py
```

Generated file:

```text
generated/visualization/graph.html
```

Open `graph.html` in a web browser to explore the equipment ontology.

### 5. Create Dashboards

First add in the properties to dashboard.yaml file and then run : 

```bash
python scripts/generate_dashboards.py
```

Generated files:

```text
generated/dashboards/<equipment>_generic.json

generated/dashboards/<equipment>_specific.json
```
Open generic and specific files in grafana dashboard to explore the timeseries data.
