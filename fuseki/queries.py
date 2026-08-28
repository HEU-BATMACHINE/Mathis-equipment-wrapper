# Query to find all instances of a device type
def query_instance_of_device(device_name:str,namespace:str):
    """
    Generic function to get device characteristics
    #TODO add getting all the properties
    """
    QUERY = f"""
    PREFIX equipment: <https://w3id.org/batteryequipment/public/ontology#>
    PREFIX coater: <https://w3id.org/coater/public/ontology#>
    PREFIX emmo: <https://w3id.org/emmo#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?deviceid ?devicelabel ?devicemodel ?comment
    WHERE {{
        ?deviceid  a {namespace}:{device_name} ;
                    rdfs:label ?devicelabel .
        OPTIONAL {{
            ?deviceid equipment:hasEquipmentModel ?devicemodel .
        }}
        {namespace}:{device_name} rdfs:comment ?comment .

    }}
    """
    return QUERY


def query_instance_of_coaterdryerdevice():
    """
    Query to get the information for a coaterdryerdevice
    """
    QUERY = """
    PREFIX equipment: <https://w3id.org/batteryequipment/public/ontology#>
    PREFIX coater: <https://w3id.org/coater/public/ontology#>
    PREFIX emmo: <https://w3id.org/emmo#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?deviceid ?devicelabel ?devicemodel ?substratewidth ?maxcoatspeed ?comment
    WHERE {
        ?deviceid  a coater:CoaterDryerEquipment ;
                    equipment:hasEquipmentModel ?devicemodel ;
                    coater:hasSubstrateWidth ?substratewidth ;
                    coater:hasCoatingSpeedMax ?maxcoatspeed ;
                    rdfs:label ?devicelabel .

        coater:CoaterDryerEquipment rdfs:comment ?comment .

    }
    """
    return QUERY


def query_instance_of_mixerdevice():
    """
    Query to get the information for a mixer device
    """
    QUERY = """
    PREFIX equipment: <https://w3id.org/batteryequipment/public/ontology#>
    PREFIX coater: <https://w3id.org/coater/public/ontology#>
    PREFIX mixer: <https://w3id.org/mixer/public/ontology#>
    PREFIX emmo: <https://w3id.org/emmo#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?deviceid ?devicelabel ?devicemodel ?mixingcapacity ?mixingeffvolume ?comment
    WHERE {
        ?deviceid  a mixer:MixerEquipment ;
                    equipment:hasEquipmentModel ?devicemodel ;
                    mixer:hasMixerTotalCapacity ?mixingcapacity ;
                    mixer:hasMixerEffectiveVolume ?mixingeffvolume ;
                    rdfs:label ?devicelabel .

        mixer:MixerEquipment rdfs:comment ?comment .

    }
    """
    return QUERY

def query_subdevices_of_device(maindeviceid:str):
    """
    Query to get the list of subdevice for a device
    """
    QUERY = f"""
    PREFIX equipment: <https://w3id.org/batteryequipment/public/ontology#>
    PREFIX coater: <https://w3id.org/coater/public/ontology#>
    PREFIX emmo: <https://w3id.org/emmo#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?deviceid ?devicelabel ?devicemodel ?comment 
    WHERE {{
        <{maindeviceid}>  equipment:hasDevice ?deviceid .
        ?deviceid rdfs:label ?devicelabel .
        OPTIONAL {{
            ?deviceid equipment:hasEquipmentModel ?devicemodel .
        }}
        ?deviceid a ?device_name .
        ?device_name rdfs:comment ?comment .
    }}
    """
    return QUERY

def query_components_of_device(maindeviceid:str):
    """
    Query to get the list of components for a device
    """
    QUERY = f"""
    PREFIX equipment: <https://w3id.org/batteryequipment/public/ontology#>
    PREFIX coater: <https://w3id.org/coater/public/ontology#>
    PREFIX emmo: <https://w3id.org/emmo#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?deviceid ?devicelabel ?devicemodel ?comment 
    WHERE {{
        <{maindeviceid}>  equipment:hasComponent ?deviceid .
        ?deviceid rdfs:label ?devicelabel .
        OPTIONAL {{
            ?deviceid equipment:hasEquipmentModel ?devicemodel .
        }}
        ?deviceid a ?device_name .
        ?device_name rdfs:comment ?comment .
    }}
    """
    return QUERY

def query_subparts_of_device(maindeviceid:str):
    """
    Query to get the list of subdevice for a device
    hasPArt: EMMO_17e27c22_37e1_468c_9dd7_95e137f73e7f
    """
    QUERY = f"""
    PREFIX equipment: <https://w3id.org/batteryequipment/public/ontology#>
    PREFIX coater: <https://w3id.org/coater/public/ontology#>
    PREFIX emmo: <https://w3id.org/emmo#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?deviceid ?devicelabel ?devicemodel ?comment 
    WHERE {{
        <{maindeviceid}>  emmo:EMMO_17e27c22_37e1_468c_9dd7_95e137f73e7f ?deviceid .
        ?deviceid rdfs:label ?devicelabel .
        OPTIONAL {{
            ?deviceid equipment:hasEquipmentModel ?devicemodel .
        }}
        ?deviceid a ?device_name .
        ?device_name rdfs:comment ?comment .
    }}
    """
    return QUERY

def query_device_measurements(deviceid):
    """
    Recover information about a device measurements
    Return channelname, channeltype, channelunit
    """
    QUERY = f"""
    PREFIX coater: <https://w3id.org/coater/public/ontology#>
    PREFIX emmo: <https://w3id.org/emmo#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX chameo: <https://w3id.org/emmo/domain/characterisation-methodology/chameo#>
    PREFIX csvw: <http://www.w3.org/ns/csvw#>

    SELECT DISTINCT ?channelname ?channeltype ?channelunit ?output
    WHERE {{
        ?measurementprocess chameo:hasMeasurementSample <{deviceid}> .
        ?measurementprocess emmo:EMMO_c4bace1d_4db0_4cd3_87e9_18122bae2840 ?output .
        ?output csvw:tableSchema ?schema .
        ?schema csvw:columns ?column .
        ?column csvw:name ?channelname .
        ?column csvw:datatype "number" .
        ?column emmo:EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569 ?unit .
        ?unit <http://www.w3.org/2004/02/skos/core#prefLabel> ?channelunit .
        ?column csvw:propertyUrl ?property .
        ?property rdfs:range ?class .
        ?class <http://www.w3.org/2004/02/skos/core#prefLabel> ?channeltype .
    }}
    """
    return QUERY


def query_device_controls(deviceid):
    """
    Recover information about a device controls
    Return channelname, channeltype, channelunit
    """
    QUERY = f"""
    PREFIX coater: <https://w3id.org/coater/public/ontology#>
    PREFIX emmo: <https://w3id.org/emmo#>
    PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX chameo: <https://w3id.org/emmo/domain/characterisation-methodology/chameo#>
    PREFIX csvw: <http://www.w3.org/ns/csvw#>

    SELECT DISTINCT ?channelname ?channeltype ?channelunit ?output
    WHERE {{
        ?controlprocess chameo:hasInteractionWithSample <{deviceid}> .
        ?controlprocess emmo:EMMO_36e69413_8c59_4799_946c_10b05d266e22 ?output .
        ?output csvw:tableSchema ?schema .
        ?schema csvw:columns ?column .
        ?column csvw:name ?channelname .
        ?column csvw:datatype "number" .
        ?column emmo:EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569 ?unit .
        ?unit <http://www.w3.org/2004/02/skos/core#prefLabel> ?channelunit .
        ?column csvw:propertyUrl ?property .
        ?property rdfs:range ?class .
        ?class <http://www.w3.org/2004/02/skos/core#prefLabel> ?channeltype .
    }}
    """
    return QUERY