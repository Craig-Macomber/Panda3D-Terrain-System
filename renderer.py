from direct.showbase.ShowBase import ShowBase
import direct.directbase.DirectStart
from panda3d.core import GeoMipTerrain, NodePath, TextureStage, Vec3, PNMImage

from bakery import Tile, parseFile, loadTex
from math import ceil

useBruteForce=True

class RenderNode(NodePath):
    def __init__(self,path):
        NodePath.__init__(self,path+"_render")
        
        self.heightScale=.125
        
        d=parseFile(path+'/texList.txt')
        
        def getRenderMapType(name):
            return getattr(TextureStage,name)
        
        def getCombineMode(name):
            return getattr(TextureStage,name)
        
        self.mapTexStages={}
        self.specialMaps={}
        for m in d['Special']:
            s=m.split('\t')
            self.specialMaps[s[1]]=s[0]
        
        # terrainNode holds all the terrain tiles
        self.terrainNode=NodePath(path+"_terrainNode")
        self.terrainNode.reparentTo(self)
        #self.terrainNode.setShader(loader.loadShader(path+"/render.sha"))
        self.terrainNode.setShaderAuto()
        
        # List on non map texture stages, and their sizes
        # (TexStage,Size)
        self.texList=[]
        
        if "Tex2D" in d:
            sort=0;
            for m in d["Tex2D"]:
                sort+=1
                s=m.split()
                name=s[0]
                texStage=TextureStage(name+'stage'+str(sort))
                texStage.setSort(sort)
                source=s[1]
                
                def setTexModes(modeText):
                    combineMode=[]
                    for t in modeText:
                        if t[:1]=='M':
                            texStage.setMode(getRenderMapType(t))
                        elif t[:1]=='C':
                            combineMode.append(getCombineMode(t))
                        elif t=='Save':
                            texStage.setSavedResult(True)
                        else:
                            print "Illegal mode info for "+name
                    if len(combineMode)>0:
                        texStage.setCombineRgb(*combineMode)
                    if len(modeText)==0:
                        texStage.setMode(TextureStage.MModulate)
                
                if source=='file':
                    
                    setTexModes(s[3:])
                    
                    self.terrainNode.setTexture(texStage,loadTex(path+"/textures/"+name))
                    self.texList.append((texStage,float(s[2])))
                    
                elif source=='map':
                    setTexModes(s[2:])
                    self.mapTexStages[s[0]]=texStage

                else:
                    print 'Invalid source for '+name+' int Tex2D'

        
        # Add a task to keep updating the terrain
        taskMgr.add(self.updateTask, "update")
        
    def updateTask(self,task):
        for t in self.getTiles():
            t.terrain.update()
        return task.cont
        
    def getTiles(self):
        return [c.getPythonTag("subclass") for c in self.terrainNode.getChildren()]
    
    def addTile(self, bakedTile):
        n=RenderTile(bakedTile,self)
        n.reparentTo(self.terrainNode)
        return n
        
    def addTiles(self, bakedTiles):
        """ Expects a list of lists of tiles """
        for tlist in bakedTiles:
            for t in tlist:
                self.addTile(t)
    
    def removeTile(self, renderTile):
        renderTile.removeNode()
        
        
class RenderAutoTiler(RenderNode):
    def __init__(self,path,tileSource,tileScale,focus,addThreshold=1.0,removeThreshold=1.8,):
        RenderNode.__init__(self,path)        
        self.tileSource=tileSource
        self.tileScale=tileScale
        self.tilesMade=0
        self.addThreshold=addThreshold
        self.removeThreshold=removeThreshold
        self.focus=focus
        
        self.currentGenTile=None
        
        # Add a task to keep updating the terrain
        taskMgr.add(self.updateTiles, "updateTiles")
        
    def updateTiles(self,task):
        
        """Make any needed tiles and remove any unneeded"""
        
        # This is offset as if the tile origin was in their center!
        # Its also scaled so the current tiles are size 1
        camTilePos=(self.focus.getPos(self))/self.tileScale-Vec3(0.5, 0.5, 0.0)

        
        # Figure out which tiles are needed
        # This is done by looping by nearby tiles positions, and checking their distances
        
        # Stores (tile x index, tile y index) : distance
        needTiles={}
        
        addRange=xrange(int(-ceil(self.addThreshold)),int(ceil(self.addThreshold)))
        xOffset=int(ceil(camTilePos.getX()))
        yOffset=int(ceil(camTilePos.getY()))
        vecOffset=Vec3(xOffset,yOffset,0)
        for x in addRange:
            for y in addRange:
                vecOffset=Vec3(int(xOffset+x),int(yOffset+y),0)
                d=(camTilePos-vecOffset).length()
                if d<self.addThreshold:
                    # Add location index tuple to needTiles
                    needTiles[(xOffset+x,yOffset+y)]=d
        
        
        # Go through existing tiles
        # Remove them from needTiles as they are already generated
        # Collect any tiles too far away to keep in toRemove so they can be removed later

        tiles=self.getTiles()
        # Remove distant tiles and remove existing tiles from needTiles
        for t in tiles:
            if t.tileLoc in needTiles:
                del needTiles[t.tileLoc]
            dist=(camTilePos-(t.getPos()/self.tileScale)).length()
            if dist>self.removeThreshold:
                self.removeTile(t)
        
        # Add a tile if appropriate
        if self.currentGenTile is None:
            if len(needTiles)>0:
                minTile,minDist=needTiles.popitem()
                for k,v in needTiles.iteritems():
                    if v<minDist:
                        minTile=k
                        minDist=v
                self.currentGenTile=minTile
                x=minTile[0]*self.tileScale
                y=minTile[1]*self.tileScale
                self.tileSource.asyncGetTile(x,y,self.tileScale,self._asyncTileDone)
                
               
        return task.cont
    
    def _asyncTileDone(self,tile):
            t=self.addTile(tile)
            t.tileLoc=self.currentGenTile
            self.currentGenTile=None
            self.tilesMade+=1
            
            
    def height(self,x,y):
        # This is inefficent. Should keep a tile dictionary around for finding the right one
        # This has issues. It's inaccurate and has seam problems for some reason.
        tiles=self.getTiles()
        for t in tiles:
            xDif=x-t.getX()
            if xDif>=0 and xDif<=self.tileScale:
                yDif=y-t.getY()
                if yDif>=0 and yDif<=self.tileScale:
                    
                
                    # found correct tile
                    h=t.terrain.heightfield()
                    mapSize=h.getXSize()
                    s=(mapSize-1)/self.tileScale
                    xLoc=min(mapSize,max(0,xDif*s))
                    yLoc=min(mapSize,max(0,yDif*s))
                    
                    return t.terrain.getElevation(xLoc,yLoc)*self.heightScale
                    '''
                    
                    xLoc=min(mapSize,max(0,xDif*s))
                    yLoc=min(mapSize,max(0,mapSize-yDif*s-1))
                    px1=int(floor(xLoc))
                    py1=int(floor(yLoc))
                    px2=int(ceil(xLoc))
                    py2=int(ceil(yLoc))
                    xFade=xLoc-px1
                    yFade=yLoc-py1
                    v1=h.getRed(px2,py1)*xFade+h.getRed(px1,py1)*(1-xFade)
                    v2=h.getRed(px2,py2)*xFade+h.getRed(px1,py2)*(1-xFade)
                    v=v2*yFade+v1*(1-yFade)
                    return v*self.heightScale  
                    '''
        #print "Find height Failed"
        return 0
        
class RenderTile(NodePath):
    def __init__(self,bakedTile,node):
        self.bakedTile=bakedTile
        
        NodePath.__init__(self,"renderTile")
        NodePath.setPythonTag(self, "subclass", self)
        self.setPos(bakedTile.x,bakedTile.y,0)
        
        self.tileScale=bakedTile.scale
        
        # Save a center because some things might want to know it.
        self.center=Vec3(bakedTile.x+self.tileScale/2.0,bakedTile.y+self.tileScale/2.0,0)
        
        renderMaps=bakedTile.renderMaps
        
        for t in node.texList:
            texScale=1.0/(t[1])
            self.setTexScale(t[0],texScale*self.tileScale)
            self.setTexOffset(t[0],(self.getX() % t[1])*texScale,(self.getY() % t[1])*texScale)
        
        for t in node.mapTexStages:
            tex=bakedTile.renderMaps[t].tex
            size=tex.getXSize()
            
            self.setTexture(node.mapTexStages[t],tex)
            
            # Here we apply a transform to the textures so centers of the edge pixels fall on the edges of the tile
            # Normally the edges of the edge pixels would fall on the edges of the tiles.
            # The benifits of this should be visible, though they have not been varified sucessfully yet.
            # In fact, these transforms appear to not do anything.
            # This is troubling, but the problem they are supposed to fix is currently invisible as well.
            #margin=bakery.texMargin(size)
            #self.setTexOffset(t,-margin,-margin)
            #self.setTexScale(t,float(size+margin*2)/size)
            
        self.setShaderInput("offset",bakedTile.x,bakedTile.y,0.0,0.0)
        self.setShaderInput("scale",bakedTile.scale)
              
        # Set up the GeoMipTerrain
        self.terrain = GeoMipTerrain("TerrainTile")
        heightTex=bakedTile.renderMaps[node.specialMaps["height"]].tex
        heightTexSize=heightTex.getXSize()
        pnmImage=PNMImage()
        heightTex.store(pnmImage)
        self.terrain.setHeightfield(pnmImage)
        
        
        # Set terrain properties
        self.terrain.setBlockSize(min(32,(heightTexSize-1)))
        self.terrain.setNear(heightTexSize)
        self.terrain.setFar(heightTexSize*4)
        self.terrain.setFocalPoint(base.camera)
        #self.terrain.setBorderStitching(True)
        #self.terrain.setAutoFlatten(GeoMipTerrain.AFMStrong)
        self.terrain.setBruteforce(useBruteForce)
        # Store the root NodePath for convenience
        root = self.terrain.getRoot()
        root.reparentTo(self)
        
        xyScale=float(self.tileScale)/(heightTexSize-1)
        root.setScale(xyScale,xyScale,node.heightScale)
        
        # Generate it.
        self.terrain.generate()
        
        
