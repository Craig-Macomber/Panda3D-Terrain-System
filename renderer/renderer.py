from direct.showbase.ShowBase import ShowBase
import direct.directbase.DirectStart
from pandac.PandaModules import *

from terrain.bakery.bakery import Tile, parseFile, loadTex
import math

"""
Planned Renderers
RenderNode - Basic Tile Renderer
RenderAutoTiler(RenderNode) - Fetches tiles near a ficuse from a tile source and renders them
GeoClipMapper - 

"""

class RenderNode(NodePath):
    def __init__(self,path,terrainNode,heightScale):
        NodePath.__init__(self,path+"_render")
        
        self.heightScale=heightScale
        
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
        self.terrainNode=terrainNode
        self.terrainNode.reparentTo(self)
        #self.terrainNode.setShader(loader.loadShader(path+"/render.sha"))
        #self.terrainNode.setShaderAuto()
        
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
                    tex=loadTex(path+"/textures/"+name)
                    self.terrainNode.setTexture(texStage,tex)
                    self.terrainNode.setShaderInput('tex2D_'+name,tex)
                    self.texList.append((texStage,float(s[2])))
                    
                elif source=='map':
                    setTexModes(s[2:])
                    self.mapTexStages[s[0]]=texStage

                else:
                    print 'Invalid source for '+name+' int Tex2D'
