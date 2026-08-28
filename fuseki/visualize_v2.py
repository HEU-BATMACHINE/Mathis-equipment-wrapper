#!/usr/bin/env python
"""
Generate an interactive HTML network out of a knowledge graph.

• Hover on a node   → shows short summary.
• Click  on a node  → opens a modal with full details.

"""

import json
from pathlib import Path
from pyvis.network import Network

from fuseki.queries import (
    query_components_of_device,
    query_instance_of_coaterdryerdevice,
    query_instance_of_mixerdevice,
    query_device_measurements,
    query_subdevices_of_device,
    query_subparts_of_device,
    query_device_controls,
)
from fuseki.visualize import KnowledgeGraph


def formulate_coaterdryer_node(res_row):
    """
    ?dewviceid ?devicelabel ?devicemodel ?substratewidth ?maxcoatspeed ?comment
    """
    dict_node = {
        "id": res_row.deviceid,
        "label": res_row.devicelabel,
        "summary": f"Coater and dryer equipment: model {res_row.devicemodel}",
        "details": f"""<h3>{res_row.devicelabel}</h3>
        <p>Status: Online</p>
        <p><b>ID</b>: {res_row.deviceid}</p>
        <p><b>Equipment description</b>: {res_row.comment}</p>
        <p><b>Characteristics:</b></p>
        <ul>
              <li>Substrate Width: {res_row.substratewidth} mm</li>
              <li>Max coating speed: {res_row.maxcoatspeed} mm/s</li>
        </ul>""",
        }
    return dict_node

def formulate_device_node_basic(res_row):
    """
    ?deviceid ?devicelabel ?devicemodel ?comment
    """
    dict_node = {
        "id": res_row.deviceid,
        "label": res_row.devicelabel,
        "details": f"""<h3>{res_row.devicelabel}</h3>
        <p>Status: Online</p>
        <p><b>ID</b>: {res_row.deviceid}</p>
        <p><b>Equipment description</b>: {res_row.comment}</p>
        """,
        }
    if res_row.devicemodel is None:
        dict_node["summary"]= f"Device model unknown",
    else:
        dict_node["summary"]= f"Device model {res_row.devicemodel}",
    return dict_node

def append_coaterdryer_characteristics(dict_node,res_row):
    """
    ?substratewidth ?maxcoatspeed
    """
    dict_node["details"] += f"""
        <p><b>Characteristics:</b></p>
        <ul>
              <li>Substrate Width: {res_row.substratewidth} mm</li>
              <li>Max coating speed: {res_row.maxcoatspeed} mm/s</li>
        </ul>"""
    
    return dict_node

def append_mixer_characteristics(dict_node,res_row):
    """
    ?mixingcapacity ?mixingeffvolume
    """
    dict_node["details"] += f"""
        <p><b>Characteristics:</b></p>
        <ul>
              <li>Mixing Capacity: {res_row.mixingcapacity} L</li>
              <li>Mixing Effective Volume: {res_row.mixingeffvolume} L</li>
        </ul>"""
    
    return dict_node

def append_measurement(dict_node,res_row):
    """
    ?channelname ?channeltype ?channelunit
    the channel name has been changed to value so we need to use the output cleaned
    """
    name = res_row.output.split("#")[-1]
    dict_node["details"] +=  \
        f"<p><b>Measure:</b> {name},    \
             <b>Type:</b> {res_row.channeltype},       \
             <b>Unit:</b> {res_row.channelunit}</p>\n"
    
    return dict_node

def append_control(dict_node,res_row):
    """
    ?channelname ?channeltype ?channelunit
    the channel name has been changed to value so we need to use the output cleaned
    """
    name = res_row.output.split("#")[-1]
    dict_node["details"] +=  \
        f"<p><b>Control:</b> {name},    \
             <b>Type:</b> {res_row.channeltype},       \
             <b>Unit:</b> {res_row.channelunit}</p>\n"
    
    return dict_node


def fetch_nodes(g,device_type="coaterdryer"):
    """
    Return a list of dicts with id, label, summary, and details for coaterdryer devices.
    """
    list_nodes = []
    list_edges = []
    # search for an instance of http://example.org/ontology/coater#CoaterDryerEquipment
    # function to run this query
    if device_type == "coaterdryer":
        query = query_instance_of_coaterdryerdevice()
        res = g.graph.query(query)
        print(len(res)," coaterdryer devices found.")
    elif device_type == "mixer":
        query = query_instance_of_mixerdevice()
        res = g.graph.query(query)
        print(len(res)," mixer devices found.")
    else:
        raise ValueError(f"Unsupported device type: {device_type}")
    

    for row in res:
        # formulate node and properties
        #dict_node = formulate_coaterdryer_node(row)
        dict_node = formulate_device_node_basic(row)
        if device_type == "coaterdryer":
            dict_node = append_coaterdryer_characteristics(dict_node,row)
        elif device_type == "mixer":
            dict_node = append_mixer_characteristics(dict_node,row)

        # get data on measurements for this device
        query3 = query_device_measurements(row.deviceid)
        res3 = g.graph.query(query3)
        #print(query3)
        print("found ",len(res3)," measurements for device ",row.deviceid)
        #print(res3)
        for row3 in res3:
            dict_node = append_measurement(dict_node,row3)
        print("adding node: ",dict_node["id"])
        list_nodes.append(dict_node)
        

        # get the nodes from the subdevices
        query2 = query_subdevices_of_device(row.deviceid)
        res2 = g.graph.query(query2)
        print("found ",len(res2)," subdevices for device ",row.deviceid)
        for row2 in res2:
            dict_node = formulate_device_node_basic(row2)
            # get data on measurements for this device
            query3 = query_device_measurements(row2.deviceid)
            res3 = g.graph.query(query3)
            print("found ",len(res3)," measurements for device ",row2.deviceid)
            for row3 in res3:
                dict_node = append_measurement(dict_node,row3)
            # get data on controls for this device
            query3b = query_device_controls(row2.deviceid)
            res3b = g.graph.query(query3b)
            print("found ",len(res3b)," controls for device ",row2.deviceid)
            for row3b in res3b:
                dict_node = append_control(dict_node,row3b)
            list_nodes.append(dict_node)
            list_edges.append({"src": row.deviceid, "dst": row2.deviceid, "label": "hasDevice"})
            print("adding node: ",dict_node["id"])

            # second depth search
            query4 = query_subparts_of_device(row2.deviceid)
            res4 = g.graph.query(query4)
            print("found ",len(res4)," subparts for device ",row2.deviceid)
            for row4 in res4:
                dict_node = formulate_device_node_basic(row4)
                # get data on measurements for this device
                query5 = query_device_measurements(row4.deviceid)
                res5 = g.graph.query(query5)
                for row5 in res5:
                    dict_node = append_measurement(dict_node,row5)
                #get data on controls for this device
                query5b = query_device_controls(row4.deviceid)
                res5b = g.graph.query(query5b)
                for row5b in res5b:
                    dict_node = append_control(dict_node,row5b)
                list_nodes.append(dict_node)
                list_edges.append({"src": row2.deviceid, "dst": row4.deviceid, "label": "hasPart"})
                print("adding node: ",dict_node["id"])

                # third level depth search
                query6 = query_subparts_of_device(row4.deviceid)
                res6 = g.graph.query(query6)
                print("found ",len(res6)," subparts for device ",row4.deviceid)
                for row6 in res6:
                    dict_node = formulate_device_node_basic(row6)
                    # get data on measurements for this device
                    query7 = query_device_measurements(row6.deviceid)
                    res7 = g.graph.query(query7)
                    for row7 in res7:
                        dict_node = append_measurement(dict_node,row7)
                    # get data on controls for this device
                    query7b = query_device_controls(row6.deviceid)
                    res7b = g.graph.query(query7b)
                    for row7b in res7b:
                        dict_node = append_control(dict_node,row7b) 
                    list_nodes.append(dict_node)
                    list_edges.append({"src": row4.deviceid, "dst": row6.deviceid, "label": "hasPart"})
                    print("adding node: ",dict_node["id"])
                #check for components of the subpart
                query8 = query_components_of_device(row4.deviceid)
                res8 = g.graph.query(query8)
                print("found ",len(res8)," components for device ",row4.deviceid)
                for row8 in res8:
                    dict_node = formulate_device_node_basic(row8)
                    # get data on measurements for this device
                    query9 = query_device_measurements(row8.deviceid)
                    res9 = g.graph.query(query9)
                    for row9 in res9:
                        dict_node = append_measurement(dict_node,row9)
                    # get data on controls for this device
                    query9b = query_device_controls(row8.deviceid)
                    res9b = g.graph.query(query9b)
                    for row9b in res9b:
                        dict_node = append_control(dict_node,row9b)
                    list_nodes.append(dict_node)
                    list_edges.append({"src": row4.deviceid, "dst": row8.deviceid, "label": "hasComponent"})
                    print("adding node: ",dict_node["id"])





    # look for device attached to it with predicate http://example.org/ontology/coater#hasDevice

    return list_nodes,list_edges


def fetch_edges_v0():
    """Return list of edge dicts with src, dst and optional label."""
    return [
        {"src": 1, "dst": 2, "label": "works at"},
        {"src": 1, "dst": 3, "label": "author of"},
        {"src": 2, "dst": 3, "label": "funded"},
    ]

def fetch_edges():
    """Return list of edge dicts with src, dst and optional label."""
    return []


###############################################################################
# 2. Graph builder
###############################################################################
def build_graph(nodes, edges, outfile="graph.html"):
    """Create an interactive html file."""
    net = Network(
        height="750px",
        width="100%",
        #bgcolor="#ffffff",
        font_color="black",
        directed=True,
    )

    """net.force_atlas_2based(
        gravity            = -30,
        central_gravity    = 0.01,
        spring_length      = 220,
        spring_strength    = 0.08,
        damping            = 0.4,
        overlap            = 1          # 0‑1; 1 means "try hard not to overlap"
    )"""

    net.repulsion(
        node_distance      = 800,   # ⬅️ try 150‑300 until labels stop colliding
        central_gravity    = 0.15,
        spring_length      = 400,
        spring_strength    = 0.05,
        damping            = 0.09
    )

    # Global vis‑js options (tweak sizes/colors here if you like)
    vis_opts = {
    "nodes": {
        "shape": "dot",
        "size": 18,
        "font": {"size": 14},
        "borderWidth": 2
    },
    "edges": {
        "arrows": {"to": {"enabled": True, "scaleFactor": 0.8}},
        "smooth": {"type": "dynamic"}
    },
    "interaction": {"hover": True, "multiselect": True}
    }

    net.set_options(json.dumps(vis_opts))

    # Add nodes
    for n in nodes:
        net.add_node(
            n["id"],
            label=n["label"],
            title=n["summary"],   # shows on hover
            shape="dot",
        )

    # Add edges
    for e in edges:
        net.add_edge(
            e["src"],
            e["dst"],
            #label=e.get("label", ""),
            title=e.get("label", ""),
        )

    # Write base html
    net.save_graph(str(outfile))

    # Inject header
    inject_header(outfile)

    # Inject modal + click‑handler JS
    inject_modal(outfile, nodes)


###############################################################################
# 3. HTML post‑processing – header and lightweight modal window
###############################################################################

def inject_header(html_path: str | Path) -> None:
    """
    Insert `header_html` (any HTML) right after the opening <body> tag
    of the file at `html_path`.
    """
    html_path = Path(html_path)
    html      = html_path.read_text(encoding="utf8")

    content_map = """
        <!-- Display the image and associate it with the map -->
        <img src="../coaterdryer_steps_diagram.png" usemap="#image-map" alt="Process steps Image" width="608" height="125">

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

    # Insert once, right after <body>
    html = html.replace("<body>",  f"<body>\n{content_map}")

    html_path.write_text(html, encoding="utf8")


def inject_modal(html_path: str | Path, nodes: list[dict]):
    """Append a modal template & click handler to the Vis.js html."""
    html_path = Path(html_path)
    html = html_path.read_text(encoding="utf8")

    # Map id → details (ready for JS)
    details_js = json.dumps({n["id"]: n["details"] for n in nodes})

    # Extra HTML & JS
    addon = f"""
<!-- ─── Node‑detail modal (auto‑injected) ─────────────────────────────── -->
<style>
.modal {{
  display:none; position:fixed; z-index:1000; left:0; top:0;
  width:100%; height:100%; overflow:auto;
  background:rgba(0,0,0,0.4);
}}
.modal-content {{
  background:#fff; margin:10% auto; padding:20px; border:1px solid #888;
  width:60%; border-radius:8px; max-width:700px;
}}
.modal-close {{
  float:right; font-size:1.2rem; font-weight:bold; cursor:pointer;
}}
</style>

<div id="detailModal" class="modal">
  <div class="modal-content">
    <span id="modalClose" class="modal-close">&times;</span>
    <div id="modalBody"></div>
  </div>
</div>

<script type="text/javascript">
const nodeDetails = {details_js};

function showModal(html) {{
  const modal      = document.getElementById("detailModal");
  const modalBody  = document.getElementById("modalBody");
  modalBody.innerHTML = html;
  modal.style.display = "block";
}}

function hideModal() {{
  document.getElementById("detailModal").style.display = "none";
}}

document.getElementById("modalClose").onclick = hideModal;
window.onclick = (event) => {{
  const modal = document.getElementById("detailModal");
  if (event.target === modal) hideModal();
}};

// Hook into pyvis / Vis.js
// 'network' is the Vis Network instance injected by pyvis
network.on("click", function(params) {{
  if (params.nodes.length > 0) {{
    const id = params.nodes[0];
    if (nodeDetails[id]) {{
      showModal(nodeDetails[id]);
    }}
  }}
}});
</script>
<!-- ───────────────────────────────────────────────────────────────────── -->
"""

    # Insert before closing </body>
    html = html.replace("</body>", addon + "\n</body>")
    html_path.write_text(html, encoding="utf8")
