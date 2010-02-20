from pandac.PandaModules import *

loadPrcFile("TerrainConfig.prc")

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
import direct.directbase.DirectStart
from direct.filter.CommonFilters import CommonFilters

from bakery import *
from renderer import *

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


tileSize=.05

# Make the main (highest LOD) tiler
n=RenderAutoTiler('render',b,tileSize,base.cam,4.5,5.5)
n.reparentTo(render)


useLowLOD=True
useMidLOD=True

# Make the background LOD tilers. This causes lots of over draw
# The over draw issues should be resolved in the future somehow.

cm=CardMaker("depthwiper")
cm.setFrameFullscreenQuad()

'''
c.reparentTo(base.camera)
c.setDepthTest(False)
c.setDepthWrite(True)
c.setBin(backBinName,2)
dist=10000
c.setY(dist)
c.setScale(dist)
c.clearShader()
c.setAttrib(DepthTestAttrib.make(RenderAttrib.MAlways))
c.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.MNone))
'''

dist=10000
clearCardHolder=NodePath('clearCardHolder')
clearCardHolder.reparentTo(base.camera)
clearCardHolder.setDepthTest(False)

c=NodePath(cm.generate())
c.reparentTo(clearCardHolder)
c.setBin(backBinName,11)


c=NodePath(cm.generate())
c.reparentTo(clearCardHolder)
c.setBin(backBinName,1)

clearCardHolder.setY(dist)
clearCardHolder.setScale(dist)
clearCardHolder.setAttrib(DepthTestAttrib.make(RenderAttrib.MAlways))
clearCardHolder.setAttrib(ColorWriteAttrib.make(ColorWriteAttrib.MNone))
if useMidLOD:
    bg1=RenderAutoTiler('render',b,tileSize*8,base.cam,1.5,2.0)
    bg1.reparentTo(render)
    #bg1.setDepthTest(False)
    #bg1.setDepthWrite(False)
    bg1.setBin(backBinName,10)
    bg1.setScale(100)

if useLowLOD:
    bg2=RenderAutoTiler('render',b,tileSize*64,base.cam,1.0,1.2)
    bg2.reparentTo(render)
    bg2.setDepthTest(False)
    bg2.setDepthWrite(False)
    bg2.setBin(backBinName,0)
    bg2.setScale(100)




n.setScale(100)


# Show the buffers
base.bufferViewer.toggleEnable()

# Make a little UI input handeling class
class UI(DirectObject):
    def __init__(self):
        self.accept("v", base.bufferViewer.toggleEnable)
        self.accept("V", base.bufferViewer.toggleEnable)
        self.accept("p", self.save)
        self.accept("x", self.analize)
        self.accept("c", self.color)
        base.bufferViewer.setPosition("llcorner")
        base.bufferViewer.setCardSize(.25, 0.0)
    def save(self):
        #t[0][0].saveMaps("pics/map_")
        i=0
        for t in n.getTiles():
            t.bakedTile.saveMaps("pics/map_"+str(i)+"_")
            i+=1
        pass
    def analize(self):
        print ""
        render.analyze()
        print ""
        print n.tilesMade," Tiles Made for high LOD"
        print len(n.getTiles()), " Tiles displaying for high LOD"
        
        if useMidLOD:
            print bg1.tilesMade," Tiles Made for mid LOD"
            print len(bg1.getTiles()), " Tiles displaying for mid LOD"
        if useLowLOD:
            print bg2.tilesMade," Tiles Made for low LOD"
            print len(bg2.getTiles()), " Tiles displaying for low LOD"
        
    def color(self):
        if useMidLOD:
            if bg1.hasColor():
                bg1.clearColor()
            else:
                bg1.setColor(1,.5,.5)
w=UI()


# Setup some lights
dlight = DirectionalLight('dlight')
dlight.setColor(VBase4(0.9, 0.9, 0.8, 1))
dlnp = render.attachNewNode(dlight)
dlnp.setHpr(0, 0, 0)
render.setLight(dlnp)

alight = AmbientLight('alight')
alight.setColor(VBase4(0.2, 0.2, 0.4, 1))
alnp = render.attachNewNode(alight)
render.setLight(alnp)


dayCycle=dlnp.hprInterval(10.0,Point3(0,360,0))
dayCycle.loop()


# Filter to display the glow map's glow via bloom.
filters = CommonFilters(base.win, base.cam)
filterok = filters.setBloom(blend=(0,0,0,1), desat=0.5, intensity=2.5, size="small",mintrigger=0.0, maxtrigger=1.0)



# Init camera
base.disableMouse()
camLens=base.camLens
camLens.setNear(.1)





from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.task.Task import Task
from direct.showbase.DirectObject import DirectObject
import random, sys, os, math

# Figure out what directory this program is in.
MYDIR=os.path.abspath(sys.path[0])
MYDIR=Filename.fromOsSpecific(MYDIR).getFullpath()

#font = loader.loadFont("cmss12")
font = TextNode.getDefaultFont()

# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1), font = font,
                        pos=(-1.3, pos), align=TextNode.ALeft, scale = .05)

# Function to put title on the screen.
def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1,1,1,1), font = font,
                        pos=(1.3,-0.95), align=TextNode.ARight, scale = .07)
#A simple function to make sure a value is in a given range, -1 to 1 by default
def restrain(i, mn = -1, mx = 1): return min(max(i, mn), mx)

class World(DirectObject):

    def __init__(self):
        DirectObject.__init__(self)
        
        base.win.setClearColor(Vec4(0,0,0,1))

        # Post the instructions

        self.title = addTitle("Infinite Ralph")
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")
        self.inst2 = addInstructions(0.90, "WASD + Arrow Keys")
        self.inst3 = addInstructions(0.85, "Shift for hyper")
        self.inst3 = addInstructions(0.80, "X for analyze")
        self.inst3 = addInstructions(0.75, "C tints mid LOD")
        self.inst3 = addInstructions(0.75, "V toggles buffer viewer")
        
        
        # Create the main character, Ralph

        ralphStartPos = Vec3(0,0,0)
        self.ralph = Actor("models/ralph",
                                 {"run":"models/ralph-run"})
        self.ralph.reparentTo(render)
        self.ralph.setScale(.02)
        self.ralph.setPos(ralphStartPos)
        self.ralph.setShaderAuto()
        
        #Now we use controlJoint to get a NodePath that's in control of his neck
        #This must be done before any animations are played
        #self.neck = self.ralph.controlJoint(None, 'modelRoot', 'Neck')

        # Create a floater object.  We use the "floater" as a temporary
        # variable in a variety of calculations.
        
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.ralph)

        # Accept the control keys for movement and rotation
        
        self.accept("escape", sys.exit)

        self.keyMap = {}
        
        self.addKey("w","forward")
        self.addKey("a","left")
        self.addKey("s","backward")
        self.addKey("d","right")
        self.addKey("arrow_left","turnLeft")
        self.addKey("arrow_right","turnRight")
        self.addKey("arrow_down","turnDown")
        self.addKey("arrow_up","turnUp")
        
        self.setKey('zoom',0)
        self.accept("wheel_up", self.setKey, ['zoom',1])
        self.accept("wheel_down", self.setKey, ['zoom',-1])
        
        #addKey("wheel_down","zoomOut")
        #addKey("wheel_up","zoomIn")
        self.addKey("shift","hyper")

        taskMgr.add(self.move,"moveTask")

        # Game state variables
        self.isMoving = False

        # Set up the camera
        
        base.disableMouse()
        base.camera.setH(180)
        #base.camera.setPos(self.ralph.getX(),self.ralph.getY()+10,2)
        #base.camera.reparentTo(n)
        
        #self.ralph.enableBlend()
        #self.ralph.setControlEffect("run",1)
        #self.ralph.setControlEffect("walk",0)
        
        base.camera.reparentTo(self.ralph)
        self.camDist=100.0
        #print self.ralph.listJoints()
        #print self.ralph.getAnimNames()
        
    #Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value
    
    def addKey(self,key,name,allowShift=True):
        self.accept(key, self.setKey, [name,True])
        self.accept(key+"-up", self.setKey, [name,False])  
        self.accept(key.upper()+"-up", self.setKey, [name,False])
        
        if allowShift:
            self.addKey("shift-"+key,name,False)
        
        self.keyMap[name]=0
    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self, task):

        # Get the time elapsed since last frame. We need this
        # for framerate-independent movement.
        elapsed = globalClock.getDt()

        # If the camera-left key is pressed, move camera left.
        # If the camera-right key is pressed, move camera right.
        #base.camera.setPos(self.ralph,Vec3(0,200,0))
        #base.camera.lookAt(self.ralph)
        
        
        
        turnRightAmount=self.keyMap["turnRight"]-self.keyMap["turnLeft"]
        turnUpAmmount=self.keyMap["turnUp"]-self.keyMap["turnDown"]
        
        #zoomOut=self.keyMap["zoomOut"]-self.keyMap["zoomIn"]
        zoomOut=self.keyMap["zoom"]
        self.camDist=max(min(1200,self.camDist+zoomOut*elapsed*50),30)
        #print zoomOut
        
        self.ralph.setH(self.ralph.getH() - elapsed*100*turnRightAmount)
        base.camera.setP(base.camera.getP() + elapsed*100*turnUpAmmount)
        
        # save ralph's initial position so that we can restore it,
        # in case he falls off the map or runs into something.

        startpos = self.ralph.getPos()

        # If a move-key is pressed, move ralph in the specified direction.
        forwardMove=0.0
        rightMove=0.0
        if self.keyMap["forward"]:
            forwardMove+=1.0
        if self.keyMap["backward"]:
            forwardMove-=.5
        if self.keyMap["left"]:
            rightMove-=.5
        if self.keyMap["right"]:
            rightMove+=.5
        
        forwardMove*=1.0-abs(rightMove)
        
        if self.keyMap["hyper"]:
            speed=10
        else:
            speed=1
        rightMove*=speed
        forwardMove*=speed
        
        self.ralph.setX(self.ralph, -elapsed*25*rightMove)
        self.ralph.setY(self.ralph, -elapsed*25*forwardMove)
        h=n.height(self.ralph.getX(n),self.ralph.getY(n))
        self.ralph.setZ(n,h)
        
        
        
        #self.ralph.setZ(10)
        
        # If ralph is moving, loop the run animation.
        # If he is standing still, stop the animation.
        
        def sign(n):
            if n>=0: return 1
            #if n==0: return 0
            return -1
        
        if rightMove!=0 or forwardMove!=0:
            self.ralph.setPlayRate(forwardMove+abs(rightMove)*sign(forwardMove), 'run')
            if self.isMoving is False:
                self.ralph.loop("run")
                
                #self.ralph.loop("walk")
                self.isMoving = True
        else:
            if self.isMoving:
                self.ralph.stop()
                self.ralph.pose("walk",5)
                self.isMoving = False

        # If the camera is too far from ralph, move it closer.
        # If the camera is too close to ralph, move it farther.
        
        
        '''
        camvec = self.ralph.getPos() - base.camera.getPos()
        
        
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if (camdist > 10.0):
            base.camera.setPos(base.camera.getPos() + camvec*(camdist-10))
            camdist = 10.0
        if (camdist < 5.0):
            base.camera.setPos(base.camera.getPos() - camvec*(5-camdist))
            camdist = 5.0
        '''
        
        # The camera should look in ralph's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above ralph's head.
      
        #self.floater.setPos(self.ralph.getPos())
        self.floater.setZ(10)
        base.camera.setPos(self.floater,0,0,0)
        base.camera.setPos(base.camera,0,-self.camDist,0)
        
        '''
        base.camera.setZ(self.floater.getZ()+2.0)
        base.camera.lookAt(self.floater)
        '''
        
        #Here we multiply the values to get the amount of degrees to turn
        #Restrain is used to make sure the values returned by getMouse are in the
        #valid range. If this particular model were to turn more than this,
        #significant tearing would be visable
        #self.neck.setP(restrain(20) * 50)
        #self.neck.setH(restrain(30) * 20)
        

        return Task.cont


w = World()
run()

