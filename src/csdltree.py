# Copyright Notice:
# Copyright 2017 Distributed Management Task Force, Inc. All rights reserved.
# License: BSD 3-Clause License. For full text see link: https://github.com/DMTF/YANG-to-Redfish-Converter/blob/master/LICENSE.md

import redfishtypes
import statement_handlers as handlers
import xml_convenience
from xml.etree.ElementTree import Element, SubElement
from xml_content import XMLContent

# This file contains the build_tree function and handlers
# for YANG statements that would result in the build_tree being
# called - i.e Yang statements which could have container/list/
# leaflist/leaf as one of their sub statements.

# Prefix + name

def createCollectionXML(name, prefix=None):
    collection_name = name + "Collection"
    collection_xml_root = xml_convenience.add_CSDL_Headers(None)

    collection_xml_root = xml_convenience.add_reference(collection_xml_root,
            "http://redfish.dmtf.org/schemas/v1/Resource_v1.xml",
            "Resource.v1_0_0", None )

    collection_xml_root = xml_convenience.add_reference(collection_xml_root,
            "http://redfish.dmtf.org/schemas/v1/" + prefix + name + "_v1.xml",
            prefix + name, str(name) )

    collection_data_services_node = SubElement(
        collection_xml_root, 'edmx:DataServices')
    collection_schema_node = SubElement(collection_data_services_node, 'Schema')
    collection_schema_node.set("xmlns", "http://docs.oasis-open.org/odata/ns/edm")
    # should this namespace be truncated as well? (errata)
    collection_schema_node.set("Namespace", prefix + collection_name)
    collection_target = SubElement(collection_schema_node, "EntityType")

    collection_target.set('Name', collection_name.split('.')[-1])
    collection_target.set('BaseType' ,"Resource.v1_0_0.ResourceCollection")
    xml_convenience.add_annotation(collection_target, {"Term": "OData.Description", 
        "String": "A Collection of " + name + " resource instances." 
        })
    xml_convenience.add_collection_annotation(collection_target, {"Term":
        "Capabilities.InsertRestrictions"}, {"Insertable": "false"})
    xml_convenience.add_collection_annotation(collection_target, {"Term":
        "Capabilities.UpdateRestrictions"}, {"Updatable": "false"})
    xml_convenience.add_collection_annotation(collection_target, {"Term":
        "Capabilities.DeleteRestrictions"}, {"Deletable": "false"})

    nav_prop = SubElement(collection_target, 'NavigationProperty')
    nav_prop.set('Name', 'Members') 
    listname = name.split('.')[-1]
    # should this be without the namespace at all (errata)
    nav_prop.set('Type', 'Collection(' + prefix + listname + '.' + listname + ')')
    nav_prop.set('Nullable', 'false')
    xml_convenience.add_annotation(nav_prop, {'Term':'OData.Permissions',
        'EnumMember':'OData.Permissions/Read'})
    xml_convenience.add_annotation(nav_prop, {'Term':'OData.Description', 'String':'Contains \
members of this collection.'})
    xml_convenience.add_annotation(nav_prop, {'Term':'OData.AutoExpandReferences'})
    return collection_xml_root


def create_xml_base(csdlname, prefix=None):
    main_node = xml_convenience.add_CSDL_Headers(True)
    entity_node = None
    # add refs to main, then add data services node
    data_services_node = Element('edmx:DataServices')
    schema_node = SubElement(data_services_node, 'Schema')
    schema_node.set(
        'Namespace', prefix + csdlname + ".v1_0_0")
    schema_node.set(
        'xmlns', 'http://docs.oasis-open.org/odata/ns/edm')
    # add in first schema
    schema_node_og = Element('Schema')
    schema_node_og.set('Namespace', prefix + csdlname)
    schema_node_og.set(
        'xmlns', 'http://docs.oasis-open.org/odata/ns/edm')
    data_services_node.insert(0, schema_node_og)

    schema1_entity = SubElement(schema_node_og, 'EntityType')
    schema1_entity.set('Name', csdlname.split('.')[-1])
    schema1_entity.set('BaseType', 'Resource.v1_0_0.Resource')
    schema1_entity.set(
        'Abstract', str(True))
    xml_convenience.add_annotation(schema1_entity, {
                   'Term': 'OData.Description', 'String': 'Parameters for {}'.format(csdlname)})
    xml_convenience.add_annotation(schema1_entity, {
                   'Term': 'OData.LongDescription', 'String': 'Parameters for {}'.format(csdlname)})
    xml_convenience.add_collection_annotation(schema1_entity, {"Term":
        "Capabilities.InsertRestrictions"}, {"Insertable": "false"})
    xml_convenience.add_collection_annotation(schema1_entity, {"Term":
        "Capabilities.UpdateRestrictions"}, {"Updatable": "false"})
    xml_convenience.add_collection_annotation(schema1_entity, {"Term":
        "Capabilities.DeleteRestrictions"}, {"Deletable": "false"})
    return main_node, schema_node, data_services_node

#=======================================================
# Recursive function to handle containment statements
# such as container, list, leaf, leaflist.
# Other statements are handed off to respective handlers - handlers.handle_XXXXX
# defined in this file and in statement_handlers.py.

def build_tree_new(segment, list_of_xml, logger, prefix=None, topleveltypes=None, toplevelimports=None, parent=None, parent_schema=None, parent_entity=None):
    seg_type = str(type(segment))
    if topleveltypes == None:
        topleveltypes = dict()
    if toplevelimports == None:
        toplevelimports = dict()
    if seg_type in ['ModuleGrammar']:
        tag, name_tag, obrace, info, content, cbrace = segment.elements
        # what is this in particular (errata)
        csdlname = handlers.get_valid_csdl_identifier(name_tag.string.strip('"'))
        filename = csdlname + '_v1.xml'
        prefix = ""
        main_node, schema_node, data_services_node = create_xml_base(csdlname, prefix)
        entity_node = Element("EntityType")
        entity_node.set('Name', csdlname.split('.')[-1])
        entity_node.set('BaseType', csdlname.split('.')[-1]+'.'+csdlname.split('.')[-1])
        # ignore brace
        for item in info:
            build_tree_repeat(item, None, schema_node, main_node, list_of_xml, logger, topleveltypes=topleveltypes, toplevelimports=toplevelimports)
        for item in content:
            build_tree_repeat(item, entity_node, schema_node, main_node, list_of_xml, logger, csdlname + '.', topleveltypes=topleveltypes, toplevelimports=toplevelimports)

        schema_node.append(entity_node)
        main_node.append(data_services_node)
        xml_content = XMLContent()
        xml_content.set_filename(filename)
        xml_content.set_xml(main_node)
        list_of_xml.append(xml_content)
        return main_node

    if seg_type in ['ContainerGrammar']:
        tag, name_tag, obrace, content, cbrace, comment = segment.elements
        csdlname = handlers.get_valid_csdl_identifier(name_tag.string.strip('"'))
        filename = prefix + csdlname + '_v1.xml'
        main_node, schema_node, data_services_node = create_xml_base(csdlname, prefix)
        member = redfishtypes.get_node_types_mapping(str(type(tag)))
        entity_node = Element("EntityType")
        entity_node.set('Name', csdlname.split('.')[-1])
        entity_node.set('BaseType', prefix+csdlname.split('.')[-1]+'.'+csdlname.split('.')[-1])
        xml_convenience.add_annotation(
            entity_node, {'Term': 'RedfishYang.NodeType', 'EnumMember': member})
        for item in content:
            build_tree_repeat(item, entity_node, schema_node, main_node, list_of_xml, logger, prefix + csdlname + '.', topleveltypes=topleveltypes, toplevelimports=toplevelimports)

        schema_node.append(entity_node)
        main_node.append(data_services_node)
        xml_content = XMLContent()
        xml_content.set_filename(filename)
        xml_content.set_xml(main_node)
        list_of_xml.append(xml_content)
        return main_node

    if seg_type in ['ListGrammar']:
        tag, name_tag, obrace, content, cbrace = segment.elements
        csdlname = handlers.get_valid_csdl_identifier(name_tag.string.strip('"'))
        filename = prefix + csdlname + '_v1.xml'

        main_node, schema_node, data_services_node = create_xml_base(csdlname, prefix)
        member = redfishtypes.get_node_types_mapping(str(type(tag)))
        entity_node = Element("EntityType")
        entity_node.set('Name', csdlname.split('.')[-1])
        entity_node.set('BaseType', prefix+csdlname.split('.')[-1]+'.'+csdlname.split('.')[-1])
        xml_convenience.add_annotation(
            entity_node, {'Term': 'RedfishYang.NodeType', 'EnumMember': member})
        for item in content:
            build_tree_repeat(item, entity_node, schema_node, main_node, list_of_xml, logger, prefix + '.' + csdlname, topleveltypes=topleveltypes, toplevelimports=toplevelimports)
            
        schema_node.append(entity_node)
        main_node.append(data_services_node)
        xml_content = XMLContent()
        xml_content.set_filename(filename)
        xml_content.set_xml(main_node)
        list_of_xml.append(xml_content)
        
        collection_node = createCollectionXML(csdlname, prefix)
        csdlname = csdlname + 'Collection'
        filename = prefix + csdlname + '_v1.xml'
        xml_content = XMLContent()
        xml_content.set_filename(filename)
        xml_content.set_xml(collection_node)
        list_of_xml.append(xml_content)
        return collection_node

    if seg_type in ['LeafGrammar']:
        tag, name_tag, obrace, if_tag, content, cbrace = segment.elements
        target = Element("Property")
        member = redfishtypes.get_node_types_mapping(str(type(tag)))
        xml_convenience.add_annotation(
            target, {'Term': 'RedfishYang.NodeType', 'EnumMember': member})
        xml_convenience.add_annotation(
            target, {'Term': 'OData.Permissions', 'EnumMember': 'OData.Permission/Read'})
        csdlname = handlers.get_valid_csdl_identifier(name_tag.string.strip('"'))
        target.set(
            'Name', csdlname)
        for item in content:
            build_tree_repeat(item, parent_entity, target, parent, list_of_xml, logger, prefix + csdlname + '.', topleveltypes=topleveltypes, toplevelimports=toplevelimports)

        return target

    if seg_type in ['LeafListGrammar']:
        tag, name_tag, obrace, content, cbrace = segment.elements
        member = redfishtypes.get_node_types_mapping(str(type(tag)))
        csdlname = handlers.get_valid_csdl_identifier(name_tag.string.strip('"'))

        prop_node = Element("Property")
        prop_node.set(
            'Name', csdlname)
        prop_node.set(
            'BaseType', 'Collection({}.{})'.format(prefix + "v1_0_0", csdlname))
        xml_convenience.add_annotation(
            prop_node, {'Term': 'RedfishYang.NodeType', 'EnumMember': member})
        xml_convenience.add_annotation(
                prop_node, {'Term': 'OData.Permissions', 'EnumMember': 'OData.Permission/Read'})
        xml_convenience.add_annotation(prop_node, {"Term": "OData.LongDescription",
                "String": "List of the type {}".format(csdlname)}
                )
        for item in content:
            build_tree_repeat(item, parent_entity, prop_node, parent_schema, list_of_xml, logger, prefix + csdlname + '.', topleveltypes=topleveltypes, toplevelimports=toplevelimports)
        return prop_node
    return None


def build_tree_repeat(repeat_item, target_entity, target, target_parent, list_of_xml, logger, prefix='', topleveltypes=None, toplevelimports=None, additional_tags=None):
    # REPEAT(SubmoduleGrammar |  Namespace | AnyXML | YangVersion | Prefix | Import | Include | Organization | Contact | Description | RevisionGrammar, min=0),
    # REPEAT(Augment | Grouping | Identity | ContainerGrammar | ChoiceGrammar |
    #      RpcGrammar | Feature | TypedefGrammar | Deviation | Notification, min=0),
    # target_entity = tag of entitytype
    # target = tag of current target
    # target_parent = tag of its parent
    repeat_item_type = str(type(repeat_item))
    if topleveltypes is None:
        topleveltypes = dict()
    if toplevelimports is None:
        toplevelimports = dict()
    if additional_tags is None:
        additional_tags = list()

    logger.debug('Handling repeat item: ' + repeat_item_type)
    # top grammars
    if (repeat_item_type == 'ListGrammar' or repeat_item_type == 'ContainerGrammar'):
        this_node = build_tree_new(repeat_item, list_of_xml, logger, prefix, topleveltypes=topleveltypes, toplevelimports=toplevelimports)
        # Handle Container Grammar
        if repeat_item_type in ['ContainerGrammar']:
            tag, name_tag, obrace, content, cbrace, comment = repeat_item.elements
            csdlname = handlers.get_valid_csdl_identifier(name_tag.string.strip('"'))
            tname = csdlname.split('.')[-1]
            filename = prefix + csdlname + '_v1.xml'
            navigation_property = SubElement(
                target_entity, 'NavigationProperty')
            navigation_property.set('Name', tname + 'Container')
            navigation_property.set('Type', tname + '.' + tname)
            navigation_property.set('ContainsTarget', str(True))
            alias = csdlname.split('.')[-1]
            xml_convenience.add_reference(target_parent,
                "http://redfish.dmtf.org/schemas/v1/{}".format(filename),
                "{}{}".format(prefix, alias), alias)
        # Handle List Grammar
        if repeat_item_type in ['ListGrammar']:
            tag, name_tag, obrace, content, cbrace = repeat_item.elements
            csdlname = handlers.get_valid_csdl_identifier(name_tag.string.strip('"')) + 'Collection'
            tname = csdlname.split('.')[-1]
            filename = prefix + csdlname + '_v1.xml'
            navigation_property = SubElement(
                target_entity, 'NavigationProperty')
            navigation_property.set('Name', tname)
            navigation_property.set('Type', tname + '.' + tname)
            navigation_property.set('ContainsTarget', str(True))
            alias = csdlname.split('.')[-1]
            xml_convenience.add_reference(target_parent,
                "http://redfish.dmtf.org/schemas/v1/{}".format(filename),
                "{}{}".format(prefix, alias), alias)
        # At the end of the grammar, modify outside nav property
        xml_convenience.add_annotation(navigation_property, {
                'Term': 'OData.Permissions',
                'EnumMember': 'OData.Permissions/Read'
                })
        xml_convenience.add_annotation(navigation_property, {
                'Term': 'OData.Description',
                'String': 'Navigation property that points to a resource of {}.'.format(str(csdlname))
                })
        xml_convenience.add_annotation(navigation_property, {
                'Term': 'OData.LongDescription',
                'String': 'Automatically generated.'
                })
        xml_convenience.add_annotation(navigation_property, {
                'Term': 'AutoExpandReferences',
                })
        return navigation_property

    elif repeat_item_type == 'LeafGrammar' or repeat_item_type == 'LeafListGrammar':
        this_node = build_tree_new(repeat_item, list_of_xml, logger, prefix=prefix, parent=target_parent, parent_schema=target, parent_entity=target_entity, topleveltypes=topleveltypes, toplevelimports=toplevelimports)
        target_entity.append(this_node)
        return this_node

    elif (repeat_item_type == 'ChoiceGrammar'):
        logger.debug('Ignored tag: {}'.format(repeat_item_type))
        return
        handlers.handle_choice_grammar(
            repeat_item.elements, target, target_parent, xml_parent, list_of_xml, '', logger)

    # module_info
    elif repeat_item_type == 'SubmoduleGrammar':
        logger.info('Found submodule. Submodules are not currently supported.')

    elif repeat_item_type == 'Namespace':
        handlers.handle_namespace(repeat_item, target)

    elif repeat_item_type == 'AnyXML': # fix
        handlers.handle_anyxml(repeat_item, target, anyxml_count)
        anyxml_count = anyxml_count + 1

    elif repeat_item_type == 'YangVersion': # fix
        handlers.handle_yang_version(repeat_item, target)

    elif repeat_item_type == 'Include':  # Include not supported
        logger.debug('Ignored tag: {}'.format(repeat_item_type))
        pass

    elif repeat_item_type == 'Prefix':
        handlers.handle_prefix(repeat_item, target)

    elif repeat_item_type == 'ReferenceGrammar':
        handlers.handle_reference(repeat_item, target)

    elif (repeat_item_type == 'Organization' or repeat_item_type == 'Contact' or
          repeat_item_type == 'Description' or repeat_item_type == 'IfFeature' or
          repeat_item_type == 'Feature'):
        handlers.handle_descriptor(repeat_item, target if target is not None else target_entity)

    elif repeat_item_type == 'RevisionGrammar':
        handlers.handle_revision(repeat_item, target)

    elif repeat_item_type == 'Type':
        handlers.handle_type(repeat_item.elements, target, target_parent, target_entity, imports=toplevelimports, types=topleveltypes)

    elif repeat_item_type == 'TypedefGrammar':
        type_name, type_node = handlers.handle_typedef(repeat_item, target, target_parent)
        topleveltypes[type_name] = type_node

    elif repeat_item_type == 'Import':
        import_name, prefix_name = handlers.handle_import(repeat_item, target_parent)
        toplevelimports[prefix_name if prefix_name not in [None, ''] else import_name] = import_name

    # module_content
    elif repeat_item_type == 'Augment':
        logger.debug("Handling augment")
        xml_nodes_to_annotate = []
        xml_annotations = []
        augment_name = None
        augment_xml_node = xml_convenience.add_CSDL_Headers(None)
        main_node = SubElement(
            augment_xml_node, 'Main')
        ref_node = SubElement(
            augment_xml_node, 'Refs')
        entity_node = SubElement(
            augment_xml_node, 'Entitys')
        xml_content = XMLContent()
        xml_content.set_xml(augment_xml_node)
        list_of_xml.append(xml_content)
        for item in repeat_item.elements:
            item_type = str(type(item))
            if item_type == 'AugmentName':
                augment_name = item.elements[0].string.replace('"','').replace(" ",":").replace('/','_')
                logger.debug("Handling augment : " + augment_name)
                print("Handling augment : " + augment_name)
                main_node.set('target', augment_name)
                xml_content.set_filename("augment" + augment_name + '.xml')
            elif item_type == '<REPEAT>':
                repeat_items_inner = item.elements
                for repeat_item_inner in repeat_items_inner:
                    repeat_item_type_inner = str(type(repeat_item_inner))
                    if repeat_item_type_inner in ['When', 'Description']:
                        xml_node = Element('Annotation')
                        xml_node.set(
                            'Term', redfishtypes.get_descriptive_properties_mapping(repeat_item_type_inner))
                        xml_node.set('String',
                            str(repeat_item_inner.elements[1]).strip('"'))
                        xml_annotations.append(xml_node)
                    else:
                        new_list_of_xml = []
                        this_node = build_tree_repeat(repeat_item_inner, entity_node, main_node, ref_node, new_list_of_xml, logger, prefix, topleveltypes, toplevelimports)
                        for xml in new_list_of_xml:
                            xml.filename = "augment" + str(augment_name).replace('/','_') + xml.filename
                            list_of_xml.append(xml)
                        if this_node is not None:
                            xml_nodes_to_annotate.append(this_node)
        for node in xml_nodes_to_annotate:
            augment_annotation = Element('Annotation')
            augment_annotation.set(
                'Term', redfishtypes.get_descriptive_properties_mapping('augment'))
            augment_annotation.set('String', augment_name)

            for annotation in xml_annotations:
                augment_annotation.append(annotation)
            node.append(augment_annotation)
        for x in augment_xml_node:
            print(x)

    elif repeat_item_type == 'Grouping':
        handlers.handle_grouping(repeat_item, target,
                        target_parent, list_of_xml, '', logger)

    elif repeat_item_type == 'Identity':
        handlers.handle_identity(repeat_item, target)

    elif repeat_item_type == 'Presence':
        handlers.handle_presence(repeat_item, target)

    elif repeat_item_type == 'Config':
        boolean = handlers.handle_config(repeat_item, target)
        permission = xml_convenience.add_annotation(
                target, {'Term': 'OData.Permissions', 'EnumMember': 'OData.Permission/Read{}'.format('' if boolean == "true" else 'Write')})
        # use this to make permissions correct
        # pass in permissions tag??

    elif repeat_item_type == 'Default':
        handlers.handle_default(repeat_item, target)

    elif repeat_item_type == 'Units':
        handlers.handle_unit(repeat_item, target)

    elif repeat_item_type == 'Mandatory':
        handlers.handle_mandatory(repeat_item, target)

    elif repeat_item_type == 'Key':
        handlers.handle_key(repeat_item, target)

    elif repeat_item_type == 'Unique':
        handlers.handle_unique(repeat_item, target)

    elif (repeat_item_type == 'RpcGrammar'):
        logger.debug('Ignored tag: {}'.format(repeat_item_type))
        return None
        handlers.handle_rpc(repeat_item, target)

    elif repeat_item_type == 'Unmapped':
        handlers.handle_unmapped(repeat_item, target)

    elif repeat_item_type == 'OrderedBy':
        handlers.handle_orderedby(repeat_item, target)

    elif repeat_item_type == 'Must':
        handlers.handle_must(repeat_item, target)

    elif repeat_item_type == 'MaxElements':
        handlers.handle_max_elements(repeat_item, target)

    elif repeat_item_type == 'MinElements':
        handlers.handle_min_elements(repeat_item, target)

    elif repeat_item_type == 'Deviation':
        handlers.handle_deviation(repeat_item, target)

    elif repeat_item_type == 'SingleLineComment':
        logger.debug('Ignoring single line comment')

    elif repeat_item_type == 'Uses':
        handlers.handle_uses(logger)

    elif repeat_item_type == 'Notification':
        logger.debug('Ignored tag: {}'.format(repeat_item_type))
        return None
        (child_node, xml_child_node) = build_tree(
            target, target_parent, repeat_item.elements, list_of_xml, target_dir, logger)
        tree_node.add_child(child_node)

    elif repeat_item_type == 'Extension':
        handlers.handle_extension(repeat_item, target)
        
    else:
        logger.warning(
            "Unhandled Item: {0}".format(repeat_item_type))
    return None
