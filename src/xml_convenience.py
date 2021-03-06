# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/YANG-to-Redfish-Converter/blob/master/LICENSE.md

from xml.etree.ElementTree import Element, SubElement, Comment, tostring

def add_import(xml_node, import_value, alias):
    """
    Add import stament node into XML.
    :param xml_node:Parent node to which 'import' node must be added.
    :param import_value: The name of the imported file
    :param alias: Optional alias for the imported file.
    """
    uri = 'http://redfish.dmtf.org/schemas/v1/' + import_value + ".xml"
    for ref in xml_node:
        if 'Reference' not in str(ref.tag):
            continue
        uri_old = ref.attrib.get('Uri')
        if uri_old == uri:
            return
    namespace = import_value
    add_reference(xml_node, uri, namespace, alias)


def add_reference(xml_node, uri, namespace, alias=None):
    """
    Add "edmx:Reference" node to XML.
    :param xml_node:Parent node to which reference  node must be added.
    :param uri: URI which will be added as the reference
    :param namespace: XML namespace or namespaces
    :param alias: Optional alias
    """
    ref = SubElement(xml_node, 'edmx:Reference')
    ref.set('Uri', uri)
    include = SubElement(ref, 'edmx:Include')
    if alias is not None:
        include.set('Alias', alias)
    include.set('Namespace', namespace)
    return xml_node


def add_references(xml_node, uri, entries):
    """
    Add "edmx:Reference" node to XML.
    :param xml_node: Parent node to which reference  node must be added.
    :param uri: URI which will be added as the reference
    :param entries: Dictionary of namespace-alias pairs
    """
    ref = SubElement(xml_node, 'edmx:Reference')
    ref.set('Uri', uri)
    for namespace, alias in entries.items():
        include = SubElement(ref, 'edmx:Include')
        if alias not in [None, '']:
            include.set('Alias', alias)
        include.set('Namespace', namespace)
    return xml_node


def add_list_reference(xml_node, uri, namespace, alias):
    ref = SubElement(xml_node, 'edmx:Reference')
    ref.set('Uri', uri)
    ref.set('Namespace' , namespace + '.xml')
    include = SubElement(ref, 'edmx:Include')
    if alias is not None:
        include.set('Alias', alias)
    if namespace is not None:
        include.set('Namespace', namespace)
    return xml_node


def add_CSDL_Headers(is_singleton=False):
    """
    Add standard CSDL tags/references which are common across all the CSDL
    XML files.
    :param xml_node:Parent node to which headers must be added.
    """
    xml_node = Element('edmx:Edmx')
    xml_node.set('Version', '4.0')
    xml_node.set('xmlns:edmx', 'http://docs.oasis-open.org/odata/ns/edmx')

    add_reference(xml_node,
            'http://docs.oasis-open.org/odata/odata/v4.0/errata03/csd01/complete/vocabularies/Org.OData.Core.V1.xml',
            'Org.OData.Core.V1', 'OData')
    add_reference(xml_node,
            'http://docs.oasis-open.org/odata/odata/v4.0/errata03/csd01/complete/vocabularies/Org.OData.Capabilities.V1.xml',
            'Org.OData.Capabilities.V1', 'Capabilities')
    if is_singleton:
        add_references(xml_node,
                'http://redfish.dmtf.org/schemas/v1/RedfishExtensions_v1.xml',
                {'RedfishExtension.v1_0_0': 'Redfish', 'Validation.v1_0_0': 'Validation'})
        add_reference(xml_node,
                'http://redfish.dmtf.org/schemas/v1/RedfishYangExtensions_v1.xml',
                      'RedfishYangExtension.v1_0_0', 'RedfishYang')
    return xml_node


def add_annotation(xml_node, key_values):
    """
    Add node of type "Annotation" to the XML
    :param xml_node: Node to which Annotations have to be addeed.
    :param key_values: Key value pairs which will be used to create the
    annotation entries.
    """
    annotation = SubElement(xml_node, 'Annotation')
    for key in key_values.keys():
        annotation.set(key, key_values[key])
    return annotation

def add_collection_annotation(xml_node, key_values, record_props):
    annotation = SubElement(xml_node, 'Annotation')
    for key in key_values.keys():
        annotation.set(key, key_values[key])
    record = SubElement(annotation, 'Record')
    for key in record_props.keys():
        record_property =  SubElement(record, "PropertyValue")
        record_property.set('Property', key)
        record_property.set('Bool', record_props[key])
    return annotation
