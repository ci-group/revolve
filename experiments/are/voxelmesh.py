from polyvox import PolyVoxCore
import collada
import numpy


def create_sphere_in_volume(volumeData: PolyVoxCore.RawVolumeuint8, radius: float, smooth=False):
    boundaries = volumeData.getEnclosingRegion()

    #This vector hold the position of the center of the volume
    v3dVolCenter_i32 = boundaries.getCentre()
    v3dVolCenter = PolyVoxCore.Vector3Dfloat(v3dVolCenter_i32.x, v3dVolCenter_i32.y, v3dVolCenter_i32.z)

    for z in range(boundaries.getLowerZ(), boundaries.getUpperZ()):
        for y in range(boundaries.getLowerY(), boundaries.getUpperY()):
            for x in range(boundaries.getLowerX(), boundaries.getUpperX()):
				#Store our current position as a vector...
                v3dCurrentPos = PolyVoxCore.Vector3Dfloat(x,y,z)	
                #And compute how far the current position is from the center of the volume
                fDistToCenter = max(0.001, (v3dCurrentPos - v3dVolCenter).length())

                if smooth:
                    value = int((radius/fDistToCenter)*(255/2))
                    uVoxelValue = max(0, min(255, value))
                else:
                    #If the current voxel is less than 'radius' units from the center then we make it solid.
                    uVoxelValue = 255 if fDistToCenter <= radius else 0

                #Wrte the voxel value into the volume	
                volumeData.setVoxel(PolyVoxCore.Vector3Dint32_t(x,y,z), uVoxelValue)    

class VoxelMesh:
    def __init__(self, resolution: int):
        self.volumeData = PolyVoxCore.RawVolumeuint8(
            PolyVoxCore.Region(PolyVoxCore.Vector3Dint32_t(0,0,0),
                            PolyVoxCore.Vector3Dint32_t(resolution,resolution,resolution)
            )
        )
    
    def create_sphere_in_volume(self, radius, smooth):
        create_sphere_in_volume(self.volumeData, radius, smooth)

    def get_cubit_mesh(self):
        mesh = PolyVoxCore.extractCubicMesh_RawVolume_u8(self.volumeData, self.volumeData.getEnclosingRegion())
        mesh = PolyVoxCore.decodeMeshCubic_u8_u32(mesh)
        return mesh

    def get_marching_cubes_mesh(self):
        mesh = PolyVoxCore.extractMarchingCubesMesh_RawVolume_u8(self.volumeData, self.volumeData.getEnclosingRegion())
        mesh = PolyVoxCore.decodeMeshMarchingCubes_u8_u32(mesh)
        return mesh

    def collada(self, marching_cubes=True, generate_normals=False):
        collada_mesh = collada.Collada()
        # Note that the second argument to Effect is for parameters. These are used for textures. We omit textures for simplicity here.
        effect = collada.material.Effect("effect0", [], "phong", diffuse=(1,0,0), specular=(0,1,0))
        collada_material = collada.material.Material("material0", "mymaterial", effect)
        collada_mesh.effects.append(effect)
        collada_mesh.materials.append(collada_material)

        if not marching_cubes:
            polyvox_mesh = self.get_cubit_mesh()
            # only marching cubes supports generated normals
            generate_normals = False
        else:
            polyvox_mesh = self.get_marching_cubes_mesh()

        voxel_object_centre = self.volumeData.getEnclosingRegion().getCentre()

        n_vertices = polyvox_mesh.getNoOfVertices()
        n_indices = polyvox_mesh.getNoOfIndices()
        
        vertices = numpy.zeros(n_vertices*3, dtype=numpy.float)
        if generate_normals:
            normals  = numpy.zeros(n_vertices*3, dtype=numpy.float)
        # materials= numpy.zeros(n_vertices, dtype=numpy.float)
        indices  = numpy.zeros(n_indices, dtype=numpy.int32)

        for i in range(0,n_vertices):
            vertex = polyvox_mesh.getVertex(i)
            position = vertex.position
            # material = vertex.data
            if generate_normals:
                normal = vertex.normal

            j = i*3

            vertices[j+0] = position.getX()
            vertices[j+1] = position.getY()
            vertices[j+2] = position.getZ()
            # materials[i] = material #TODO
            if generate_normals:
                normals[j+0] = normal.getX()
                normals[j+1] = normal.getY()
                normals[j+2] = normal.getZ()

        for i in range(0,n_indices):
            indices[i] = polyvox_mesh.getIndex(i)

        print("n_vertices: {}".format(n_vertices))
        print("vertices vec: {}".format(len(vertices)))
        if generate_normals:
            print("normals vec: {}".format(len(normals)))

        print("n_indices: {}".format(n_indices))
        print("indices vec: {}".format(len(indices)))

        vert_src   = collada.source.FloatSource("verts-array", vertices, ('X', 'Y', 'Z'))
        if generate_normals:
            normal_src = collada.source.FloatSource("normals-array", normals, ('X', 'Y', 'Z'))
        # material_src = collada.source.FloatSource("uv-array", numpy.array(material), ('X'))

        sourcebyid = [vert_src]
        if generate_normals:
            sourcebyid.append(normal_src)
        geometry = collada.geometry.Geometry(collada_mesh, "geometry0", "myshape", sourcebyid)

        input_list = collada.source.InputList()
        input_list.addInput(0, 'VERTEX', "#verts-array")
        if generate_normals:
            input_list.addInput(0, 'NORMAL', "#normals-array")
        # input_list.addInput(2, 'MATERIAL', "#material-array")

        triset  = geometry.createTriangleSet(indices, input_list, "materialref")
        geometry.primitives.append(triset)
        collada_mesh.geometries.append(geometry)

        matnode  = collada.scene.MaterialNode("materialref", collada_material, inputs=[])
        geomnode = collada.scene.GeometryNode(geometry, [matnode])
        node     = collada.scene.Node("node0", children=[geomnode])
        
        # recenter
        recenter_transform = collada.scene.TranslateTransform(
            -voxel_object_centre.x,
            -voxel_object_centre.y,
            -voxel_object_centre.z,
        )
        node.transforms.append(recenter_transform)

        # # scale voxel units from `m` to `cm`
        # scale_transform = collada.scene.ScaleTransform(
        #     0.1,
        #     0.1,
        #     0.1,
        # )
        # node.transforms.append(scale_transform)

        myscene = collada.scene.Scene("myscene", [node])
        collada_mesh.scenes.append(myscene)
        collada_mesh.scene = myscene

        return collada_mesh


if __name__ == "__main__":
    voxel_mesh = VoxelMesh(resolution=20)
    voxel_mesh.create_sphere_in_volume(radius=10.0, smooth=True)
    collada_mesh = voxel_mesh.collada(marching_cubes=True, generate_normals=True)
    collada_mesh.write('/tmp/test.dae')
