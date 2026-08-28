# Wrapper configuration

The file `config/wrapper.yaml` contains the general identity and namespace configuration for the equipment wrapper.

An initial template is what is available in this repository. Replace all example values when creating an equipment repository.

## Wrapper fields

### `wrapper.identifier`

A short, stable, lowercase identifier for the equipment.

Example:

```yaml
identifier: fom
```

The identifier can be used in generated filenames and repository automation.

Recommended format:

```text
lowercase
no spaces
short but recognizable
```

### `wrapper.name`

A human-readable equipment name.

Example:

```yaml
name: FOM roll-to-roll coater
```

### `wrapper.description`

A short description of the purpose and scope of the wrapper.

Example:

```yaml
description: Semantic wrapper for the FOM coating and drying equipment
```

---

## Ontology configuration

### `ontology.channel_prefix`

The Turtle prefix used for generated channel and table resources.

Example:

```yaml
channel_prefix: fom-table
```

### `ontology.channel_namespace`

The namespace for generated channel, schema, column, and process identifiers.

The namespace should normally end with `#` when it is intended for prefixed Turtle identifiers.

Example:

```yaml
channel_namespace: https://w3id.org/fom-table/public/ontology#
```

### `ontology.channel_ontology_iri`

The ontology IRI for the generated channel ontology.

Example:

```yaml
channel_ontology_iri: https://w3id.org/fom-table/public/ontology
```

### `ontology.individuals_prefix`

The Turtle prefix for equipment-specific individuals.

Example:

```yaml
individuals_prefix: fom-ind
```

### `ontology.individuals_namespace`

The namespace used for physical equipment, devices, components, and process individuals.

Example:

```yaml
individuals_namespace: https://w3id.org/fom-ind/public/ontology#
```

### `ontology.individuals_ontology_iri`

The ontology IRI for the equipment-individuals ontology.

Example:

```yaml
individuals_ontology_iri: https://w3id.org/fom-ind/public/ontology
```

### `ontology.domain_prefix`

The Turtle prefix for equipment-specific domain concepts.

Example:

```yaml
domain_prefix: fom
```

### `ontology.domain_namespace`

The namespace that defines the equipment-specific classes and properties used by the wrapper.

Example:

```yaml
domain_namespace: https://w3id.org/fom/public/ontology#
```

### `ontology.domain_ontology_iri`

The ontology IRI imported by the equipment-individuals ontology.

Example:

```yaml
domain_ontology_iri: https://w3id.org/fom/public/ontology
```

---

# Channel configuration

The file `config/channels.csv` defines the equipment measurement and control channels.

It uses a semicolon as the delimiter.

The required header is:

```csv
ns;label;name;category;device;property;unit;type
```

An example row is:

```csv
ns;label;name;category;device;property;unit;type
register.DW0000;oven.temperature;OvenTemperature;measurement;equipment-ind:Oven1;equipment:hasTemperatureData;<https://w3id.org/emmo#DegreeCelsius>;REAL
```

The example is illustrative. Replace all values with information for the actual equipment.

## Channel columns

### `ns`

The source-system namespace, node path, or node namespace used by the data collector.

Example:

```text
register.DW0000
```

The exact meaning of this value depends on the source-system configuration.

For OPC-UA-based integrations, this value can represent the namespace or address information needed to locate the node.

### `label`

A stable identifier for the channel.

Example:

```text
oven.temperature
```

The current generation logic can use this value for:

- The generated RDF channel identifier
- The generated table-schema identifier
- The generated database table name
- The node-list `name` value

The label should therefore be:

- Unique within the wrapper
- Stable over time
- Compatible with downstream naming requirements
- Independent of a human-readable display label

Avoid spaces and temporary descriptive wording.

### `name`

The source node identifier.

Example:

```text
OvenTemperature
```

For the current node-list generation, this value is used as the source identifier.

Do not confuse `name` with `label`:

```text
label
    Stable wrapper and storage identifier.

name
    Identifier used by the equipment data source.
```

### `category`

Identifies whether the channel represents a measurement or a control input.

Supported values:

```text
measurement
control
```

A `measurement` channel represents data observed from the equipment.

A `control` channel represents a setpoint, command, or other control-related input.

The category determines the semantic structures generated for the channel.

### `device`

The RDF identifier of the equipment, device, or component associated with the channel.

Example:

```text
equipment-ind:Oven1
```

The referenced individual must be defined in:

```text
ontology/equipment_individuals.ttl
```

Examples of possible associated resources include:

- The complete machine
- A coating device
- An unwinding device
- A rewinding device
- An oven
- A heater
- A temperature sensor
- An inlet or outlet
- A mixer component

Use the most specific valid equipment individual that represents the source or target of the channel.

### `property`

The semantic property represented by the channel.

Example:

```text
equipment:hasTemperatureData
```

This connects the equipment-specific signal to a shared semantic definition.

The property should already be defined in an imported ontology. A wrapper should not introduce a new property only by referring to it in the CSV file.

### `unit`

The RDF identifier for the physical unit associated with the channel value.

Example:

```text
<https://w3id.org/emmo#DegreeCelsius>
```

Other possible examples include:

```text
<https://w3id.org/emmo#MetrePerSecond>
<https://w3id.org/emmo#MilliMetre>
<https://w3id.org/emmo#Newton>
<https://w3id.org/emmo#RevolutionPerMinute>
<https://w3id.org/emmo#KiloWatt>
```

Use the exact unit identifier provided by the relevant ontology.

### `type`

The source data type.

The initial generator supports:

```text
REAL
INT
```

The generator maps these values to node-list and SQL data types.

Example mappings:

```text
REAL -> float64 -> REAL
INT  -> int     -> INT
```

If additional source types are introduced, update the type mappings in the generator and add corresponding validation tests.

---

# Channel configuration rules

The following rules help keep generated resources stable and valid.

## Unique labels

Every `label` must be unique within `config/channels.csv`.

Duplicate labels could lead to duplicate RDF resources, database tables, or node-list entries.

## Valid categories

Every category must be one of:

```text
measurement
control
```

Other values should be rejected during validation.

## Valid data types

Every data type must be supported by the generator.

Initially supported:

```text
REAL
INT
```

## Defined devices

Every device referenced in the `device` column must be defined in the equipment-individuals ontology or in one of its imported ontologies.

## Defined properties

Every property referenced in the `property` column should be defined by the domain ontology or another imported ontology.

## Valid units

Every unit should be a valid RDF identifier from the selected unit ontology.

## Stable identifiers

Changing a channel label may also change:

- The channel RDF identifier
- The table-schema RDF identifier
- The database table name
- References used by downstream systems

Treat label changes as potentially incompatible changes.

---

# Semantic model configuration

The `semantic_model` section defines the RDF classes and properties used by the generator when creating channels, processes, CSVW schemas, and relationships between generated resources.

These values should normally reference concepts from EMMO, CHAMEO, Batteryequipment, or an equipment-specific ontology.

Example:

```yaml
semantic_model:

  # RDF class used for generated measurement channels
  measurement_channel_class: emmo:EMMO_0f6f0120_c079_4d95_bb11_4ddee05e530e

  # RDF class used for generated control channels
  control_channel_class: coater:CommandInput

  # RDF class used for measurement processes
  measurement_process_class: chameo:CharacterisationMeasurementProcess

  # RDF class used for control processes
  control_process_class: equipment:DeviceControlProcess

  # Property connecting a process to its associated device
  measurement_device_property: emmo:EMMO_35c29eb6_f57e_48d8_85af_854f9e926e77
  control_device_property: emmo:EMMO_35c29eb6_f57e_48d8_85af_854f9e926e77

  # Property connecting a process to an output or input channel
  measurement_output_property: emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840
  control_input_property: emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22

  # CSVW metadata properties
  timestamp_property: equipment:hasDateTimeStampData
  unit_property: emmo:EMMO_02c0621e_a527_4790_8a0f_2bb51973c819
```

## Semantic model fields

### `measurement_channel_class`

RDF class assigned to generated measurement channels.

Example:

```yaml
measurement_channel_class: emmo:EMMO_0f6f0120_c079_4d95_bb11_4ddee05e530e
```

### `control_channel_class`

RDF class assigned to generated control channels.

Example:

```yaml
control_channel_class: coater:CommandInput
```

### `measurement_process_class`

RDF class assigned to generated measurement processes.

Example:

```yaml
measurement_process_class: chameo:CharacterisationMeasurementProcess
```

### `control_process_class`

RDF class assigned to generated control processes.

Example:

```yaml
control_process_class: equipment:DeviceControlProcess
```

### `measurement_device_property`

Property linking a generated measurement process to the device individual.

Example:

```yaml
measurement_device_property: emmo:EMMO_35c29eb6_f57e_48d8_85af_854f9e926e77
```

### `control_device_property`

Property linking a generated control process to the device individual.

Example:

```yaml
control_device_property: emmo:EMMO_35c29eb6_f57e_48d8_85af_854f9e926e77
```

### `measurement_output_property`

Property linking a measurement process to its generated measurement channel.

Example:

```yaml
measurement_output_property: emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840
```

### `control_input_property`

Property linking a control process to its generated control channel.

Example:

```yaml
control_input_property: emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22
```

### `timestamp_property`

Property associated with the generated timestamp column.

Example:

```yaml
timestamp_property: equipment:hasDateTimeStampData
```

### `unit_property`

Property linking generated value columns to their physical units.

Example:

```yaml
unit_property: emmo:EMMO_02c0621e_a527_4790_8a0f_2bb51973c819
```

## Notes

The template provides default values based on EMMO, CHAMEO, and BATMACHINE ontologies.

Most equipment wrappers will not need to modify these values.

Only change them if your organization uses different semantic concepts for:

- Measurement channels
- Control channels
- Process definitions
- Device relationships
- Unit annotations
- Timestamp semantics