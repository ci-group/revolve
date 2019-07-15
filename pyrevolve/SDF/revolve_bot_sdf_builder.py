import math
import xml.etree.ElementTree

from pyrevolve import SDF
from pyrevolve.revolve_bot.revolve_module import ActiveHingeModule, Orientation, BoxSlot


def revolve_bot_to_sdf(robot, robot_pose, nice_format):
    from xml.etree import ElementTree
    from pyrevolve import SDF

    sdf_root = ElementTree.Element('sdf', {'version': '1.6'})

    assert (robot.id is not None)
    model = ElementTree.SubElement(sdf_root, 'model', {
        'name': str(robot.id)
    })

    pose_elem = SDF.Pose(robot_pose)
    model.append(pose_elem)

    core_link = SDF.Link('Core')
    core_visual, core_collision, imu_core_sensor = robot._body.to_sdf('', core_link)

    links = [core_link]
    joints = []
    actuators = []
    sensors = [imu_core_sensor]

    core_link.append(core_visual)
    core_link.append(core_collision)

    for core_slot, child_module in robot._body.iter_children():
        if child_module is None:
            continue
        core_slot = robot._body.boxslot(Orientation(core_slot))
        slot_chain = core_slot.orientation.short_repr()

        children_links, \
        children_joints, \
        children_sensors = _module_to_sdf(child_module,
                                          core_link,
                                          core_slot,
                                          core_collision,
                                          slot_chain)

        links.extend(children_links)
        joints.extend(children_joints)
        sensors.extend(children_sensors)

    for joint in joints:
        model.append(joint)
        if joint.is_motorized():
            actuators.append(joint)

    for link in links:
        link.align_center_of_mass()
        link.calculate_inertial()
        model.append(link)

    # ADD BRAIN
    plugin_elem = _sdf_brain_plugin_conf(robot._brain, sensors, actuators, robot_genome=None)
    model.append(plugin_elem)

    # XML RENDER PHASE #
    def prettify(rough_string, indent='\t'):
        """Return a pretty-printed XML string for the Element.
        """
        import xml.dom.minidom
        reparsed = xml.dom.minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent=indent)

    res = xml.etree.ElementTree.tostring(sdf_root, encoding='utf8', method='xml')

    if nice_format is not None:
        res = prettify(res, nice_format)
    else:
        res = res.decode()

    return res


def _sdf_attach_module(module_slot, module_orientation: float,
                       visual, collision,
                       parent_slot, parent_collision):
    """
    Attaches `module` to `parent` using `parent_slot`.
    It modifies the pose of `visual` and `collision` to move them attached to the
    `parent_collision`
    :param module_slot:
    :param module_orientation: degrees of rotation of the component
    :param visual:
    :param collision:
    :param parent_slot:
    :param parent_collision:
    :return:
    """

    if module_orientation is not None:
        # Rotate the module_slot.tangent vector over the normal
        # with the given number of radians to apply
        # the rotation. Rotating this vector around
        # the normal should not break their orthogonality.
        orientation = module_orientation / 180.0 * math.pi
        rot = SDF.math.Quaternion.from_angle_axis(orientation, module_slot.normal)
        module_slot.tangent = rot * module_slot.tangent

    visual.align(
        module_slot,
        parent_slot,
        parent_collision,
        relative_to_child=True
    )
    collision.set_rotation(visual.get_rotation())
    old_translation = collision.get_position()
    collision.set_position(visual.get_position())
    collision.translate(collision.to_parent_direction(old_translation))


def _module_to_sdf(module, parent_link, parent_slot: BoxSlot, parent_collision, slot_chain):
    """
    Recursive function that takes a module and returns a list of SDF links and joints that
    that module and his children have generated.
    :param module: Module to parse
    :type module: RevolveModule
    :param parent_link: SDF `Link` of the parent
    :param parent_slot: Slot of the parent which this module should attach to
    :param parent_collision: Parent collision box, needed for the alignment.
    :param slot_chain: Text that names the joints, it encodes the path that was made to arrive to that element.
    :return:
    """
    links = []
    joints = []
    sensors = []

    my_link = parent_link
    my_collision = None

    # ACTIVE HINGE
    if type(module) is ActiveHingeModule:
        child_link = SDF.Link('{}_Leg'.format(slot_chain))

        visual_frame, collisions_frame, \
        visual_servo, collisions_servo, \
        joint = module.to_sdf('{}'.format(slot_chain), parent_link, child_link)

        # parent_slot = parent_module.boxslot(parent_slot)
        module_slot = module.boxslot_frame(Orientation.SOUTH)
        _sdf_attach_module(module_slot, module.orientation,
                           visual_frame, collisions_frame[0],
                           parent_slot, parent_collision)

        parent_slot = module.boxslot_frame(Orientation.NORTH)
        module_slot = module.boxslot_servo(Orientation.SOUTH)
        _sdf_attach_module(module_slot, None,
                           visual_servo, collisions_servo[0],
                           parent_slot, collisions_frame[0])

        joint.set_rotation(visual_servo.get_rotation())
        old_position = joint.get_position()
        joint.set_position(visual_servo.get_position())
        joint.translate(joint.to_parent_direction(old_position))

        # Add visuals and collisions for Servo Frame block
        parent_link.append(visual_frame)
        for i, collision_frame in enumerate(collisions_frame):
            parent_link.append(collision_frame)
            if i != 0:
                old_pos = collision_frame.get_position()
                collision_frame.set_rotation(visual_frame.get_rotation())
                collision_frame.set_position(visual_frame.get_position())
                collision_frame.translate(collision_frame.to_parent_direction(old_pos))

        # Add visuals and collisions for Servo block
        child_link.append(visual_servo)
        for i, collision_servo in enumerate(collisions_servo):
            child_link.append(collision_servo)
            if i != 0:
                old_pos = collision_servo.get_position()
                collision_servo.set_position(collisions_servo[0].get_position())
                collision_servo.set_rotation(collisions_servo[0].get_rotation())
                collision_servo.translate(collision_servo.to_parent_direction(old_pos))

        # Add joint
        child_link.add_joint(joint)
        links.append(child_link)
        joints.append(joint)

        # update my_link and my_collision
        my_link = child_link
        my_collision = collisions_servo[0]

    # OTHERS
    else:
        visual, collision, sensor = module.to_sdf(slot_chain, my_link)

        module_slot = module.boxslot(Orientation.SOUTH)
        _sdf_attach_module(module_slot, module.orientation,
                           visual, collision,
                           parent_slot, parent_collision)

        parent_link.append(visual)
        parent_link.append(collision)

        my_collision = collision

        if sensor is not None:
            sensors.append(sensor)

    # RECURSION ON CHILDREN
    for my_slot, child_module in module.iter_children():
        if child_module is None:
            continue

        my_slot = module.boxslot(Orientation(my_slot))
        child_slot_chain = '{}{}'.format(slot_chain, my_slot.orientation.short_repr())

        children_links, \
        children_joints, \
        children_sensors = _module_to_sdf(child_module,
                                          my_link,
                                          my_slot,
                                          my_collision,
                                          child_slot_chain)
        links.extend(children_links)
        joints.extend(children_joints)
        sensors.extend(children_sensors)

    return links, joints, sensors


def _sdf_brain_plugin_conf(
        robot_brain,
        sensors,
        actuators,
        robot_genome=None,
        update_rate: float = 8.0,
        controller_plugin: str = 'libRobotControlPlugin.so',
):
    """
    Creates the plugin node with the brain configuration inside

    :param robot_brain: Brain of the robot to send to the simulator
    :param battery_level:
    :param update_rate: Update rate as used by the default controller
    :param controller_plugin: Name of the shared library of the model plugin
    :return: The sdf plugin element
    :rtype: xml.etree.ElementTree.Element
    """
    plugin = xml.etree.ElementTree.Element(
        'plugin',
        attrib={
            'name': 'robot_controller',
            'filename': controller_plugin,
            'xmlns:rv': 'https://github.com/ci-group/revolve',
        })

    config = xml.etree.ElementTree.SubElement(plugin, 'rv:robot_config')

    # update rate
    SDF.sub_element_text(config, 'rv:update_rate', update_rate)

    # battery
    # if battery_level is not None:
    #     battery = xml.etree.ElementTree.SubElement(config, 'rv:battery')
    #     SDF.sub_element_text(battery, 'rv:level', battery_level)

    # brain
    robot_brain_sdf = xml.etree.ElementTree.SubElement(config, 'rv:brain')

    robot_learner = robot_brain.learner_sdf()
    if robot_learner is None:
        xml.etree.ElementTree.SubElement(robot_brain_sdf, 'rv:learner', {'type': 'None'})
    else:
        robot_brain_sdf.append(robot_learner)

    robot_controller = robot_brain.controller_sdf()
    if robot_controller is None:
        xml.etree.ElementTree.SubElement(robot_brain_sdf, 'rv:controller', {'type': 'None'})
    else:
        robot_brain_sdf.append(robot_controller)

    # sensors
    sensors_elem = xml.etree.ElementTree.SubElement(robot_brain_sdf, 'rv:sensors')
    for sensor in sensors:
        sensors_elem.append(sensor.to_robot_config_sdf())

    # actuators
    actuators_elem = xml.etree.ElementTree.SubElement(robot_brain_sdf, 'rv:actuators')
    for actuator in actuators:
        actuators_elem.append(actuator.to_robot_config_sdf())

    # robot genome
    if robot_genome is not None:
        SDF.sub_element_text(config, 'rv:genome', str(robot_genome))

    #TODO get initial charge from revolve_bot
    initial_charge = 0
    battery = xml.etree.ElementTree.SubElement(config, 'rv:battery', {
        'initial_charge': str(initial_charge),
    })
    SDF.sub_element_text(battery, 'voltage', 0.0)

    return plugin
