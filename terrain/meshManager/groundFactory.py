import math, random

from panda3d.core import Vec3, Quat, GeomVertexFormat

from panda3d.core import *

import meshManager


class GroundFactory(meshManager.MeshFactory):
    
    def __init__(self,shader=None):
        self.shader=shader
        meshManager.MeshFactory.__init__(self)
    
    def regesterGeomRequirements(self,LOD,collection):
        # for now, going to use our own node, so we don't have any special requirements
        self.dataIndex=collection.add(meshManager.GeomRequirements(geomVertexFormat=None))

    def draw(self,LOD,x0,y0,x1,y1,drawResourcesFactory):
        tile=drawResourcesFactory.getTile()
        resources=drawResourcesFactory.getDrawResources(self.dataIndex)
        
        # Set up the GeoMipTerrain
        terrain = GeoMipTerrain("TerrainTile")
        heightTex=tile.bakedTile.renderMaps[tile.renderNode.specialMaps["height"]].tex
        heightTexSize=heightTex.getXSize()
        pnmImage=PNMImage()
        # heightTex.makeRamImage () # Makes it run without having ran image in advance, but it all ends up flat.
        heightTex.store(pnmImage)
        terrain.setHeightfield(pnmImage)
        
        
        # Set terrain properties
        terrain.setBruteforce(True)
        # Store the root NodePath for convenience
        root = terrain.getRoot()
        root.setPos(tile.bakedTile.x,tile.bakedTile.y,0)
        
        for t in tile.renderNode.texList:
            texScale=1.0/(t[1])
            root.setTexScale(t[0],texScale*tile.tileScale)
            root.setTexOffset(t[0],(tile.getX() % t[1])*texScale,(tile.getY() % t[1])*texScale)
        
        for t in tile.renderNode.mapTexStages:
            tex=tile.bakedTile.renderMaps[t].tex
            
            
            root.setTexture(tile.renderNode.mapTexStages[t],tex)
            
            # Here we apply a transform to the textures so centers of the edge pixels fall on the edges of the tile
            # Normally the edges of the edge pixels would fall on the edges of the tiles.
            # The benifits of this should be visible, though they have not been varified sucessfully yet.
            # In fact, these transforms appear to not do anything.
            # This is troubling, but the problem they are supposed to fix is currently invisible as well.
            #size=tex.getXSize()
            #margin=bakery.texMargin(size)
            #tile.setTexOffset(t,-margin,-margin)
            #tile.setTexScale(t,float(size+margin*2)/size)
            
        root.setShaderInput("offset",tile.bakedTile.x,tile.bakedTile.y,0.0,0.0)
        root.setShaderInput("scale",tile.bakedTile.scale)
        
        xyScale=float(tile.tileScale)/(heightTexSize-1)
        root.setScale(xyScale,xyScale,tile.renderNode.heightScale)
        if self.shader: root.setShader(self.shader)
        # Generate it.
        terrain.generate()
        
        resources.arrachNode(root)
        
        tile.terrain=terrain