from polyvox import PolyVoxCore
import collada
import numpy


def create_sphere_in_volume(volumeData: PolyVoxCore.RawVolumeint32, radius: float):
    #This vector hold the position of the center of the volume
    v3dVolCenter = PolyVoxCore.Vector3Dfloat(volumeData.getWidth() / 2, 
                                    volumeData.getHeight() / 2,
                                    volumeData.getDepth() / 2)

    #This three-level for loop iterates over every voxel in the volume
    for z in range(0, volumeData.getDepth()):
        for y in range(0, volumeData.getHeight()):
            for x in range(0, volumeData.getWidth()):
				#Store our current position as a vector...
                v3dCurrentPos = PolyVoxCore.Vector3Dfloat(x,y,z)	
                #And compute how far the current position is from the center of the volume
                fDistToCenter = (v3dCurrentPos - v3dVolCenter).length()

                uVoxelValue = 0

                #If the current voxel is less than 'radius' units from the center then we make it solid.
                if fDistToCenter <= radius:
                    #Our new voxel value
                    uVoxelValue = 1

                #Wrte the voxel value into the volume	
                volumeData.setVoxel(PolyVoxCore.Vector3Dint32_t(x,y,z), uVoxelValue)    

class VoxelMesh:
    def __init__(self):
        self.volumeData = PolyVoxCore.RawVolumeint32(
            PolyVoxCore.Region(PolyVoxCore.Vector3Dint32_t(0,0,0),
                            PolyVoxCore.Vector3Dint32_t(32,32,32)
            )
        )
        create_sphere_in_volume(self.volumeData, 3.0)

        # self.mesh = PolyVoxCore.SurfaceMeshPositionMaterialNormal()
        # self.surface_extractor = PolyVoxCore.SurfaceExtractorSimpleVolumeDensity8(
        #     self.volumeData,
        #     self.volumeData.getEnclosingRegion(),
        #     self.mesh
        # )

    def get_mesh(self):
        mesh = PolyVoxCore.extractCubicMesh_RawVolume_i32(self.volumeData, self.volumeData.getEnclosingRegion())
        mesh = PolyVoxCore.decodeMeshCubic_typei32_indexu32(mesh)
        return mesh

    def collada(self):
        collada_mesh = collada.Collada()
        # Note that the second argument to Effect is for parameters. These are used for textures. We omit textures for simplicity here.
        effect = collada.material.Effect("effect0", [], "phong", diffuse=(1,0,0), specular=(0,1,0))
        collada_material = collada.material.Material("material0", "mymaterial", effect)
        collada_mesh.effects.append(effect)
        collada_mesh.materials.append(collada_material)

        polyvox_mesh = self.get_mesh()
        n_vertices = polyvox_mesh.getNoOfVertices()
        n_indices = polyvox_mesh.getNoOfIndices()
        # polyvox_indices = polyvox_mesh.getIndices()
        # vert_mat_norm = polyvox_mesh.getVertices()
        
        vertices = numpy.zeros(n_vertices*3, dtype=numpy.float)
        normals  = numpy.zeros(n_vertices*3, dtype=numpy.float)
        materials= numpy.zeros(n_vertices, dtype=numpy.float)
        indices  = numpy.zeros(n_indices, dtype=numpy.int32)

        for i in range(0,n_vertices):
            # v_m_n is 
            # python: PolyVoxCore.PositionMaterialNormal
            # C++:    PolyVox::PositionMaterialNormal
            position = polyvox_mesh.getVertex(i).position
            material = polyvox_mesh.getVertex(i).data
            normal   = polyvox_mesh.getVertex(i).normal

            j = i*3

            vertices[j+0] = position.getX()
            vertices[j+1] = position.getY()
            vertices[j+2] = position.getZ()
            # materials[i] = material #TODO
            normals[j+0] = normal.getX()
            normals[j+1] = normal.getY()
            normals[j+2] = normal.getZ()

        for i in range(0,n_indices):
            indices[i] = polyvox_mesh.getIndex(i)

        # print("vert_mat_norm: {}".format(len(vert_mat_norm)))
        print("n_vertices: {}".format(n_vertices))
        print("vertices: {}".format(len(vertices)))
        print("normals: {}".format(len(normals)))

        # print("polyvox_indices: {}".format(len(polyvox_indices)))
        print("n_indices: {}".format(n_indices))
        print("indices: {}".format(len(indices)))

        vert_src   = collada.source.FloatSource("verts-array", numpy.array(vertices), ('X', 'Y', 'Z'))
        # normal_src = collada.source.FloatSource("normals-array", numpy.array(normals), ('X', 'Y', 'Z'))
        # material_src = collada.source.FloatSource("uv-array", numpy.array(uvs), ('X', 'Y'))

        geometry = collada.geometry.Geometry(collada_mesh, "geometry0", "myshape", [vert_src])

        input_list = collada.source.InputList()
        input_list.addInput(0, 'VERTEX', "#verts-array")
        # input_list.addInput(1, 'NORMAL', "#normals-array")

        triset  = geometry.createTriangleSet(indices, input_list, "materialref")
        geometry.primitives.append(triset)
        collada_mesh.geometries.append(geometry)

        matnode  = collada.scene.MaterialNode("materialref", collada_material, inputs=[])
        geomnode = collada.scene.GeometryNode(geometry, [matnode])
        node     = collada.scene.Node("node0", children=[geomnode])

        myscene = collada.scene.Scene("myscene", [node])
        collada_mesh.scenes.append(myscene)
        collada_mesh.scene = myscene
        collada_mesh.write('/tmp/test.dae')

        return collada_mesh


if __name__ == "__main__":
    voxel_mesh = VoxelMesh()
    collada_mesh = voxel_mesh.collada()