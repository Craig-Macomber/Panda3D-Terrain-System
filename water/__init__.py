from panda3d.core import *


class WaterNode(NodePath):

    def __init__(self, x1, y1, x2, y2, z):
        NodePath.__init__(self,"Water")
        self.reparentTo(render)
        print('setting up water plane at z=' + str(z))

        # Water surface
        maker = CardMaker('water')
        maker.setFrame(x1, x2, y1, y2)

        self.waterNP = self.attachNewNode(maker.generate())
        self.waterNP.setHpr(0, -90, 0)
        self.waterNP.setPos(0, 0, z)
        self.waterNP.setTransparency(TransparencyAttrib.MAlpha)
        self.waterNP.setShader(loader.loadShader('water/water.sha'))
        self.waterNP.setShaderInput('wateranim', Vec4(0.03, -0.015, 64.0, 0)) # vx, vy, scale, skip
        # offset, strength, refraction factor (0=perfect mirror, 1=total refraction), refractivity
        self.waterNP.setShaderInput('waterdistort', Vec4(0.4, 4.0, 0.35, 0.045))

        # Reflection plane
        self.waterPlane = Plane(Vec3(0, 0, z + 1), Point3(0, 0, z))
        planeNode = PlaneNode('self.waterPlane')
        planeNode.setPlane(self.waterPlane)

        # Buffer and reflection camera
        buffer = base.win.makeTextureBuffer('waterBuffer', 512, 512)
        buffer.setClearColor(Vec4(0, 0, 0, 1))

        cfa = CullFaceAttrib.makeReverse()
        rs = RenderState.make(cfa)

        self.watercamNP = base.makeCamera(buffer)
        self.watercamNP.reparentTo(self)

        #sa = ShaderAttrib.make()
        #sa = sa.setShader(loader.loadShader('shaders/splut3Clipped.sha') )

        cam = self.watercamNP.node()
        cam.setLens(base.camLens)
        cam.setInitialState(rs)
        cam.setTagStateKey('Clipped')
        #cam.setTagState('True', RenderState.make(sa))

        # ---- water textures ---------------------------------------------

        # reflection texture, created in realtime by the 'water camera'
        tex0 = buffer.getTexture()
        tex0.setWrapU(Texture.WMClamp)
        tex0.setWrapV(Texture.WMClamp)
        ts0 = TextureStage('reflection')
        self.waterNP.setTexture(ts0, tex0)

        # distortion texture
        tex1 = loader.loadTexture('water/water.png')
        ts1 = TextureStage('distortion')
        self.waterNP.setTexture(ts1, tex1)

        # ---- Fog --- broken
#         min = Point3(x1, y1, -999.0)
#         max = Point3(x2, y2, z)
#         boundry = BoundingBox(min, max)
#         waterFog = Fog('waterFog')
#         waterFog.setBounds(boundry)
#         colour = (0.2, 0.5, 0.8)
#         waterFog.setColor(*colour)
#         waterFog.setExpDensity(0.05)
#         self.attachNewNode(waterFog)
#         #self.setFog(waterFog)
        
    def update(self):
        # update matrix of the reflection camera
        mc = base.camera.getMat(self)
        mf = self.waterPlane.getReflectionMat()
        self.watercamNP.setMat(mc * mf)
