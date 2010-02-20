from pandac.PandaModules import *

loadPrcFile("TerrainConfig.prc")

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
import direct.directbase.DirectStart

from bakery import *
from renderer import *
from direct.filter.CommonFilters import CommonFilters
import math

from direct.task import Task
from pandac.PandaModules import PandaSystem
print PandaSystem.getVersionString()
backBinName="background"

"""

This is a test of the terrain system.


"""

# Create a bakery that uses the "bakery2" folder for its resources
b=LiveBakery(None,"bakery2")

# Make the main (highest LOD) tiler
n=RenderAutoTiler('render',b,1,base.cam,1.5,3.0)
n.reparentTo(render)

# Make the background LOD tilers. This causes lots of over draw
# The over draw issues should be resolved in the future somehow.
bg1=RenderAutoTiler('render',b,8,base.cam,1,1.3)
bg1.reparentTo(render)
bg1.setDepthTest(False)
bg1.setDepthWrite(False)
bg1.setBin(backBinName,1)

bg2=RenderAutoTiler('render',b,64,base.cam,1,1.1)
bg2.reparentTo(render)
bg2.setDepthTest(False)
bg2.setDepthWrite(False)
bg2.setBin(backBinName,0)

# Show the buffers
base.bufferViewer.toggleEnable()

# Make a little UI input handeling class
class UI(DirectObject):
    def __init__(self):
        self.accept("v", base.bufferViewer.toggleEnable)
        self.accept("V", base.bufferViewer.toggleEnable)
        self.accept("p", self.save)
        self.accept("a", self.analize)
        self.accept("c", self.color)
        base.bufferViewer.setPosition("llcorner")
        base.bufferViewer.setCardSize(.25, 0.0)
    def save(self):
        #t[0][0].saveMaps("pics/map_")
        pass
    def analize(self):
        print ""
        render.analyze()
        print ""
        print n.tilesMade," Tiles Made for high LOD"
        print len(n.getTiles()), " Tiles displaying for high LOD"
        print bg1.tilesMade," Tiles Made for mid LOD"
        print len(bg1.getTiles()), " Tiles displaying for mid LOD"
        print bg2.tilesMade," Tiles Made for low LOD"
        print len(bg2.getTiles()), " Tiles displaying for low LOD"
    def color(self):
        if bg1.hasColor():
            bg1.clearColor()
        else:
            bg1.setColor(1,.5,.5)
w=UI()


# Setup some lights
dlight = DirectionalLight('dlight')
dlight.setColor(VBase4(0.9, 0.9, 0.8, 1))
dlnp = render.attachNewNode(dlight)
#dlnp.setHpr(0, -60, 0)
render.setLight(dlnp)

alight = AmbientLight('alight')
alight.setColor(VBase4(0.1, 0.1, 0.2, 1))
alnp = render.attachNewNode(alight)
render.setLight(alnp)


dayCycle=dlnp.hprInterval(8.0,Point3(0,360,0))
dayCycle.loop()

# Filter to display the glow map's glow via bloom.
filters = CommonFilters(base.win, base.cam)
filterok = filters.setBloom(blend=(0,0,0,1), desat=0.5, intensity=2.5, size="small",mintrigger=0.0, maxtrigger=1.0)

# Init camera
base.disableMouse()
camLens=base.camLens
camLens.setNear(.001)

#Task to move the camera
def cameraTask(task):
    time=task.time*1
    angledegrees = time * 6.0 * 2
    angleradians = angledegrees * (math.pi / 180.0)
    base.camera.setPos(-time * .05,-1.5*math.sin(angleradians*.5),.12)
    base.camera.setHpr(sin(angleradians*.5)*220, -10, 0)

    return Task.cont

taskMgr.add(cameraTask, "cameraTask")



run()