import math

from bakery import Bakery
from bakery import Map
from bakery import Tile
from bakery import loadTex
from bakery import parseFile
from bakery import pathPrefix
from direct.showbase.RandomNumGen import *
import os
from panda3d.core import *
from panda3d.core import PerlinNoise2
from panda3d.core import StackedPerlinNoise2
from textureRenderer import *

# Size Map textures are rendered
tileMapSize = 257

class ADBakery(Bakery):

    """
    """

    def __init__(self, editorFile, bakeryFolder):
        """
        A factory for tiles.
        """
        self.terrain = _Terrain()

    def hasTile(self, xStart, yStart, tileSize):
        """
        If one is using a cashed tile source instead of a live bakery, this would be sometimes be false
        """
        return True

    def getTile(self, xStart, yStart, scale):
        """
        returns a tile for the specified positions and size
        """
        sizeY = tileMapSize
        sizeX = tileMapSize
        getHeight = self.terrain.getHeight
        
        noiseTex=Texture("NoiseTex")
        noiseTex.setup2dTexture(sizeX, sizeY, Texture.TUnsignedByte, Texture.FRgb)
        p=noiseTex.modifyRamImage()
        step=noiseTex.getNumComponents()*noiseTex.getComponentWidth()
        scalar=1000.0
        for y in range(sizeY):
            yPos=scalar*(1.0*y*scale/(sizeY-1)+yStart)
            for x in range(sizeX):
                height = getHeight(scalar*(1.0*x*scale/(sizeX-1) + xStart), yPos)
                r=min(255,max(0,height*256))
                g=r*256
                b=g*256
                index = (sizeX * y + x)*step
                p.setElement(index, b%256)#Blue
                p.setElement(index+1, g%256)#Green
                p.setElement(index+2, r)#Red
        
        return Tile({"height":Map("height", noiseTex)},[], xStart, yStart, scale)

    def asyncGetTile(self, xStart, yStart, scale, callback, callbackParams=[]):
        """
        like getTile, but calls callback(tile,*callbackParams) when done
        """
        callback(self.getTile(xStart, yStart, scale), *callbackParams)


###############################################################################
#   Terrain
###############################################################################

class _Terrain():
    """A terrain contains a set of geomipmaps, and maintains their common properties."""

    def __init__(self):
        """Create a new terrain centered on the focus.

        The focus is the NodePath where the LOD is the greatest.
        id is a seed for the map and unique name for any cached heightmap images

        """

        ##### Terrain Tile physical properties
        self.maxHeight = 300
        self.dice = RandomNumGen(TimeVal().getUsec())
        self.id = self.dice.randint(2, 1000000)

        # scale the terrain vertically to its maximum height
        #self.setSz(self.maxHeight)
        # scale horizontally to appearance/performance balance
        #self.horizontalScale = 1.0
        #self.setSx(self.horizontalScale)
        #self.setSy(self.horizontalScale)

        ##### heightmap properties
        self.initializeHeightMap(id)

    def initializeHeightMap(self, id=0):
        """ """

        # the overall smoothness/roughness of the terrain
        self.smoothness = 80
        # how quickly altitude and roughness shift
        self.consistency = self.smoothness * 8
        # waterHeight is expressed as a multiplier to the max height
        self.waterHeight = 0.3
        # for realism the flatHeight should be at or very close to waterHeight
        self.flatHeight = self.waterHeight + 0.04

        #creates noise objects that will be used by the getHeight function
        self.generateNoiseObjects()

    def generateNoiseObjects(self):
        """Create perlin noise."""

        # See getHeight() for more details....

        # where perlin 1 is low terrain will be mostly low and flat
        # where it is high terrain will be higher and slopes will be exagerrated
        # increase perlin1 to create larger areas of geographic consistency
        self.perlin1 = StackedPerlinNoise2()
        perlin1a = PerlinNoise2(0, 0, 256, seed=self.id)
        perlin1a.setScale(self.consistency)
        self.perlin1.addLevel(perlin1a)
        perlin1b = PerlinNoise2(0, 0, 256, seed=self.id * 2 + 123)
        perlin1b.setScale(self.consistency / 2)
        self.perlin1.addLevel(perlin1b, 1 / 2)


        # perlin2 creates the noticeable noise in the terrain
        # without perlin2 everything would look unnaturally smooth and regular
        # increase perlin2 to make the terrain smoother
        self.perlin2 = StackedPerlinNoise2()
        frequencySpread = 3.0
        amplitudeSpread = 3.4
        perlin2a = PerlinNoise2(0, 0, 256, seed=self.id * 2)
        perlin2a.setScale(self.smoothness)
        self.perlin2.addLevel(perlin2a)
        perlin2b = PerlinNoise2(0, 0, 256, seed=self.id * 3 + 3)
        perlin2b.setScale(self.smoothness / frequencySpread)
        self.perlin2.addLevel(perlin2b, 1 / amplitudeSpread)
        perlin2c = PerlinNoise2(0, 0, 256, seed=self.id * 4 + 4)
        perlin2c.setScale(self.smoothness / (frequencySpread * frequencySpread))
        self.perlin2.addLevel(perlin2c, 1 / (amplitudeSpread * amplitudeSpread))
        perlin2d = PerlinNoise2(0, 0, 256, seed=self.id * 5 + 5)
        perlin2d.setScale(self.smoothness / (math.pow(frequencySpread, 3)))
        self.perlin2.addLevel(perlin2d, 1 / (math.pow(amplitudeSpread, 3)))
        perlin2e = PerlinNoise2(0, 0, 256, seed=self.id * 6 + 6)
        perlin2e.setScale(self.smoothness / (math.pow(frequencySpread, 4)))
        self.perlin2.addLevel(perlin2e, 1 / (math.pow(amplitudeSpread, 4)))


    def getHeight(self, x, y):
        """Returns the height at the specified terrain coordinates.

        The values returned should be between 0 and 1 and use the full range.
        Heights should be the smoothest and flatest at flatHeight.

        """

        # all of these should be in the range of 0 to 1
        p1 = (self.perlin1(x, y) + 1) / 2 # low frequency
        p2 = (self.perlin2(x, y) + 1) / 2 # high frequency
        fh = self.flatHeight

        # p1 varies what kind of terrain is in the area, p1 alone would be smooth
        # p2 introduces the visible noise and roughness
        # when p1 is high the altitude will be high overall
        # when p1 is close to fh most of the visible noise will be muted
        return (p1 - fh + (p1 - fh) * (p2 - fh)) / 2 + fh
        # if p1 = fh, the whole equation simplifies to...
        # 1. (fh - fh + (fh - fh) * (p2 - fh)) / 2 + fh
        # 2. ( 0 + 0 * (p2 - fh)) / 2 + fh
        # 3. (0 + 0 ) / 2 + fh
        # 4. fh
        # The important part to understanding the equation is at step 2.
        # The closer p1 is to fh, the smaller the mutiplier for p2 becomes.
        # As p2 diminishes, so does the roughness.

