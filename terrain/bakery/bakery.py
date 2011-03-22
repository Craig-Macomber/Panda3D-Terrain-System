class Bakery:
    """
    A factory for tiles. subclass and impliment the methods below.
    """
    def hasTile(self, xStart, yStart, tileSize):
        """If one is using a cashed tile source instead of a live bakery, this would be sometimes be false"""
        raise NotImplementedError()
        
    def getTile(self, xStart, yStart, tileSize):
        """
        returns a tile for the specified positions and size
        """
        raise NotImplementedError()
    
    def asyncGetTile(self, xStart, yStart, tileSize, callback, callbackParams=()):
        """
        like getTile, but calls callback(tile,*callbackParams) when done
        """
        raise NotImplementedError()
        #callback(self.getTile(xStart, yStart, tileSize),*callbackParams)
    



class Tile:
    """
    Baked Tile
    renderMaps is dict (mapName:Map)
    
    """
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


class Map:
    """A rendered Map for a tile"""
    def __init__(self,name,tex):
        """
        tex should be a Texture instance
        name should be the string name of the map
        """
        self.name=name
        self.tex=tex
        
class PlacedMesh:
    """An indicator for where a mesh should be placed in a tile"""
    def __init__(self):
        pass






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



class SpecifiedMap:
    def __init__(self,name):
        self.name=name
        
def loadTex(pathx,mask=False):
    path=pathPrefix()+pathx
    extensions=['png','jpg','tiff','tif']
    for t in extensions:
        #if os.path.exists(path+'.'+t):
        #    if os.path.exists(path+'_mask.'+t):
        #        tex=loader.loadTexture(path+'.'+t,path+'_mask.'+t)
        #    else:
        #        tex=loader.loadTexture(path+'.'+t)
            if mask:
                tex=loader.loadTexture(path+'.'+t,path+'_mask.'+t,okMissing=True)
            else:
                tex=loader.loadTexture(path+'.'+t,okMissing=True)
            
            if tex is None:
                print "Texture load failed:",path+'.'+t
            else:
                return tex
    print "Texture not found:",path
     
