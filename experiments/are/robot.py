import os
import sys
import voxelmesh

current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
sys.path.append(newpath)

from pyrevolve import sdfbuilder

class ARERobot:
    def __init__(self, name):
        self.name = name
        self.position = sdfbuilder.math.Vector3(0,0,2)
        self.rotation = sdfbuilder.math.Quaternion(1,0,0,0)
        self.scale    = sdfbuilder.math.Vector3(0.1, 0.1, 0.1)
        self.controller_plugin = "libRobotControlPlugin.so"
        self.smooth=False

        self.voxel_mesh = voxelmesh.VoxelMesh(resolution=20)
        self.voxel_mesh.create_sphere_in_volume(radius=10.0, smooth=self.smooth)
    
    def sdf(self):
        model = self._build_model_node()
        sdf = sdfbuilder.SDF(version="1.6")
        sdf.add_element(model)
        return sdf

    def _build_model_node(self):
        model = sdfbuilder.Model(self.name, static=False)
        # C++ plugin node
        # model.add_element(self._build_plugin_node())

        # Add Body
        model.add_elements(self._build_body_node())

        # Set robot position
        model.set_position(self.position)
        model.set_rotation(self.rotation)

        return model

    def _build_plugin_node(self):
        # C++ plugin element
        plugin = sdfbuilder.Element(
            tag_name='plugin',
            attributes={
                'name': 'robot_controller',
                'filename': self.controller_plugin
            })

        # Add C++ plugin config
        plugin_config = sdfbuilder.Element(
            tag_name='rv:robot_config',
            attributes={
                'xmlns:rv': 'https://github.com/ci-group/revolve'
            }
        )
        plugin_config.add_element(sdfbuilder.Element(
            tag_name='rv:test',
            body="this is a test"
        ))

        plugin.add_element(plugin_config)

        return plugin

    def _build_body_node(self):
        collada_uri = '/tmp/test.dae'
        collada_mesh = self.voxel_mesh.collada(marching_cubes=self.smooth, generate_normals=False)
        collada_mesh.write(collada_uri)
        sphere = sdfbuilder.Geometry()
        # sphere.add_element(sdfbuilder.geometry.Sphere(radius=.5))
        sphere.add_element(sdfbuilder.geometry.Mesh(uri=collada_uri, scale=self.scale))
        
        sphere_link = sdfbuilder.Link("sphere_link")
        sphere_collision = sdfbuilder.Collision(
            name="sphere_collision",
            elements=[sphere])
        sphere_visual = sdfbuilder.Visual(
            name="sphere_visual",
            elements=[sphere])
        sphere_inertia = sdfbuilder.Inertial(
            name="sphere_inertia",
            elements=[sdfbuilder.inertial.Mass(value=1.0)]
        )
        sphere_link.add_elements([sphere_collision, sphere_visual, sphere_inertia])

        sphere_link.set_position(sdfbuilder.math.Vector3(0,0,0))
        sphere_link.set_rotation(sdfbuilder.math.Quaternion(1,0,0,0))
        return [sphere_link]
        

    