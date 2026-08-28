from rdflib import Graph, OWL, URIRef
import pandas as pd

#TODO need to check that the units or concepts from EMMO exist

def load_ontology_with_imports(ontology_file):
    """
    Load an ontology from a file and recursively load any imported ontologies.
    """
    g = Graph()
    g.parse(ontology_file, format="turtle")

    # Find all owl:imports URIs in the graph
    imported_ontologies = list(g.objects(predicate=OWL.imports))

    # Loop through and parse each imported ontology
    for ontology_url in imported_ontologies:
        if isinstance(ontology_url, URIRef):
            try:
                print(f"Importing: {ontology_url}")
                # RDFLib will try to guess the format, or you can specify it
                g.parse(location=str(ontology_url))
            except Exception as e:
                print(f"Could not load {ontology_url}: {e}")

    return g


def load_graph_limited_imports(initial_source, file_format="turtle", max_layers=2):
    g = Graph()
    
    # Track files already successfully parsed to prevent infinite loops
    processed = set()
    
    # Store tuples in the queue: (source_path_or_url, current_layer)
    # The initial root file is layer 0
    to_process = [(initial_source, 0)]
    
    while to_process:
        current_source, layer = to_process.pop(0)
        
        if current_source in processed:
            continue
            
        try:
            print(f"[Layer {layer}] Parsing: {current_source}")
            g.parse(current_source, format=file_format)
            processed.add(current_source)
            
            # If we are already at the max allowed layer, do NOT look for deeper imports
            if layer >= max_layers:
                continue
                
            # Scan for imports to build the NEXT layer
            for obj in g.objects(predicate=OWL.imports):
                if isinstance(obj, URIRef):
                    import_uri = str(obj)
                    
                    # Add to queue only if we haven't seen it or queued it yet
                    if import_uri not in processed and not any(item[0] == import_uri for item in to_process):
                        to_process.append((import_uri, layer + 1))
                        
        except Exception as e:
            print(f"Error loading {current_source} at layer {layer}: {e}")
            
    return g



def get_list_individuals_from_csv(csv_file, sep=','):
    """
    Read a CSV file and return a list of individuals (URIs) from the column device.
    """
    individuals = []
    df = pd.read_csv(csv_file, sep=sep)
    if 'device' in df.columns:
        individuals = df['device'].tolist()
    else:
        print("Warning: 'device' column not found in CSV.")
    return individuals


def check_individuals_in_graph(graph, individuals):
    """
    Check if each individual in the list is present in the RDF graph.
    """
    prefixes = dict(graph.namespaces())
    missing_individuals = []
    for individual in individuals:
        if ':' in individual:
            prefix, local_name = individual.split(':', 1)
            if prefix in prefixes:
                individual = str(prefixes[prefix]) + local_name
            else:
                print(f"Warning: Prefix '{prefix}' not found in graph namespaces.")
        if not (URIRef(individual), None, None) in graph:
            missing_individuals.append(individual)
    return missing_individuals


def get_list_properties_from_csv(csv_file, sep=','):
    """
    Read a CSV file and return a list of properties (URIs) from the column property.
    """
    properties = []
    df = pd.read_csv(csv_file, sep=sep)
    if 'property' in df.columns:
        properties = df['property'].tolist()
    else:
        print("Warning: 'property' column not found in CSV.")
    return properties


def check_properties_in_graph(graph, properties):
    """
    Check if each property in the list is present in the RDF graph.
    """
    prefixes = dict(graph.namespaces())
    missing_properties = []
    for property in properties:
        if ':' in property:
            prefix, local_name = property.split(':', 1)
            if prefix in prefixes:
                property = str(prefixes[prefix]) + local_name
            else:
                print(f"Warning: Prefix '{prefix}' not found in graph namespaces.")
        if not (URIRef(property), None, None) in graph:
            missing_properties.append(property)
    return missing_properties
