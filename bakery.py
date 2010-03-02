from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
import direct.directbase.DirectStart

from direct.task import Task

from direct.stdpy.threading import Condition



from textureRenderer import *



qq=Queue()


# Size Map textures are rendered
tileMapSize=256

# Makes debugging shaders easier
useShaderFiles=False

def pathPrefix():
    if base.appRunner!=None:
        return base.appRunner.multifileRoot+'/'
        
    else:
        return ''


def parseFile(path):
    """
    
    Read sections headed by :SectionName into lists by section name in a dictionary
    blank lines, line preceeding and ending whitespace and #Comments are stripped
    
    
    """
    
    d={}
    currentList=None
    
    f = open(pathPrefix()+path, 'r')
    for t in f.readlines(): 
        # Remove comments
        i=t.find('#')
        if i!=-1:
            t=t[:i]
        
        # Strip excess whitespace
        t=t.strip()
        
        if len(t)>0:
            if t[0]==':':
                currentList=[]
                d[t[1:]]=currentList
            else:
                if currentList!=None:
                    currentList.append(t)
    return d




mapMakerShaderSource=open(pathPrefix()+'mapMaker.cg', 'r').read()

def texMargin(size):
    return (1.0/(size-1))/2.0

class Bakery:
    
    """
    
    This will manage the baking from start to finish.
    It bakes tiles. For a batch, the process is as follows:
    Load
        Determin what maps are needed for rendering and object placement (Output maps)
        Recursivly determine all maps that are needed to make output maps, including output maps (Used maps)
            Also, build and load all the shaders than that make these maps, and record their input maps.
        Originze shaders into a usable order (so all input maps will exist when a given shader is run)
        Setup texture rendering system
            Make buffer (a size needs to be specified, prabably starndard for all tiles, but could be map dependant)
            Setup Camera
            Setup Mesh
            Load specified map drawing shader (draws specified maps from editor over generated texture)
        Read in editor file
        Locate all used maps in editor file (used specified maps)
    Bake Tiles
        Allocate tile array
        Add all used specified maps that overlap a given tile to its map list
    
    For a given tile the process is as follows:
    Run all shaders in shader list in order
        Provide all input textures
        Apply shader to texture rendering system's mesh
        Render texture
        Soft specified maps (they should have an order) (This could be done per tile, or before adding the maps to tiles)
        Apply all specified maps (If any)
            Apply specified map drawing shader to texture rendering system's mesh
            Render texture
    Generate mesh placements (Trees and such)
        Editor specified placement
        Procedural placement
    
    """

    def __init__(self, editorFile, bakeryFolder):
        """
        
        editorFile is path to file saved by the editor that should contain any specified maps
        bakeryFolder is path to all project baking resources
        this should contain all the shaders, and a few other things (This text should get updated as requirements are added)
        
        
        """
        
        # Start a list of output maps
        # Thses are maps that are needed for mesh placement and rendering
        d=parseFile(bakeryFolder+'/outputMaps.txt')
        
        if "Render" in d:
            self.renderMapNames=d["Render"]
        else:
            self.renderMapNames=[]
            
            
        if "MeshPlacement" in d:
            self.meshPlacementMapNames=d["MeshPlacement"]
        else:
            self.meshPlacementMapNames=[]
          
        outputMapNames=self.renderMapNames+self.meshPlacementMapNames
        
        
        # Make an carfully orderd list of MapShaders that will generate all output maps
        self.shaders=[]
        sDict={}
        
        def addShaders(shaderNames):
            for shaderName in shaderNames:
                if shaderName in sDict:
                    s=sDict[shaderName]
                    self.shaders.remove(s)
                    self.shaders.insert(0,s)
                    addShaders(s.inputMapNames)
                else:
                    s=MapShader(shaderName,bakeryFolder+'/')
                    self.shaders.insert(0,s)
                    sDict[shaderName]=self.shaders[0]
                    addShaders(s.inputMapNames)
                #print [s.name for s in self.shaders]
        

        addShaders(outputMapNames)

        
        # Load Editor File
        self.usedSpecifiedMaps=[]
        if editorFile!=None:
            pass
           
    def bake(self, xStart, yStart, tileSize, tileCountX, tileCountY):
        """
        
        Batch tile bake
        Returns a list of lists. Use [x][y] to extract tiles.
        
        """
        
        return [[self.bakeTile(xStart+x*tileSize,yStart+y*tileSize, tileSize) for y in xrange(tileCountY)] for x in xrange(tileCountX)]

        
    def bakeTile(self, xStart, yStart, tileSize):
        """bake a single tile"""
        return _RawTile(xStart,yStart, tileSize).bake(self)
    
    def asyncBakeTile(self, xStart, yStart, tileSize, callback, callbackParams=[]):
        _RawTile(xStart,yStart, tileSize).asyncBake(self,callback,callbackParams)
    
    def getRenderMapCam(self, rawTile, inputMaps, shader, size):
        """
        Sets up scene and cam for rendering the map
        Returns the cam
        """
        margin=texMargin(size)
        
        altRender=NodePath("newRender")

        # setup square orthographic cam
        altCam=NodePath(Camera("renderMapCam"))
        altCam.reparentTo(altRender)   
        altCam.setPos(.5,-1,.5) 

        oLens = OrthographicLens()
        oLens.setFilmSize(1+margin*2, 1+margin*2)
        altCam.node().setLens(oLens)
        
         # Make a card on which the shader will render the map
        c=CardMaker("MapCardMaker")
        c.setUvRange(0-margin,1+margin,0-margin,1+margin)
        c.setFrame(0-margin,1+margin,0-margin,1+margin)
        mapCard=NodePath(c.generate())
        
        mapCard.setPos(0,0,0)   
        mapCard.setShader(shader.shader)
        mapCard.setShaderInput("offset",rawTile.x,rawTile.y,0,0)
        mapCard.setShaderInput("scale",rawTile.scale,0,0,0)

        for m in inputMaps:
            texStage=TextureStage(m.name+"stage")
            mapCard.setTexture(texStage,m.tex)
        
        for p in shader.shaderTex:
            mapCard.setTexture(*p)
        
        mapCard.reparentTo(altRender)
        
        # Comment out this line to cause the bug with multiple textures requireing an extra frame to work properly
        altRender.prepareScene(base.win.getGsg())
        
        return altCam
        
    def asyncRenderMap(self, rawTile, inputMaps, shader, callback, callbackParams=()):
        size=int(round(tileMapSize*shader.resolutionScale+shader.addPixels))
        
        q=QueueItem(size,size,self._asyncRenderMapDone,self.getRenderMapCam, (callback,shader.name,callbackParams), (rawTile, inputMaps, shader, size),toRam=False)
        qq.queue.append(q)
    
    def _asyncRenderMapDone(self,tex,callback,name,callbackParams):
        tex.setWrapU(Texture.WMClamp)
        tex.setWrapV(Texture.WMClamp)
        callback(Map(name,tex),*callbackParams)
    
    def renderMap(self, rawTile, inputMaps, shader):
        """
        
        This is where the map images are genrated.
        A render to texture process is used.
        
        
        """
        
        # Resolution of texture/buffer to be rendered
        size=int(round(tileMapSize*shader.resolutionScale+shader.addPixels))
        
        
        altCam=self.getRenderMapCam(rawTile, inputMaps, shader, size)
        
        q=SimpleQueueItem(size,size,None,altCam,toRam=True)
        
        tex= qq.renderTex(q)
        self.mapCard.remove()
        
        tex.setWrapU(Texture.WMClamp)
        tex.setWrapV(Texture.WMClamp)
        
        return Map(shader.name,tex)
        
        
class LiveBakery(Bakery):

    """
    
    A little, prabably unnessary class used to make the interface
    used for supplying tiles to the tiles to RenderAutoTiler a bit clearer.
    
    
    """        
    def hasTile(self, xStart, yStart, tileSize):
        """If one is using a cashed tile source instead of a live bakery, this would be sometimes be false"""
        return True
        
    def getTile(self, xStart, yStart, tileSize):
        return self.bakeTile(xStart, yStart, tileSize)
    
    def asyncGetTile(self, xStart, yStart, tileSize, callback, callbackParams=[]):
        self.asyncBakeTile(xStart, yStart, tileSize, callback, callbackParams)
    

class _AsyncMapRenderer:
    """ For use within _RawTile.asyncBake """
    def __init__(self, bakery, rawTile, callbackData):
        self.bakery=bakery
        self.rawTile=rawTile
        self.callbackData=callbackData
        self.maps={}
        self.shadersToDo=list(bakery.shaders)
        self.doNext()
        
    def doNext(self):
        if len(self.shadersToDo)==0:
            self.rawTile._asyncBakeMapsDone(self.maps,self.bakery,self.callbackData)
            return
        
        s=self.shadersToDo.pop(0)
        inputMaps=[]
        for m in s.inputMapNames:
            inputMaps.append(self.maps[m])
        self.bakery.asyncRenderMap(self.rawTile,inputMaps,s,self.mapDone,[s.name])
        
    def mapDone(self,map,name):
        self.maps[name]=map
        self.doNext()
        
class _RawTile:
    """Unbaked Tile"""
    def __init__(self, x, y, scale):
        self.x=x
        self.y=y
        self.scale=scale
        self.specifiedMaps={}
        
    def addSpecifiedMap(self, map):
        name=map.name
        if name not in self.specifiedMaps:
            self.specifiedMaps[name]=[map]
        else:
            self.specifiedMaps[name].append(map)
    
    def _tileFromMaps(self, bakery, maps):
        renderMaps={}
        for m in bakery.renderMapNames:
            if m not in maps:
                print "Error: Required RenderMap missing, presumed not generated"
            else:
                renderMaps[m]=maps[m]
            
        # Place meshes
        placedMesh=[]
        pass
        
        return Tile(renderMaps,placedMesh,self.x,self.y,self.scale)
    
    def asyncBake(self, bakery, callback, callbackParams=[]):
        callbackData=(callback,callbackParams)
        r=_AsyncMapRenderer(bakery, self, callbackData)
    
    def _asyncBakeMapsDone(self, maps, bakery, callbackData):
        t=self._tileFromMaps(bakery, maps)
        callbackData[0](t,*(callbackData[1]))
        
    
    def bake(self, bakery):
        # Make Maps
        maps={}
        for s in bakery.shaders:
            inputMaps=[]
            for m in s.inputMapNames:
                inputMaps.append(maps[m])
            maps[s.name]=bakery.renderMap(self,inputMaps,s)
        
        return self._tileFromMaps(bakery, maps)
 
class Tile:
    """Baked Tile"""
    def __init__(self,renderMaps,placedMesh, x, y, scale):
        self.x=x
        self.y=y
        self.scale=scale
        self.renderMaps=renderMaps
        self.placedMesh=placedMesh
    def saveMaps(self,path):
        for map in self.renderMaps:
            m=self.renderMaps[map]
            m.tex.write(path+m.name+".png")
        
class SpecifiedMap:
    def __init__(self,name):
        self.name=name
        
class MapShader:
    def __init__(self, name, folder):
        file=folder+'maps/'+name+'.txt'
        d=parseFile(file)
        #inputMapNames, tex2DNames, shaderSource
        if "Input" in d:
            self.inputMapNames=d["Input"]
        else:
            self.inputMapNames=[]
            
        if "Tex2D" in d:
            tex2D=d["Tex2D"]
        else:
            tex2D=[]
        
        shaderSource='\n'.join(d["Shader"])
        
        
        self.name=name
        
        texLines=[]
        paramsStrs=[]
        paramsDefStrs=[]
        for i in xrange(len(self.inputMapNames)):
            texLines.append('  in uniform sampler2D tex_'+str(i)+': TEXUNIT'+str(i)+',')
            paramsStrs.append('tex2D(tex_'+str(i)+', l_tex)')
            paramsDefStrs.append('float4 map_'+self.inputMapNames[i])
     
        self.shaderTex=[]
        for t in tex2D:
            i=len(texLines)
            texName='tex_'+str(i)
            texLines.append('  in uniform sampler2D '+texName+': TEXUNIT'+str(i)+',')
            paramsStrs.append('tex_'+str(i))
            paramsDefStrs.append('sampler2D tex2D_'+t)
            tex=loadTex(folder+'textures/'+t)
            texStage=TextureStage(t+"stage")
            self.shaderTex.append((texStage,tex))
            
       
        texText='\n'.join(texLines)
        paramsText=', '.join(paramsStrs)
        paramsDef=', '.join(paramsDefStrs)
        
        if len(paramsDef)>0:
            paramsDef=", "+paramsDef
            paramsText=", "+paramsText
        
        self.source=mapMakerShaderSource.replace('#tex#',texText)
        self.source=self.source.replace('#params#',paramsText)
        self.source=self.source.replace('#source#',shaderSource)
        self.source=self.source.replace('#paramsDef#',paramsDef)
        
        if useShaderFiles:
            outLoc='ShadersOut/'+name+'.sha'
            fOut=open(outLoc, 'w')
            fOut.write(self.source)
            fOut.close()
            self.shader=loader.loadShader(outLoc)
        else:
            self.shader=Shader.make(self.source)
        
        self.resolutionScale=1
        self.addPixels=0
        
        if "Settings" in d:
            for s in d["Settings"]:
                t=s.split()
                v=t[1]
                m=t[0]
                if m=='resolutionScale':
                    self.resolutionScale=float(v)
                elif m=='addPixels':
                    self.addPixels=int(v)
        
def loadTex(path):
    extensions=['png','jpg']
    for t in extensions:
        tex=loader.loadTexture(path+'.'+t,okMissing=True)
        if tex!=None:
            return tex
     
class Map:
    """A rendered Map for a tile"""
    def __init__(self,name,tex):
        self.name=name
        self.tex=tex
        
class PlacedMesh:
    """An indicator for where a mesh should be placed in a tile"""
    def __init__(self):
        pass