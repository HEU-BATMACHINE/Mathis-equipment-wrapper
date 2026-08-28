"""
Visualize the knowledge graph

It is assumed that all nodes have exactly one rdfs:label defined to them
"""

from pathlib import Path
from pyvis.network import Network
from rdflib.graph import Graph
from rdflib.extras.external_graph_libs import rdflib_to_networkx_multidigraph
import networkx as nx


# Query to find all process that might point to participants
QUERY_VIEW1 = """
PREFIX emmo: <https://w3id.org/emmo#>

SELECT DISTINCT ?process ?processlabel ?participant ?participantlabel WHERE {
    # process isA TechnologyProcess
    ?process a ?type .
    ?type rdfs:subClassOf* emmo:EMMO_2b9cbfb5_dbd0_4a68_9c6f_acc41b40dd72 .

    ?process rdfs:label ?processlabel .

    # process hasTemporaryParticipant participant
    OPTIONAL {
        ?process emmo:EMMO_35c29eb6_f57e_48d8_85af_854f9e926e77 ?participant .
        ?participant rdfs:label ?participantlabel .
    }
}
"""

# Query to find all equipment and their devices.
QUERY_VIEW2_1 = """
PREFIX : <http://example.org/ontology/coater#>
PREFIX emmo: <https://w3id.org/emmo#>

SELECT DISTINCT ?equipment ?equipmentlabel ?device ?devicelabel WHERE {
    # ManufacturingEquipment hasPart ManufacturingDevice
    ?equipment a ?equipment_type ;
               :hasDevice ?device ;
               rdfs:label ?equipmentlabel .

    ?equipment_type rdfs:subClassOf* :ManufacturingEquipment .

    ?device a ?device_type .
    ?device_type rdfs:subClassOf* :ManufacturingDevice .

    ?device rdfs:label ?devicelabel .
}
"""

# Query to find all process that point to equipment/device
QUERY_VIEW2_2 = """
PREFIX : <http://example.org/ontology/coater#>
PREFIX emmo: <https://w3id.org/emmo#>

SELECT DISTINCT ?process ?processlabel ?participant ?participantlabel WHERE {
    # process isA TechnologyProcess
    ?process a ?type .
    ?type rdfs:subClassOf* emmo:EMMO_2b9cbfb5_dbd0_4a68_9c6f_acc41b40dd72 .

    ?process rdfs:label ?processlabel .

    # process hasTemporaryParticipant participant
    ?process emmo:EMMO_35c29eb6_f57e_48d8_85af_854f9e926e77 ?participant .

    # Verify participant type
    VALUES ?allowed_participant_types { :ManufacturingDevice :ManufacturingEquipment }
    ?participant a ?participant_type .
    ?participant_type rdfs:subClassOf* ?allowed_participant_types .

    ?participant rdfs:label ?participantlabel .
}
"""

# Query to find all equipment and their devices.
QUERY_VIEW1_NEXT = """
PREFIX : <http://example.org/ontology/coater#>
PREFIX emmo: <https://w3id.org/emmo#>

SELECT DISTINCT ?processSource ?processSourcelabel ?processNext ?processNextlabel WHERE {
    # process isA TechnologyProcess
    #?processSource a ?type .
    #?type rdfs:subClassOf* emmo:EMMO_2b9cbfb5_dbd0_4a68_9c6f_acc41b40dd72 .
    ?processSource rdfs:label ?processSourcelabel .
    #?processNext a ?type .
    ?processNext rdfs:label ?processNextlabel .

    # process hasTemporaryParticipant participant
    ?processSource emmo:EMMO_499e24a5_5072_4c83_8625_fe3f96ae4a8d ?processNext .
}
"""

# Query to find the data for the device description
QUERY_DEVICE_1 = """
PREFIX : <http://example.org/ontology/coater#>
PREFIX emmo: <https://w3id.org/emmo#>

SELECT DISTINCT ?process ?processlabel ?participant ?participantlabel WHERE {
    # process isA TechnologyProcess
    ?process a ?type .
    ?type rdfs:subClassOf* emmo:EMMO_2b9cbfb5_dbd0_4a68_9c6f_acc41b40dd72 .

    ?process rdfs:label ?processlabel .

    # process hasTemporaryParticipant participant
    ?process emmo:EMMO_35c29eb6_f57e_48d8_85af_854f9e926e77 ?participant .

    # Verify participant type
    VALUES ?allowed_participant_types { :ManufacturingDevice :ManufacturingEquipment }
    ?participant a ?participant_type .
    ?participant_type rdfs:subClassOf* ?allowed_participant_types .

    ?participant rdfs:label ?participantlabel .
}
"""


class KnowledgeGraph:
    def __init__(self, data: Path | str | bytes = "",graph: Graph = None):
        # Parse triples and infer relations
        if graph is not None:
            self.graph = graph
        else:
            g = Graph()
            g.parse(data)
            g.parse("https://emmo-repo.github.io/versions/1.0.0-beta7/emmo-inferred.ttl")
            self.graph = g

        # Define networkx graph
        d = rdflib_to_networkx_multidigraph(self.graph, edge_attrs=self._edge_attrs)
        self.digraph = d

        #TODO: add the possibility to provide the graph coming from elsewhere

    def _edge_attrs(self, s, p, o):
        return dict(key=p, title=p)
    
    def set_output_folder(self,outputfolder:Path):
        """
        set the path to the output folder
        """
        self.output_folder = outputfolder

    def view_process(self):
        """ Change view to all processes """

        print("--------------Process view----------------")
        g = nx.DiGraph()

        res = self.graph.query(QUERY_VIEW1)
        for row in res:
            g.add_node(row.processlabel, title=row.process, group=1)
            if row.participant:
                print(f"{row.process} -> {row.participant}")
                g.add_node(row.participantlabel, title=row.participant, group=2)
                g.add_edge(row.processlabel, row.participantlabel, title="hasTemporaryParticipant")
            else:
                print(f"{row.process}")

        print(g.nodes)

        # add the edges for the next process
        res = self.graph.query(QUERY_VIEW1_NEXT)
        print("---------------------------------------------")
        for row in res:
            if row.processSourcelabel in g.nodes:
                print(f"Node '{row.processSourcelabel}' exists and will be used.")
            else:
                print(f"Node '{row.processSourcelabel}' does NOT exist. Check for mismatches.")
            print(f"{row.processSourcelabel} -> {row.processNextlabel}")
            g.add_edge(row.processSourcelabel, row.processNextlabel, title="hasNext")

        self.digraph = g

    def view_device(self):
        """ Change view to all processes """

        g = nx.DiGraph()

        res = self.graph.query(QUERY_DEVICE_1)
        for row in res:
            g.add_node(row.processlabel, title=row.process, group=1)
            if row.participant:
                print(f"{row.process} -> {row.participant}")
                g.add_node(row.participantlabel, title=row.participant, group=2)
                g.add_edge(row.processlabel, row.participantlabel, title="hasTemporaryParticipant")
            else:
                print(f"{row.process}")

        self.digraph = g

    def view_equipment(self):
        """ Change view to all equipments """
        g = nx.DiGraph()

        # SELECT DISTINCT ?equipment ?equipmentlabel ?device ?devicelabel
        res = self.graph.query(QUERY_VIEW2_1)
        for row in res:
            print(f"{row.equipment} -> {row.device}")
            g.add_node(row.equipmentlabel, title=row.equipment, group=2)
            g.add_node(row.devicelabel, title=row.device, group=3,url=self.get_filepath(row.devicelabel).as_uri())
            g.add_edge(row.equipmentlabel, row.devicelabel, title="hasDevice")

        # SELECT DISTINCT ?process ?processlabel ?participant ?participantlabel
        res = self.graph.query(QUERY_VIEW2_2)
        for row in res:
            # If a process points to a node not related to equipment 
            # defined by QUERY_VIEW2_1 (above), then skip
            if not g.has_node(row.participantlabel):
                continue
            print(f"{row.process} -> {row.participant}")
            g.add_node(row.processlabel, title=row.process, group=1,url=self.get_filepath("process").as_uri())
            g.add_edge(row.processlabel, row.participantlabel, title="hasTemporaryParticipant")

        self.digraph = g

    def html(self):
        net = Network(cdn_resources="in_line", directed=True)
        net.from_nx(self.digraph)
        net.generate_html()
        # Set Pyvis network options (JSON configuration)
        net.set_options("""
        {
            "nodes": {
                "shape": "dot",
                "size": 20,
                "font": {
                    "size": 14
                }
            },
            "interaction": {
                "navigationButtons": true,
                "keyboard": true
            }
        }
        """)
        # Custom JavaScript to handle double-click event
        custom_js = """
        <script type="text/javascript">
            document.addEventListener("DOMContentLoaded", function() {
                network.on("doubleClick", function(params) {
                    if (params.nodes.length > 0) {
                        var nodeId = params.nodes[0];
                        var node = nodes.get(nodeId); // Access node data
                        if (node.url) {
                            window.open(node.url, '_blank'); // Open the URL in a new tab
                        }
                    }
                });
            });
        </script>
        """
        html_content = net.html
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{custom_js}\n</body>")

        #image map:
        content_map = """
        <!-- Display the image and associate it with the map -->
        <img src="../process_steps_diagram.png" usemap="#image-map" alt="Process steps Image" width="608" height="125">

        <!-- Define the image map -->
        <map name="image-map">
            <!-- Rectangle area -->
            <area shape="rect" coords="17,7,131,115" href="https://yahoo.fr" alt="Rectangle Area" target="_blank">
            <!-- Rectangle area -->
            <area shape="rect" coords="166,7,315,115" href="https://google.com" alt="Rectangle Area" target="_blank">
            <!-- Rectangle area -->
            <area shape="rect" coords="346,7,449,115" href="https://bing.fr" alt="Rectangle Area" target="_blank">
            
        </map>
        """

        if "<body>" in html_content:
            html_content = html_content.replace("<body>", f"<body>\n{content_map}")
        return html_content
    
    def html_write(self,label):
        """
        write the html file
        """
        outfile1 = self.get_filepath(label=label)
        outfile1.write_bytes(self.html().encode())


    def network_data(self):
        """ Returns a list of nodes and a list of edges """
        net = Network(directed=True)
        net.from_nx(self.digraph)
        return dict(nodes=net.nodes, edges=net.edges)

    def get_filepath(self,label):
        """
        get the uri
        """
        filepath = self.output_folder / f"view_{label}.html"
        return filepath
    