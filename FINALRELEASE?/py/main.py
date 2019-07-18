import wx
import requests
import itertools
import numpy, json, pandas
import random, math

locale = wx.Locale.GetSystemLanguage() 

ACTIONS=numpy.array([0], dtype=numpy.int16)

CURRENT_SELECTED_LEVEL_DATA = None
CURRENT_SELECTED_LEVEL =      0
CURRENT_SELECTED_LEVEL_OBJ =  None
CURRENT_SELECTED_LEVEL_WARP = None
OBJ_DF=None
WARP_DF=None

WORLD_DATA=None

SPRITE_INDEX = 0
DEPTH = 0
TILE_DEF = 0
EXTRA_DATA = 0

TYPE=97
POS=0
PARAMS=[""]

ID=0
POSWARP=0
DATA=0

SELECTING_OBJS_OR_WARPS="OBJ"
SELECTING_TILES_FROM_SELECTOR=False

SBW=None
SBH=None

TOOLS="BRUSH"
CURRENT_DRAW_TYPE_SELECT="TILE"

IS_DRAWING_PRESETS=False
IS_CLONING=False

TILE_PRESET=[[0]]

SELECTION_START=[0,0]
SELECTION_END=[0,0]

class Convert:
     def __init__(self):
          pass
     def Convert(self, data):

          self.jsondata=self.getRaw(data)

          print(type(self.jsondata),self.jsondata)
          self.world_data=[]
          for i in range(len(self.jsondata["world"])):
               self.world_data.append(self.Level(i))
                           
          return self.world_data #numpy.array(level1data, dtype=numpy.int64)

     def getRaw(self, data):
          jsos=json.loads(data)
          return jsos
     
     def Level(self, which):
          print(len(self.jsondata["world"][which]["zone"]),self.jsondata["world"][which]["zone"])
          return {"id":self.jsondata["world"][which]["id"],
                  "name":self.jsondata["world"][which]["name"],
                  "zones":[{"id_zone":self.jsondata["world"][which]["zone"][x]["id"],
                           "playerpos":self.jsondata["world"][which]["zone"][x]["initial"],
                           "color":self.jsondata["world"][which]["zone"][x]["color"],
                           "music":self.jsondata["world"][which]["zone"][x]["music"],
                           "data":self.jsondata["world"][which]["zone"][x]["data"],
                           "obj":self.jsondata["world"][which]["zone"][x]["obj"],
                           "warp":self.jsondata["world"][which]["zone"][x]["warp"]
                           } for x in range(len(self.jsondata["world"][which]["zone"]))]}
               

def trueresize(array,shape,cval,fillall=False):
     new=numpy.array([[cval]*shape[0]]*shape[1], dtype=int)
     if not fillall:
          for x,y in itertools.product(range(shape[0]),range(shape[1])):
               if x < (array.shape[1]) and y < (array.shape[0]):
                    new[y,x] = array[y,x]
               else:
                    pass
     return new

def decode(tiledata):
     CONST_DEPTH=32768
     CONST_T_DEF=65536
     CONST_EXTRA=16777216

     sprite_index=tiledata%CONST_DEPTH
     depth=int(bool((tiledata-sprite_index)%CONST_T_DEF))
     extra_data=int((((tiledata-sprite_index)-CONST_EXTRA)/CONST_EXTRA)+0.93359375)
     tiledef=int((tiledata-sprite_index-(extra_data*CONST_EXTRA)-(depth*CONST_DEPTH))/CONST_T_DEF)
     return sprite_index, depth, extra_data, tiledef

def encode(sprite_index, depth, extra_data, tiledef):
     CONST_DEPTH=32768
     CONST_T_DEF=65536
     CONST_EXTRA=16777216
     tile_data = sprite_index+((CONST_DEPTH*int(bool(depth)))+(CONST_T_DEF*tiledef)+(CONST_EXTRA*extra_data))
     return tile_data

def hextorgb(color):
     r=int(color[0:2],16)
     g=int(color[2:4],16)
     b=int(color[4:6],16)
     return r,g,b
def rgbtohex(r,g,b):
     print(r,g,b)
     if r != 0:
          rhex=str(hex(r))[2:]
     else:
          rhex="00"
     if g != 0:
          ghex=str(hex(g))[2:]
     else:
          ghex="00"
     if b != 0:
          bhex=str(hex(b))[2:]
     else:
          bhex="00"
     print("#"+rhex+ghex+bhex)
     return "#"+rhex+ghex+bhex

def UpdateData():
     global WORLD_DATA,CURRENT_SELECTED_LEVEL_DATA
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["id"]=CURRENT_SELECTED_LEVEL_DATA["id_zone"]
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["playerpos"]=CURRENT_SELECTED_LEVEL_DATA["playerpos"]
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["color"]=CURRENT_SELECTED_LEVEL_DATA["color"] #Errrori dappertutto
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["music"]=CURRENT_SELECTED_LEVEL_DATA["music"] #Errrori dappertutto
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["data"]=CURRENT_SELECTED_LEVEL_DATA["data"].tolist()
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["obj"]=CURRENT_SELECTED_LEVEL_DATA["obj"]
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["warp"]=CURRENT_SELECTED_LEVEL_DATA["warp"]

def decodepos(position):
     CONST_Y=65536
     x=(position%CONST_Y)
     y=int((position-x)/CONST_Y)
     return x,y

def encodepos(x,y):
     CONST_Y=65536
     pos=(x%CONST_Y)+(y*CONST_Y)
     return pos

def create_sprites(image, scale):
     sprite_list=[]

     rangex=int((image.GetHeight()//(16*scale)))
     rangey=int((image.GetWidth()//(16*scale)))
     print(rangex,rangey)
     for x,y in itertools.product(range(rangex),range(rangey)):
          temp=image.GetSubImage(wx.Rect((y*16)*scale,(x*16)*scale,16*scale,16*scale))
          sprite_list.append(temp)
     return sprite_list
def create_powerups(image, scale):
     pw_list=[]
     for i in range(7):
          temp=image.GetSubImage(wx.Rect(i*(16*scale),0,(16*scale),(16*scale)))

          pw_list.append(temp)
     return pw_list
def create_gfx(image, scale):
     gfx_list=[]
     for i in range(4):
          temp = image.GetSubImage(wx.Rect(i*(16*scale),0,(16*scale),(16*scale)))

          gfx_list.append(temp)
     return gfx_list

class DrawPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel,pos=wx.Point(5,30), size=wx.Size((24*27),(24*16)))
          self.panel=panel
          self.SetBackgroundColour(wx.Colour(150,150,150))
          self.rotation=0
          self.Bind(wx.EVT_MOUSE_EVENTS, self.capture_mouse)
          self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown) #         ---------------    Non funzionaaaaa!1!!! trova un modo idiota :P
          self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
          self.Bind(wx.EVT_PAINT, self.OnPaint)
          self.scale=1.5
          self.fileimage=wx.Image("sources\\smb_map.png", type=wx.BITMAP_TYPE_PNG)
          self.spritesheet=self.Rescale(self.fileimage)
          self.images=create_sprites(self.spritesheet, self.scale)

          fileimagetwo=wx.Image("sources\\powerups.png", type=wx.BITMAP_TYPE_PNG)
          rescalepows=self.Rescale(fileimagetwo)#fileimagetwo.Scale(fileimagetwo.GetWidth()*self.scale, fileimagetwo.GetHeight()*self.scale, wx.IMAGE_QUALITY_NEAREST)
          self.powerups=create_powerups(rescalepows, self.scale)

          giefex = wx.Image("sources\\barrier.png", type=wx.BITMAP_TYPE_PNG)
          rescalegfx = self.Rescale(giefex)#bawwier.Scale(bawwier.GetWidth()*self.scale)
          self.gfx=create_gfx(rescalegfx, self.scale)

          obgiects = wx.Image("sources\\objects.png", type=wx.BITMAP_TYPE_PNG)
          rescaleobj = self.Rescale(obgiects)
          self.objects=self.create_obj(rescaleobj)
          
          self.Bind(wx.EVT_ENTER_WINDOW, self.AllowDrawing)
          self.Bind(wx.EVT_LEAVE_WINDOW, self.DenyDrawing)
          
          self.Bind(wx.EVT_IDLE, self.OnIdling)
          
          self.yoffset=0
          
          self.isVert=False
          self.isBrushing=False
          self.isSelecting=False
          self.selection=False
          self.selectedData=[]
          self.objType={17:"GOOMBA",
                        18:"KOOPA",
                        19:"KOOPA TROOPA",
                        21:"FLYING FISH",
                        22:"UNSPELLABLE PLANT",
                        49:"HAMMER BRO",
                        25:"BOWSER",
                        145:"PLATFORM",
                        146:"BUS PLATFORM",
                        149:"SPRING",
                        177:"FLAG",
                        33:"FIRE TRAP",
                        34:"FIRE BLAST",
                        35:"LAUNCHER",
                        81:"MUSHROOM",
                        82:"FIRE FLOWER",
                        83:"ONEUP",
                        84:"STAR",
                        100:"GOLD FLOWER",
                        97:"COIN",
                        85:"AXE",
                        86:"POISON MUSHROOM",
                        253:"TEXT"}
          self.brushSet=numpy.array([[0]], dtype=int)


     def AllowDrawing(self,event):
          self.isBrushActive=True
     def DenyDrawing(self,event):
          self.isBrushActive=False
          self.isBrushing=False

     def Rescale(self, image):
          imagewo = image.Scale(image.GetWidth()*self.scale, image.GetHeight()*self.scale, wx.IMAGE_QUALITY_NEAREST)
          return imagewo

     def OnIdling(self,event):
          self.Refresh(eraseBackground=False)
          if IS_DRAWING_PRESETS == False and IS_CLONING == False:
               self.brushSet=trueresize(self.brushSet,(SBW.GetValue(),SBH.GetValue()),encode(SPRITE_INDEX, DEPTH, EXTRA_DATA, TILE_DEF), True)
          elif IS_DRAWING_PRESETS == False and IS_CLONING == True:
               self.brushSet=trueresize(self.brushSet,(SBW.GetValue(),SBH.GetValue()),encode(SPRITE_INDEX, DEPTH, EXTRA_DATA, TILE_DEF), False)
          else:
               self.brushSet=numpy.array(TILE_PRESET, dtype=numpy.int64)
          #event.RequestMore()

     def OnPaint(self, event=None):
          global CURRENT_SELECTED_LEVEL_DATA,CURRENT_SELECTED_LEVEL_OBJ,CURRENT_SELECTED_LEVEL_WARP,OBJ_DF,WARP_DF,TOOLS
          global SPRITE_INDEX, DEPTH, EXTRA_DATA, TILE_DEF
          global SELECTION_START, SELECTION_END
          global CURRENT_DRAW_TYPE_SELECT,SELECTING_OBJS_OR_WARPS
          global TYPE,POS,PARAMS
          global ID,POSWARP,DATA
          global IS_CLONING
          global ACTIONS
          try:
               widthlevel=CURRENT_SELECTED_LEVEL_DATA["data"].shape[1]
               heightlevel=CURRENT_SELECTED_LEVEL_DATA["data"].shape[0]

               self.mouse_pos=round(self.mx/(16*self.scale))*(16*self.scale),round(self.my/(16*self.scale))*(16*self.scale)

               dc = wx.BufferedPaintDC(self)
               dc.SetBackground(wx.Brush(wx.Colour(hextorgb(CURRENT_SELECTED_LEVEL_DATA["color"][1:]))))
               dc.Clear()

               dc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))
               dc.SetTextForeground(wx.Colour(255,0,0))
               camoffset=int(self.rotation/10)*2
               screenboundarie=27
               try:
                    if not CURRENT_SELECTED_LEVEL_DATA == self.old_selected_data:
                         camoffset=0
                         self.yoffset=0
                         self.rotation=0
               except:
                    pass
               if (screenboundarie) >= widthlevel:
                    ranges=(0,widthlevel)
               else:
                    if 0-camoffset < 0:
                         ranges=(0,(screenboundarie)-camoffset)
                    elif (screenboundarie)-camoffset > widthlevel:
                         ranges=self.oldranges
                    else:
                         ranges=(0-camoffset,(screenboundarie)-camoffset)
               self.oldranges=ranges

               playerpos=CURRENT_SELECTED_LEVEL_DATA["playerpos"]
               
               for x,y in itertools.product(range(ranges[0],ranges[1]),range(0,heightlevel)):


                    decoded_sprite=decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[0]
                    decoded_tiledef=decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[3]
                    decoded_extradata=decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[2]
                    #print(x,y)
                    posx=((camoffset*16)+(x*16))*self.scale
                    posy=((self.yoffset*8)+y*16)*self.scale
                    
                    
                         #print(SPRITE_INDEX)
                    dc.DrawBitmap(wx.Bitmap(self.images[decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[0]]),posx,posy,True)

                    # BRUSH FUNC
                    try:
                         if CURRENT_DRAW_TYPE_SELECT == "TILE":
                              if posx == self.mouse_pos[0] and posy == self.mouse_pos[1] and self.isBrushing == True and TOOLS == "BRUSH":
                                   mosposy=(int((self.mouse_pos[1])/(16*self.scale)))-int((self.yoffset/2))
                                   mosposx=int((self.mouse_pos[0])/(16*self.scale))-(camoffset)
                                   if CURRENT_SELECTED_LEVEL_DATA["data"][mosposy,mosposx] != encode(SPRITE_INDEX, DEPTH, EXTRA_DATA, TILE_DEF):
                                        ACTIONS[ACTIONS.shape[0]] = 1
                                        ACTIONS = trueresize(ACTIONS, (ACTIONS.shape[0]+1), 0)
                                        print(ACTIONS)
                                        
                                   try:
                                        CURRENT_SELECTED_LEVEL_DATA["data"][mosposy:mosposy+self.brushSet.shape[0],mosposx:mosposx+self.brushSet.shape[1]] = self.brushSet
                                        #print(self.brushSet)
                                   except Exception as error:
                                        
                                        print(error, self.brushSet.shape[0], self.brushSet.shape[1])
                         elif CURRENT_DRAW_TYPE_SELECT == "OBJECT":
                              if posx == self.mouse_pos[0] and posy == self.mouse_pos[1] and self.isBrushing == True and TOOLS == "BRUSH":
                                        mosposy=abs(15-(int((self.mouse_pos[1])/(16*self.scale))))+int((self.yoffset/2))
                                        mosposx=int((self.mouse_pos[0])/(16*self.scale))-(camoffset)
                                        positionowo=encodepos(mosposx,mosposy)
                                        self.updateOBJ_DF()
                                        if CURRENT_SELECTED_LEVEL_DATA["obj"] != []:
                                             checkif=OBJ_DF[OBJ_DF["pos"] == positionowo].to_dict('records')
                                        else:
                                             checkif= []
                                        print(checkif)
                                        try:
                                             if checkif == []:
                                                  
                                                  CURRENT_SELECTED_LEVEL_DATA["obj"].append({"type":TYPE, "pos":positionowo, "param":PARAMS})
                                        except Exception as error:
                                             print(error)
                         elif CURRENT_DRAW_TYPE_SELECT == "WARP":
                              if posx == self.mouse_pos[0] and posy == self.mouse_pos[1] and self.isBrushing == True and TOOLS == "BRUSH":
                                        mosposye=abs(15-(int((self.mouse_pos[1])/(16*self.scale))))+int((self.yoffset/2))
                                        mosposxe=int((self.mouse_pos[0])/(16*self.scale))-(camoffset)
                                        positionowoe=encodepos(mosposxe,mosposye)
                                        self.updateOBJ_DF()
                                        if CURRENT_SELECTED_LEVEL_DATA["warp"] != []:
                                             checkief=WARP_DF[WARP_DF["pos"] == positionowoe].to_dict('records')
                                        else:
                                             checkief= []
                                        print(checkief)
                                        try:
                                             if checkief == []:
                                                  
                                                  CURRENT_SELECTED_LEVEL_DATA["warp"].append({"id":ID, "pos":positionowoe, "data":DATA})
                                        except Exception as error:
                                             print(error)
                    except Exception as error:
                         print(error)

                    # TILEPICKER
                    try:
                         if CURRENT_DRAW_TYPE_SELECT == "TILE":
                              if posx == self.mouse_pos[0] and posy == self.mouse_pos[1] and self.isBrushing == True and TOOLS == "PICKER":
                                   posio=(int((posy)/(16*self.scale)))-int((self.yoffset/2))
                                   posiu=int((posx)/(16*self.scale))-(camoffset)
                                   SPRITE_INDEX, DEPTH, EXTRA_DATA, TILE_DEF= decode(CURRENT_SELECTED_LEVEL_DATA["data"][posio,posiu])
                                   if self.brushSet.shape[0] > 1 or self.brushSet.shape[1] > 1:
                                        IS_CLONING = True
                                   else:
                                        IS_CLONING = False
                                   self.brushSet = CURRENT_SELECTED_LEVEL_DATA["data"][posio:posio+self.brushSet.shape[0],posiu:posiu+self.brushSet.shape[1]]
                                   print(SPRITE_INDEX, DEPTH, EXTRA_DATA, TILE_DEF, posio, posiu, self.yoffset)
                         elif CURRENT_DRAW_TYPE_SELECT == "OBJECT":
                              pass
                    except Exception as error:
                         print(error)

                    #Solid blocks
                    if decoded_tiledef != 0 and decoded_tiledef != 86 and decoded_tiledef != 160:
                         dc.SetTextForeground(wx.Colour(0,0,0))
                         dc.DrawText("S",wx.Point(posx+14,posy+10))

                    # Invisible blocks

                    if decoded_tiledef == 21 or decoded_tiledef == 22:
                         dc.DrawBitmap(wx.Bitmap(self.powerups[5]), posx, posy, True)

                    #Vine block

                    if decoded_tiledef == 24:
                         dc.DrawBitmap(wx.Bitmap(self.powerups[6]), posx, posy, True)

                    
                    #PowerUps

                    if decoded_tiledef == 17 or decoded_tiledef == 21:
                         if decoded_extradata == 81:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[0]), posx, posy, True)
                         if decoded_extradata == 82:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[1]), posx, posy, True)
                         if decoded_extradata == 83:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[2]), posx, posy, True)
                         if decoded_extradata == 84:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[3]), posx, posy, True)
                         if decoded_extradata == 86:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[4]), posx, posy, True)
                    #Invisible barriers
                    if decoded_sprite == 30 and (decoded_tiledef == 1 or decoded_tiledef == 2):
                         dc.DrawBitmap(wx.Bitmap(self.gfx[0]), posx, posy, True)
                    if decoded_tiledef == 86:
                         dc.DrawBitmap(wx.Bitmap(self.gfx[3]), posx, posy, True)
                    if decoded_tiledef == 81 or decoded_tiledef == 82 or decoded_tiledef == 83 or decoded_tiledef == 84 or decoded_tiledef == 85:
                         dc.SetPen(wx.Pen(wx.Colour(255,255,255)))
                         dc.SetBrush(wx.Brush(wx.Colour(0,0,0),wx.BRUSHSTYLE_TRANSPARENT))
                         dc.DrawRectangle(wx.Rect(wx.Point(posx,posy), wx.Size(self.getdist(),self.getdist())))
                         dc.SetTextForeground(wx.Colour(255,0,0))
                         dc.DrawText(str(decoded_extradata), wx.Point(posx+3,posy+5))
                    # SELECTION
               try:
                    if SELECTING_OBJS_OR_WARPS == "OBJ":
                         if self.isBrushing == True and TOOLS == "SELECTION":# and CURRENT_DRAW_TYPE_SELECT == "OBJECT":
                              #print(self.mouse_pos)
                              mousepossecy=abs(15-(int((self.mouse_pos[1])/(16*self.scale))))+int((self.yoffset/2))
                              mousepossecx=int((self.mouse_pos[0])/(16*self.scale))-(camoffset)
                              positionooo=encodepos(mousepossecx,mousepossecy)

                              #finding
                              self.updateOBJ_DF()
                              try:
                                   CURRENT_SELECTED_LEVEL_OBJ = list(OBJ_DF[OBJ_DF["pos"] == positionooo].to_dict('records'))[0]
                                   self.current_selected_level_obj_index=CURRENT_SELECTED_LEVEL_DATA["obj"].index(CURRENT_SELECTED_LEVEL_OBJ)
                              except IndexError:
                                   CURRENT_SELECTED_LEVEL_OBJ = None
                              try:
                                   TYPE=CURRENT_SELECTED_LEVEL_OBJ["type"]
                                   POS=CURRENT_SELECTED_LEVEL_OBJ["pos"]
                                   PARAMS=CURRENT_SELECTED_LEVEL_OBJ["param"]
                                   #print("Selected",CURRENT_SELECTED_LEVEL_OBJ)
                              except Exception as error:
                                   print(error,CURRENT_SELECTED_LEVEL_OBJ)
                    elif SELECTING_OBJS_OR_WARPS == "WARP":
                         if self.isBrushing == True and TOOLS == "SELECTION":
                              mouseposwapy=abs(15-(int((self.mouse_pos[1])/(16*self.scale))))+int((self.yoffset/2))
                              mouseposwapx=int((self.mouse_pos[0])/(16*self.scale))-(camoffset)
                              positionooxo=encodepos(mouseposwapx,mouseposwapy)

                              #finding
                              self.updateOBJ_DF()
                              try:
                                   CURRENT_SELECTED_LEVEL_WARP = list(WARP_DF[WARP_DF["pos"] == positionooxo].to_dict('records'))[0]
                                   self.current_selected_level_warp_index=CURRENT_SELECTED_LEVEL_DATA["warp"].index(CURRENT_SELECTED_LEVEL_WARP)
                              except IndexError:
                                   CURRENT_SELECTED_LEVEL_WARP = None
                              try:
                                   ID=CURRENT_SELECTED_LEVEL_WARP["id"]
                                   POSWARP=CURRENT_SELECTED_LEVEL_WARP["pos"]
                                   DATA=CURRENT_SELECTED_LEVEL_WARP["data"]
                                   #print("Selected",CURRENT_SELECTED_LEVEL_OBJ)
                              except Exception as error:
                                   print("Internal error",error,CURRENT_SELECTED_LEVEL_WARP)

               except Exception as error:
                    print("External error",error)

               playerposy= ((heightlevel-(decodepos(playerpos)[1]))*(16*self.scale))+int((self.yoffset/2)*(16*self.scale))-(16*self.scale)
               playerposx=(decodepos(playerpos)[0]*(16*self.scale))+(camoffset*(16*self.scale))
               setoffset=2

               #print(playerposx, playerposy)
                    
               dc.DrawBitmap(wx.Bitmap(self.gfx[1]), playerposx, playerposy, True)
                         #print("Error has occurred")
               #                                        DRAW OBJECTS
               for object_ in range(len(CURRENT_SELECTED_LEVEL_DATA["obj"])):
                    try:
                         whatobj=CURRENT_SELECTED_LEVEL_DATA["obj"][object_]["type"]
                         obget=self.objType[whatobj]
                         objx=((decodepos(CURRENT_SELECTED_LEVEL_DATA["obj"][object_]["pos"])[0])*(16*self.scale))+(camoffset*(16*self.scale))
                         objy=((heightlevel-decodepos(CURRENT_SELECTED_LEVEL_DATA["obj"][object_]["pos"])[1])*(16*self.scale))+int((self.yoffset/2)*(16*self.scale))
                         if not obget == "TEXT": 
                              subimage=self.objects[obget]
                              

                              dc.SetPen(wx.Pen(wx.Colour(0,255,0), width=2))
                              try:
                                   if CURRENT_SELECTED_LEVEL_OBJ == CURRENT_SELECTED_LEVEL_DATA["obj"][object_]:
                                        dc.SetBrush(wx.Brush(wx.Colour(128,0,0), wx.BRUSHSTYLE_TRANSPARENT))
                                   else:
                                        dc.SetBrush(wx.Brush(wx.Colour(0,128,0), wx.BRUSHSTYLE_TRANSPARENT))
                              except:
                                   dc.SetBrush(wx.Brush(wx.Colour(0,128,0), wx.BRUSHSTYLE_TRANSPARENT))
                              dc.DrawRoundedRectangle(wx.Rect(wx.Point(objx,objy),wx.Point(objx+self.getdist(),objy-self.getdist())),7.0)

                              dc.DrawBitmap(wx.Bitmap(self.objects[obget]), objx, objy-int(subimage.GetHeight()), True)
                         else:
                              dc.SetPen(wx.Pen(wx.Colour(0,255,0), width=2))
                              try:
                                   if CURRENT_SELECTED_LEVEL_OBJ == CURRENT_SELECTED_LEVEL_DATA["obj"][object_]:
                                        dc.SetBrush(wx.Brush(wx.Colour(128,0,0), wx.BRUSHSTYLE_TRANSPARENT))
                                   else:
                                        dc.SetBrush(wx.Brush(wx.Colour(0,128,0), wx.BRUSHSTYLE_TRANSPARENT))
                              except:
                                   dc.SetBrush(wx.Brush(wx.Colour(0,128,0), wx.BRUSHSTYLE_TRANSPARENT))
                              dc.DrawRoundedRectangle(wx.Rect(wx.Point(objx,objy),wx.Point(objx+self.getdist(),objy-self.getdist())),7.0)
                              perem=CURRENT_SELECTED_LEVEL_DATA["obj"][object_]["param"]
                    except:
                         pass

                         #print(error)
               for warp_ in range(len(CURRENT_SELECTED_LEVEL_DATA["warp"])):
                    warpid=CURRENT_SELECTED_LEVEL_DATA["warp"][warp_]["id"]
                    warppos=CURRENT_SELECTED_LEVEL_DATA["warp"][warp_]["pos"]
                    warpdata=CURRENT_SELECTED_LEVEL_DATA["warp"][warp_]["data"]
                    warpx=((decodepos(warppos)[0])*(16*self.scale))+(camoffset*(16*self.scale))
                    warpy=((heightlevel-decodepos(warppos)[1])*(16*self.scale))+int((self.yoffset/2)*(16*self.scale))
                    
                    dc.SetPen(wx.Pen(wx.Colour(255,255,255)))
                    if CURRENT_SELECTED_LEVEL_WARP == CURRENT_SELECTED_LEVEL_DATA["warp"][warp_]:
                         dc.SetBrush(wx.Brush(wx.Colour(128,128,128)))
                    else:
                         dc.SetBrush(wx.Brush(wx.Colour(0,128,128)))

                    dc.DrawRectangle(wx.Rect(wx.Point(warpx+setoffset,warpy-setoffset),wx.Point(warpx+self.getdist()-setoffset,warpy-self.getdist()+setoffset)))
                    dc.DrawText(str(warpid), wx.Point(warpx+4,warpy-19))
                    

               if TOOLS=="BRUSH":
                    dc.SetPen(wx.Pen(wx.Colour(255,255,255,128+(128*int(self.isBrushing)))))
                    dc.SetBrush(wx.Brush(wx.Colour(128,128,128,128+(128*int(self.isBrushing))),wx.BRUSHSTYLE_FDIAGONAL_HATCH))
                    dc.DrawRoundedRectangle(wx.Rect(*self.mouse_pos,16*self.brushSet.shape[1]*self.scale,16*self.brushSet.shape[0]*self.scale),5.0)

               if TOOLS=="PICKER":
                    dc.SetPen(wx.Pen(wx.Colour(128,255,255,128+(128*int(self.isBrushing)))))
                    dc.SetBrush(wx.Brush(wx.Colour(128,0,0,128+(128*int(self.isBrushing))),wx.BRUSHSTYLE_FIRST_HATCH))
                    dc.DrawRectangle(*self.mouse_pos,16*self.brushSet.shape[1]*self.scale,16*self.brushSet.shape[0]*self.scale)


               if TOOLS=="SELECTION":
                    dc.SetPen(wx.Pen(wx.Colour(255,255,255,128+(128*int(self.isBrushing)))))
                    dc.SetBrush(wx.Brush(wx.Colour(0,128,0,128+(128*int(self.isBrushing)))))
                    dc.DrawRectangle(wx.Rect(wx.Point(self.mouse_pos[0]+4,self.mouse_pos[1]+4), wx.Size(self.getdist()-8,self.getdist()-8)))
                    
               dc.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
               dc.SetTextForeground(wx.Colour(255,255,255))
               if (screenboundarie) >= widthlevel:
                    dc.DrawText("At first block " + str(-camoffset) + ", at last block " + str(widthlevel) + ", world size: " + str(widthlevel)+ "x"+str(heightlevel), 5, 5)
               else:
                    dc.DrawText("At first block " + str(-camoffset) + ", at last block " + str((screenboundarie)-camoffset)  + ", world size: " + str(widthlevel)+ "x"+str(heightlevel), 5, 5)

               self.old_mouse_pos=round(self.mx/(16*self.scale))*(16*self.scale),round(self.my/(16*self.scale))*(16*self.scale)
               self.old_selected_data=CURRENT_SELECTED_LEVEL_DATA
               #print(SELECTION_START, SELECTION_END)
          except Exception as error:
               pass
               #print("An error occurred:",error)               #(Exception)
               #raise error


          #self.Refresh(eraseBackground=False)
          #self.Update()
     def remove_duplicates(self,listTo):
          return list(dict.fromkeys(listTo))
     def getdist(self):
          return 16*self.scale
     def updateOBJ_DF(self):
          global OBJ_DF,WARP_DF,CURRENT_SELECTED_LEVEL_DATA
          OBJ_DF=pandas.DataFrame(CURRENT_SELECTED_LEVEL_DATA["obj"])
          WARP_DF=pandas.DataFrame(CURRENT_SELECTED_LEVEL_DATA["warp"])
     def shift(arr,num, axis=1):
          arr=np.roll(arr,num, axis)
          if axis==1:
               if num<0:
                    for x,y in itertools.product(range(len(arr)+num,len(arr)),range(arr.shape[0])):
                         arr[y,x]=30
               elif num > 0:
                    for x,y in itertools.product(range(num),range(arr.shape[0])):
                         arr[y,x]=30
          elif axis==0:
               if num<0:
                    for x,y in itertools.product(range(arr.shape[1]),range(len(arr)+num,len(arr))):
                         arr[y,x]=30
               elif num > 0:
                    for x,y in itertools.product(range(arr.shape[0]),range(num)):
                         arr[y,x]=30
          return arr
          
     def capture_mouse(self, event):
          global TOOLS
          global SELECTION_START, SELECTION_END
          
          self.mx,self.my=event.GetPosition()
          if self.isVert:
               self.rotation-=(event.GetWheelRotation()/12)
          elif not self.isVert:
               self.yoffset+=(event.GetWheelRotation()/12)
               
          if event.ButtonDown(wx.MOUSE_BTN_LEFT):
               self.isBrushing=True
               
          if event.ButtonUp(wx.MOUSE_BTN_LEFT):
               self.isBrushing=False
               self.updateOBJ_DF()
               
          if event.ButtonDown(wx.MOUSE_BTN_RIGHT):
               if TOOLS == "SELECTION":
                    SELECTION_END=[0,0]
                    SELECTION_START=[self.mouse_pos[0],self.mouse_pos[1]]
               self.isSelecting=True

          if event.ButtonUp(wx.MOUSE_BTN_RIGHT):
               self.isSelecting=False


          #self.Refresh(eraseBackground=False)
          self.SetFocus()
          #print(self.rotation)
          #print()
          #self.Refresh(eraseBackground=False)

          
     def OnKeyDown(self, event):
          global CURRENT_SELECTED_LEVEL_OBJ,CURRENT_SELECTED_LEVEL_WARP,CURRENT_SELECTED_LEVEL_DATA,SELECTING_OBJS_OR_WARPS
          #self.Refresh(eraseBackground=False)
          if int(event.GetKeyCode()) == 306: #Shift mothafuca
               self.isVert= True
          if SELECTING_OBJS_OR_WARPS == "OBJ":
               if int(event.GetKeyCode()) == 127 and CURRENT_SELECTED_LEVEL_OBJ!=None:
                    CURRENT_SELECTED_LEVEL_OBJ=None
                    del CURRENT_SELECTED_LEVEL_DATA["obj"][self.current_selected_level_obj_index]
                    self.updateOBJ_DF()
          elif SELECTING_OBJS_OR_WARPS == "WARP":
               if int(event.GetKeyCode()) == 127 and CURRENT_SELECTED_LEVEL_WARP!=None:
                    CURRENT_SELECTED_LEVEL_WARP=None
                    del CURRENT_SELECTED_LEVEL_DATA["warp"][self.current_selected_level_warp_index]
                    self.updateOBJ_DF()
          if int(event.GetKeyCode()) == 87: # W
               if SELECTING_OBJS_OR_WARPS == "OBJ" and CURRENT_SELECTED_LEVEL_OBJ!=None:
                    self.movethings(0,1,"OBJ")
               if SELECTING_OBJS_OR_WARPS == "WARP" and CURRENT_SELECTED_LEVEL_WARP!=None:
                    self.movethings(0,1,"WARP")
          if int(event.GetKeyCode()) == 83: # S
               if SELECTING_OBJS_OR_WARPS == "OBJ" and CURRENT_SELECTED_LEVEL_OBJ!=None:
                    self.movethings(0,-1,"OBJ")
               if SELECTING_OBJS_OR_WARPS == "WARP" and CURRENT_SELECTED_LEVEL_WARP!=None:
                    self.movethings(0,-1,"WARP")
          if int(event.GetKeyCode()) == 65: # A
               if SELECTING_OBJS_OR_WARPS == "OBJ" and CURRENT_SELECTED_LEVEL_OBJ!=None:
                    self.movethings(-1,0,"OBJ")
               if SELECTING_OBJS_OR_WARPS == "WARP" and CURRENT_SELECTED_LEVEL_WARP!=None:
                    self.movethings(-1,0,"WARP")
          if int(event.GetKeyCode()) == 68: # D
               if SELECTING_OBJS_OR_WARPS == "OBJ" and CURRENT_SELECTED_LEVEL_OBJ!=None:
                    self.movethings(1,0,"OBJ")
               if SELECTING_OBJS_OR_WARPS == "WARP" and CURRENT_SELECTED_LEVEL_WARP!=None:
                    self.movethings(1,0,"WARP")
     def OnKeyUp(self, event):
          if int(event.GetKeyCode()) == 306: #Shift mothafuca
               self.isVert= False
          #print(event.GetKeyCode())
     def movethings(self, x, y, what):
          global CURRENT_SELECTED_LEVEL_DATA,CURRENT_SELECTED_LEVEL_OBJ,CURRENT_SELECTED_LEVEL_WARP
          if what=="OBJ":
               CURRENT_SELECTED_LEVEL_DATA["obj"][self.current_selected_level_obj_index]["pos"]=encodepos(decodepos(CURRENT_SELECTED_LEVEL_DATA["obj"][self.current_selected_level_obj_index]["pos"])[0]+x,
                                                                                                          decodepos(CURRENT_SELECTED_LEVEL_DATA["obj"][self.current_selected_level_obj_index]["pos"])[1]+y)
               CURRENT_SELECTED_LEVEL_OBJ["pos"]=CURRENT_SELECTED_LEVEL_DATA["obj"][self.current_selected_level_obj_index]["pos"]
               self.updateOBJ_DF()
          elif what=="WARP":
               CURRENT_SELECTED_LEVEL_DATA["warp"][self.current_selected_level_warp_index]["pos"]=encodepos(decodepos(CURRENT_SELECTED_LEVEL_DATA["warp"][self.current_selected_level_warp_index]["pos"])[0]+x,
                                                                                                          decodepos(CURRENT_SELECTED_LEVEL_DATA["warp"][self.current_selected_level_warp_index]["pos"])[1]+y)
               CURRENT_SELECTED_LEVEL_WARP["pos"]=CURRENT_SELECTED_LEVEL_DATA["warp"][self.current_selected_level_warp_index]["pos"]
               self.updateOBJ_DF()
     def create_obj(self, image):
          obj_list={}
          obj_list["GOOMBA"]= image.GetSubImage(wx.Rect(32*self.scale, 0*self.scale, 16*self.scale, 16*self.scale))
          obj_list["KOOPA"]= image.GetSubImage(wx.Rect(16*self.scale, 0*self.scale, 16*self.scale, 32*self.scale))
          obj_list["KOOPA TROOPA"]= image.GetSubImage(wx.Rect(0*self.scale, 0*self.scale, 16*self.scale, 32*self.scale))
          obj_list["FLYING FISH"]= image.GetSubImage(wx.Rect(32*self.scale, 16*self.scale, 16*self.scale, 16*self.scale))
          obj_list["UNSPELLABLE PLANT"]= image.GetSubImage(wx.Rect(0*self.scale, 32*self.scale, 16*self.scale, 32*self.scale))
          obj_list["HAMMER BRO"]= image.GetSubImage(wx.Rect(16*self.scale, 32*self.scale, 16*self.scale, 32*self.scale))
          obj_list["BOWSER"]= image.GetSubImage(wx.Rect(48*self.scale, 0*self.scale, 32*self.scale, 32*self.scale))
          obj_list["PLATFORM"]= image.GetSubImage(wx.Rect(48*self.scale, 48*self.scale, 16*self.scale, 16*self.scale))
          obj_list["BUS PLATFORM"]= image.GetSubImage(wx.Rect(48*self.scale, 48*self.scale, 16*self.scale, 16*self.scale))
          obj_list["SPRING"]= image.GetSubImage(wx.Rect(64*self.scale, 32*self.scale, 16*self.scale, 32*self.scale))
          obj_list["FLAG"]= image.GetSubImage(wx.Rect(48*self.scale, 32*self.scale, 16*self.scale, 16*self.scale))
          obj_list["FIRE TRAP"]= image.GetSubImage(wx.Rect(80*self.scale, 32*self.scale, 16*self.scale, 16*self.scale))
          obj_list["FIRE BLAST"]= image.GetSubImage(wx.Rect(32*self.scale, 48*self.scale, 16*self.scale, 16*self.scale))
          obj_list["LAUNCHER"]= image.GetSubImage(wx.Rect(32*self.scale, 32*self.scale, 16*self.scale, 16*self.scale))
          obj_list["MUSHROOM"]= image.GetSubImage(wx.Rect(16*self.scale, 64*self.scale, 16*self.scale, 16*self.scale))
          obj_list["FIRE FLOWER"]= image.GetSubImage(wx.Rect(64*self.scale, 64*self.scale, 16*self.scale, 16*self.scale))
          obj_list["ONEUP"]= image.GetSubImage(wx.Rect(0*self.scale, 64*self.scale, 16*self.scale, 16*self.scale))
          obj_list["STAR"]= image.GetSubImage(wx.Rect(48*self.scale, 64*self.scale, 16*self.scale, 16*self.scale))
          obj_list["GOLD FLOWER"]= image.GetSubImage(wx.Rect(80*self.scale, 64*self.scale, 16*self.scale, 16*self.scale))
          obj_list["POISON MUSHROOM"]= image.GetSubImage(wx.Rect(32*self.scale, 64*self.scale, 16*self.scale, 16*self.scale))
          obj_list["COIN"]= image.GetSubImage(wx.Rect(80*self.scale, 48*self.scale, 16*self.scale, 16*self.scale))
          obj_list["AXE"]= image.GetSubImage(wx.Rect(80*self.scale, 0*self.scale, 16*self.scale, 16*self.scale))
          
          

          return obj_list
          

class TestPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(5,5), size=wx.Size(window.Size[0]-16,window.Size[1]-106))
          self.SetBackgroundColour("LIGHT GRAY")
          

##          font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
##          font2 = wx.Font(12, wx.TELETYPE, wx.NORMAL, wx.NORMAL)
##          text1=wx.StaticText(self, label="404: Code not found", pos=wx.Point(5,5))
##          text1.SetFont(font)
##          text2=wx.StaticText(self, label="Seems like the developer was hit by laziness...", pos=wx.Point(5,35))
##          text2.SetFont(font2)



class ItemPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel,pos=wx.Point((24*27)+10,30), size=wx.Size(327,(24*16)))
          self.SetBackgroundColour('LIGHT GRAY')
          self.tree=wx.TreeCtrl(self, id=wx.NewId(), pos=wx.Point(0,0), size=wx.Size(327,125))

          self.tilepresetspanel=tile_presets_panel(self, window)
          
          self.levels=[]
          self.zones=[]
          
     def UpdateData(self):
          global WORLD_DATA,CURRENT_SELECTED_LEVEL_DATA
          self.levels.clear()
          self.zones.clear()
          self.tree.DeleteAllItems()
          self.World=self.tree.AddRoot("World")

          for levels in range(len(WORLD_DATA)):
               self.levels.append(self.tree.AppendItem(self.World, "Level "+str(WORLD_DATA[levels]["id"])))
               for zones in range(len(WORLD_DATA[levels]["zones"])):
                    self.zones.append(self.tree.AppendItem(self.levels[levels], "Zone "+str(WORLD_DATA[levels]["zones"][zones]["id_zone"])))
          self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.ChangeZone)
     def ChangeZone(self, event=None):
          global WORLD_DATA,CURRENT_SELECTED_LEVEL_DATA,window,CURRENT_SELECTED_LEVEL
          item=str(self.tree.GetItemText(event.GetItem()))
          parent=str(self.tree.GetItemText(self.tree.GetItemParent(event.GetItem())))
          print(item,parent,int(parent[6:]),int(item[5:]))
          if item.startswith("Zone") and parent.startswith("Level"):
               #print(WORLD_DATA[int(parent[6:])]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])])
               UpdateData()
               CURRENT_SELECTED_LEVEL=int(parent[6:])
               #print(WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])])
               CURRENT_SELECTED_LEVEL_DATA={"id_zone":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["id_zone"],
                                            "id_level":WORLD_DATA[int(parent[6:])]["id"],
                                            "playerpos":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["playerpos"],
                                            "color":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["color"],
                                            "music":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["music"],
                                            "data":numpy.array(WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["data"], dtype=numpy.int64),
                                            "obj":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["obj"],
                                            "warp":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["warp"]}
          window.PANELS.entryPanel.zonePanel.setValues()
          window.PANELS.entryPanel.levelPanel.setValues()
               

class tile_presets_panel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(5,130), size=wx.Size(317,250))
          self.SetBackgroundColour("GRAY")
          
          self.Scrollbetweensprites = wx.ScrollBar(self, pos=wx.Point(297,0), size=wx.Size(20,250), style=wx.SB_VERTICAL)
          self.Scrollbetweensprites.SetScrollbar(0,1,6,1)
          self.Scrollbetweensprites.Bind(wx.EVT_SCROLL, self.scrollPreset)

          self.DrawPresets=wx.CheckBox(self, label="Draw Presets", pos=wx.Point(5,5))
          self.DrawPresets.Bind(wx.EVT_CHECKBOX, self.drawingpresetsornot)

          self.tilepreset1=tile_presets_1(self, window)
          self.tilepreset2=tile_presets_2(self, window)
          self.tilepreset3=tile_presets_3(self, window)
          self.tilepreset4=tile_presets_4(self, window)
          self.tilepreset5=tile_presets_5(self, window)
          self.tilepreset6=tile_presets_6(self, window)
          self.scrollPreset()
     def drawingpresetsornot(self, event):
          global IS_DRAWING_PRESETS
          IS_DRAWING_PRESETS = not IS_DRAWING_PRESETS
          print(IS_DRAWING_PRESETS)
     def scrollPreset(self, event=None):
          if event==None:
               self.tilepreset1.Show(True)
               self.tilepreset2.Show(False)
               self.tilepreset3.Show(False)
               self.tilepreset4.Show(False)
               self.tilepreset5.Show(False)
               self.tilepreset6.Show(False)
               return
          num=event.GetPosition()
          if num==0:
               self.tilepreset1.Show(True)
               self.tilepreset2.Show(False)
               self.tilepreset3.Show(False)
               self.tilepreset4.Show(False)
               self.tilepreset5.Show(False)
               self.tilepreset6.Show(False)
          if num==1:
               self.tilepreset1.Show(False)
               self.tilepreset2.Show(True)
               self.tilepreset3.Show(False)
               self.tilepreset4.Show(False)
               self.tilepreset5.Show(False)
               self.tilepreset6.Show(False)
          if num==2:
               self.tilepreset1.Show(False)
               self.tilepreset2.Show(False)
               self.tilepreset3.Show(True)
               self.tilepreset4.Show(False)
               self.tilepreset5.Show(False)
               self.tilepreset6.Show(False)
          if num==3:
               self.tilepreset1.Show(False)
               self.tilepreset2.Show(False)
               self.tilepreset3.Show(False)
               self.tilepreset4.Show(True)
               self.tilepreset5.Show(False)
               self.tilepreset6.Show(False)
          if num==4:
               self.tilepreset1.Show(False)
               self.tilepreset2.Show(False)
               self.tilepreset3.Show(False)
               self.tilepreset4.Show(False)
               self.tilepreset5.Show(True)
               self.tilepreset6.Show(False)
          if num==5:
               self.tilepreset1.Show(False)
               self.tilepreset2.Show(False)
               self.tilepreset3.Show(False)
               self.tilepreset4.Show(False)
               self.tilepreset5.Show(False)
               self.tilepreset6.Show(True)
          
          


class tile_presets_1(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(317,365))
          self.SetBackgroundColour(wx.Colour(*hextorgb("9D4900")))

          text=wx.StaticText(self, label="Theme: Overworld", pos=wx.Point(5,5))

          self.ButtonBush=wx.Button(self, label="Bush", pos=wx.Point(5, 20), size=wx.Size(40,20))
          self.ButtonBush.Bind(wx.EVT_BUTTON, self.bush)
          self.ButtonHill=wx.Button(self, label="Hill", pos=wx.Point(5, 40),size=wx.Size(40,20))
          self.ButtonHill.Bind(wx.EVT_BUTTON, self.hill)
          self.ButtonCloud=wx.Button(self, label="Cloud", pos=wx.Point(50, 20),size=wx.Size(45,20))
          self.ButtonCloud.Bind(wx.EVT_BUTTON, self.cloud)
          self.ButtonTree=wx.Button(self, label="Tree", pos=wx.Point(5, 80),size=wx.Size(40,20))
          self.ButtonTree.Bind(wx.EVT_BUTTON, self.tree)
          self.ButtonPipe=wx.Button(self, label="Pipe", pos=wx.Point(5, 60),size=wx.Size(40,20))
          self.ButtonPipe.Bind(wx.EVT_BUTTON, self.pipe)
          self.ButtonFlagpole=wx.Button(self, label="Flagpole", pos=wx.Point(5,160),size=wx.Size(65,20))
          self.ButtonFlagpole.Bind(wx.EVT_BUTTON, self.flagpole)
          self.ButtonWater=wx.Button(self, label="Water", pos=wx.Point(50,40),size=wx.Size(45,20))
          self.ButtonWater.Bind(wx.EVT_BUTTON, self.water)

          
     def bush(self, event):
          global TILE_PRESET
          TILE_PRESET=random.choice([[[374,375,376]],
                                    [[374,375,375,376]],
                                    [[374,375,375,375,376]]])
     def hill(self, event):
          global TILE_PRESET
          TILE_PRESET=[[30,339,30],
                       [338,random.choice([371,372,373]),340]]
     def cloud(self, event):
          global TILE_PRESET
          TILE_PRESET=random.choice([[[726,727,728],[759,760,761]],
                                    [[726,727,727,728],[759,760,760,761]],
                                    [[726,727,727,727,728],[759,760,760,760,761]]])

     def tree(self, event):
          global TILE_PRESET
          TILE_PRESET=random.choice([[[343],[40]],
                                    [[344],[377],[40]]])
     def pipe(self, event):
          global TILE_PRESET
          TILE_PRESET=[[98634,98635],
                       [98667,98668]]
     def flagpole(self, event):
          global TILE_PRESET
          TILE_PRESET=[[10486106],
                       [10486139],
                       [10486139],
                       [10486139],
                       [10486139],
                       [10486139],
                       [10486139],
                       [10486139],
                       [10486139],
                       [10486139],
                       [65569]]
     def water(self, event):
          global TILE_PRESET
          TILE_PRESET=[[861],[894]]
class tile_presets_2(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(317,365))
          self.SetBackgroundColour(wx.Colour(*hextorgb("217C8C")))

          text=wx.StaticText(self, label="Theme: Underground", pos=wx.Point(5,5))
class tile_presets_3(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(317,365))
          self.SetBackgroundColour(wx.Colour(*hextorgb("FFFFFF")))
          text=wx.StaticText(self, label="Theme: Snow / Castle", pos=wx.Point(5,5))
class tile_presets_4(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(317,365))
          self.SetBackgroundColour(wx.Colour(*hextorgb("1F9800")))
          text=wx.StaticText(self, label="Theme: Underwater", pos=wx.Point(5,5))
class tile_presets_5(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(317,365))
          self.SetBackgroundColour(wx.Colour(*hextorgb("C19900")))
          text=wx.StaticText(self, label="Theme: Desert", pos=wx.Point(5,5))
class tile_presets_6(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(317,365))
          self.SetBackgroundColour(wx.Colour(*hextorgb("90E0E8")))
          text=wx.StaticText(self, label="Theme: Ice", pos=wx.Point(5,5))




class tilePanel(wx.Panel):
     
     def __init__(self, panel, window):
          
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(window.Size[0],200))
          self.SetBackgroundColour("LIGHT GRAY")
          self.tiledatalabel=wx.StaticText(self, pos=wx.Point(5,5), label="Tile data (integer)")
          self.tiledata=wx.TextCtrl(self, id=wx.NewId(), value="0", pos=wx.Point(5,25), size=wx.Size(135,20), style=wx.TE_READONLY)
          
          self.tiletypelabel=wx.StaticText(self, pos=wx.Point(150,5), label="Tile type (string)")
          self.tiletype=wx.TextCtrl(self, id=wx.NewId(), value="", pos=wx.Point(150,25), size=wx.Size(135,20), style=wx.TE_READONLY)

          self.spriteindexlabel=wx.StaticText(self, pos=wx.Point(5,55), label="Sprite index (integer)")
          self.spriteindex=wx.TextCtrl(self, id=wx.NewId(), value="0", pos=wx.Point(5,75), size=wx.Size(135,20), style= wx.TE_PROCESS_ENTER)
          self.spriteindex.Bind(wx.EVT_KEY_DOWN, self.spriteindexChange)

          #self.depthlabel=wx.StaticText(self, pos=wx.Point(165,55), label="Depth (0-1)")
          self.depth=wx.CheckBox(self, id=wx.NewId(), label="Layer", pos=wx.Point(165,75), size=wx.Size(100,20), style = wx.CHK_2STATE)
          self.depth.Bind(wx.EVT_CHECKBOX, self.depthChange)

          self.choices={"AIR":0,
                        "SOLID STANDARD":1,
                        "SOLID BUMPABLE":2,
                        "SOLID BREAKABLE NORMAL":3,
                        "ITEM BLOCK STANDARD":17,
                        "COIN BLOCK STANDARD":18,
                        "COIN BLOCK MULTI":19,
                        "ITEM BLOCK INVISIBLE":21,
                        "COIN BLOCK INVISIBLE":22,
                        "VINE BLOCK":24,
                        "WARP TILE":81,
                        "WARP PIPE SLOW":82,
                        "WARP PIPE RIGHT SLOW":83,
                        "WARP PIPE FAST":84,
                        "WARP PIPE RIGHT FAST":85,
                        "LEVEL END WARP":86,
                        "FLAGPOLE":160}

          self.tile_deflabel=wx.StaticText(self, pos=wx.Point(285,55), label="Tile definition (wot? ez)")
          self.tile_def=wx.ComboBox(self, id=wx.NewId(), style=wx.CB_READONLY, pos=wx.Point(285,75), size=wx.Size(180,20), choices=["AIR",
                                                                   "SOLID STANDARD",
                                                                   "SOLID BUMPABLE",
                                                                   "SOLID BREAKABLE NORMAL",
                                                                   "ITEM BLOCK STANDARD",
                                                                   "COIN BLOCK STANDARD",
                                                                   "COIN BLOCK MULTI",
                                                                   "ITEM BLOCK INVISIBLE",
                                                                   "COIN BLOCK INVISIBLE",
                                                                   "VINE BLOCK",
                                                                   "WARP TILE",
                                                                   "WARP PIPE SLOW",
                                                                   "WARP PIPE RIGHT SLOW",
                                                                   "WARP PIPE FAST",
                                                                   "WARP PIPE RIGHT FAST",
                                                                   "LEVEL END WARP",
                                                                   "FLAGPOLE"], value="AIR")
          self.tile_def.Bind(wx.EVT_COMBOBOX, self.tile_defChange)

          self.extra_datalabel=wx.StaticText(self, pos=wx.Point(475,55), label="Extra data (integer)")
          self.extra_data=wx.TextCtrl(self, id=wx.NewId(), value="0", pos=wx.Point(475,75), size=wx.Size(135,20), style= wx.TE_PROCESS_ENTER)
          self.extra_data.Bind(wx.EVT_KEY_DOWN, self.extra_dataChange)

          self.Bind(wx.EVT_IDLE, self.UpdateAll)

          self.preview = preview_panel(self, window)
                                                                   

     def UpdateAll(self, event):
          global TOOLS,SELECTING_TILES_FROM_SELECTOR
          if TOOLS=="PICKER":
               self.spriteindex.SetValue(str(SPRITE_INDEX))
               self.depth.SetValue(bool(DEPTH))
               for key, value in self.choices.items():
                    if value == TILE_DEF:
                         self.tile_def.SetValue(str(key))
               self.extra_data.SetValue(str(EXTRA_DATA))
               self.tiledata.SetValue(str(encode(SPRITE_INDEX, DEPTH, EXTRA_DATA, TILE_DEF)))
          if SELECTING_TILES_FROM_SELECTOR:
               self.spriteindex.SetValue(str(SPRITE_INDEX))
               self.tiledata.SetValue(str(encode(SPRITE_INDEX, DEPTH, EXTRA_DATA, TILE_DEF)))
     
     def spriteindexChange(self, event=None):
          global SPRITE_INDEX,DEPTH,TILE_DEF,EXTRA_DATA,IS_CLONING
          IS_CLONING=False
          if not event == None:
               if not event.GetKeyCode() == wx.WXK_RETURN:
                    event.Skip()
                    return 0
               else:
                    if str(self.spriteindex.GetValue()).isnumeric():
                         if int(self.spriteindex.GetValue()) <= 1253:
                              SPRITE_INDEX = int(self.spriteindex.GetValue())
                              self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))
          else:
               SPRITE_INDEX = int(self.spriteindex.GetValue())
               self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))
     def depthChange(self, event=None):
          IS_CLONING=False
          global SPRITE_INDEX,DEPTH,TILE_DEF,EXTRA_DATA

          DEPTH = int(bool(self.depth.GetValue()))
          self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))
     def tile_defChange(self, event=None):
          IS_CLONING=False
          global SPRITE_INDEX,DEPTH,TILE_DEF,EXTRA_DATA
          sel_value=self.tile_def.GetValue()

          TILE_DEF=self.choices[str(sel_value)]
          
          self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))
     def extra_dataChange(self, event=None):
          IS_CLONING=False
          global SPRITE_INDEX,DEPTH,TILE_DEF,EXTRA_DATA
          if not event == None:
               if not event.GetKeyCode() == wx.WXK_RETURN:
                    event.Skip()
                    return 0
               else:
                    if str(self.extra_data.GetValue()).isnumeric():
                         EXTRA_DATA = int(self.extra_data.GetValue())
                         self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))
          else:
               EXTRA_DATA = int(self.extra_data.GetValue())
               self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))

class preview_panel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(775,5), size=wx.Size(200,125))
          self.SetBackgroundColour("GRAY")

          self.scale=4
          self.imSize=(8*self.scale,8*self.scale)
          
          self.fileimage=wx.Image("sources\\smb_map.png", type=wx.BITMAP_TYPE_PNG)
          self.spritesheet=self.Rescale(self.fileimage)
          self.images=create_sprites(self.spritesheet, self.scale) 

          fileimagetwo=wx.Image("sources\\powerups.png", type=wx.BITMAP_TYPE_PNG)
          rescalepows=self.Rescale(fileimagetwo)
          self.powerups=create_powerups(rescalepows, self.scale)

          giefex = wx.Image("sources\\barrier.png", type=wx.BITMAP_TYPE_PNG)
          rescalegfx = self.Rescale(giefex)
          self.gfx=create_gfx(rescalegfx, self.scale)

          self.usualpos=int((self.Size[0]/2)-self.imSize[0])-16,int((self.Size[1]/2)-self.imSize[1])
          self.bump_offset=0

          self.Bind(wx.EVT_PAINT, self.OnPainting)
          self.Bind(wx.EVT_IDLE, self.Refreshing)

     def Refreshing(self, event):
          self.Refresh(eraseBackground=False)

     def Rescale(self, image):
          imagewo = image.Scale(image.GetWidth()*self.scale, image.GetHeight()*self.scale, wx.IMAGE_QUALITY_NEAREST)
          return imagewo
     def OnPainting(self, event):
          dc = wx.BufferedPaintDC(self)
          dc.SetBackground(wx.Brush(wx.Colour(100,100,100)))
          dc.Clear()

          fnucit={"invisible item block":lambda: dc.DrawBitmap(wx.Bitmap(self.powerups[5]), self.usualpos[0], self.usualpos[1], True),
                  "vine block":lambda: dc.DrawBitmap(wx.Bitmap(self.powerups[6]), self.usualpos[0], self.usualpos[1], True),
                  "mushroom":lambda: dc.DrawBitmap(wx.Bitmap(self.powerups[0]), self.usualpos[0], self.usualpos[1], True),
                  "fire flower":lambda: dc.DrawBitmap(wx.Bitmap(self.powerups[1]), self.usualpos[0], self.usualpos[1], True),
                  "star":lambda: dc.DrawBitmap(wx.Bitmap(self.powerups[2]), self.usualpos[0], self.usualpos[1], True),
                  "oneup":lambda: dc.DrawBitmap(wx.Bitmap(self.powerups[3]), self.usualpos[0], self.usualpos[1], True),
                  "poison mushroom":lambda: dc.DrawBitmap(wx.Bitmap(self.powerups[4]), self.usualpos[0], self.usualpos[1], True),
                  "barrier":lambda: dc.DrawBitmap(wx.Bitmap(self.gfx[0]), self.usualpos[0], self.usualpos[1], True)
                  }
          self.doBumps()
          if DEPTH == 0:
               if TILE_DEF == 2 or TILE_DEF == 19:
                    dc.DrawBitmap(wx.Bitmap(self.images[SPRITE_INDEX]), self.usualpos[0],self.usualpos[1]-(abs(math.sin(self.bump_offset)*10)),True)
               else:
                    dc.DrawBitmap(wx.Bitmap(self.images[SPRITE_INDEX]), self.usualpos[0],self.usualpos[1],True)
               self.filterSpecial(fnucit)
               dc.DrawBitmap(wx.Bitmap(self.gfx[2]), int((self.Size[0]/2)-self.imSize[0])+16,int((self.Size[1]/2)-self.imSize[1]),True)
          elif DEPTH == 1:
               dc.DrawBitmap(wx.Bitmap(self.gfx[2]), int((self.Size[0]/2)-self.imSize[0])+16,int((self.Size[1]/2)-self.imSize[1]),True)
               if TILE_DEF == 2 or TILE_DEF == 19:
                    dc.DrawBitmap(wx.Bitmap(self.images[SPRITE_INDEX]), self.usualpos[0],self.usualpos[1]-(abs(math.sin(self.bump_offset)*10)),True)
               else:
                    dc.DrawBitmap(wx.Bitmap(self.images[SPRITE_INDEX]), self.usualpos[0],self.usualpos[1],True)
               self.filterSpecial(fnucit)

     def doBumps(self):
          self.bump_offset+=0.07
     def filterSpecial(self,functions):
          if TILE_DEF == 21 or TILE_DEF == 22:
               functions["invisible item block"]()
          #Vine block
          if TILE_DEF == 24:
               functions["vine block"]()

          if TILE_DEF == 17 or TILE_DEF == 21:
               if EXTRA_DATA == 81:
                    functions["mushroom"]()
               if EXTRA_DATA == 82:
                    functions["fire flower"]()
               if EXTRA_DATA == 83:
                    functions["star"]()
               if EXTRA_DATA == 84:
                    functions["oneup"]()
               if EXTRA_DATA == 86:
                    functions["poison mushroom"]()
          if SPRITE_INDEX == 30 and (TILE_DEF == 1 or TILE_DEF == 2):
               functions["barrier"]()

class objectPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(window.Size[0],200))
          self.SetBackgroundColour("LIGHT GRAY")
          self.objTypeselect={"GOOMBA":17,
                        "KOOPA":18,
                        "KOOPA TROOPA":19,
                        "FLYING FISH":21,
                        "UNSPELLABLE PLANT":22,
                        "HAMMER BRO":49,
                        "BOWSER":25,
                        "PLATFORM":145,
                        "BUS PLATFORM":146,
                        "SPRING":149,
                        "FLAG":177,
                        "FIRE TRAP":33,
                        "FIRE BLAST":34,
                        "LAUNCHER":35,
                        "MUSHROOM":81,
                        "FIRE FLOWER":82,
                        "ONEUP":83,
                        "STAR":84,
                        "GOLD FLOWER":100,
                        "COIN":97,
                        "AXE":85,
                        "POISON MUSHROOM":86,
                        "TEXT":253}
          self.objTextSelect={"GOOMBA":"[color]\ncolor: 0 for light goomba, 1 for dark goomba.",
                        "KOOPA":"[fly,color]\nfly: to make a koopa fly, set the fly value to 1.\ncolor: 0 for light koopa, 1 for dark koopa.",
                        "KOOPA TROOPA":"[fly,color]\nfly: to make a koopa troopa fly, set the fly value to 1.\ncolor: 0 for light koopa troopa, 1 for dark koopa troopa.",
                        "FLYING FISH":"[delay,impulse]\ndelay: how much the fish should wait before jump again.\nimpulse: with how much force the fish should jump.",
                        "UNSPELLABLE PLANT":"[color]\ncolor: 0 for light plant, 1 for dark plant.",
                        "HAMMER BRO":"[reverse]\nreverse: set it to 1 to make him move backwards.",
                        "BOWSER":"[]\nNo parameters. :D",
                        "PLATFORM":"oh shit...\n[width,movx,movy,speed,loop,delay,reverse]\nwidth: width of the platform, positive int.\nmovx: how far to move horizontally, float\nmovy: how far to move vertically, float\nspeed: speed, float\nloop: if set to 1 it will go back and forth\ndelay: initial delay of platform. (see elevators)\nreverse: if set to 1 will start at end point (see elevators)",
                        "BUS PLATFORM":"[width,movx,movy,speed]\nwidth: width of the platform, positive int.\nmovx: how far to move horizontally, float\nmovy: how far to move vertically, float\nspeed: speed, float",
                        "SPRING":"[]\nNo parameters. :D",
                        "FLAG":"[]\nNo parameters. Always place these on top of the flagpole. :P",
                        "FIRE TRAP":"[start,size]\nstart: 0 or 1, offsets a bit.\nsize: how big the fire trap should be. default is 6. positive int.",
                        "FIRE BLAST":"[delay,impulse]\ndelay: how much the blast should wait before jump again.\nimpulse: with how much force the blast should jump.",
                        "LAUNCHER":"[delay]\ndelay: how much the launcher should wait before shoot again. positive int.",
                        "MUSHROOM":"[]\nNO PARAMETERS. >:(",
                        "FIRE FLOWER":"[]\nNO PARAMETERS. >:(",
                        "ONEUP":"[]\nNO PARAMETERS. >:(",
                        "STAR":"[]\nNO PARAMETERS. >:(",
                        "GOLD FLOWER":"[]\nNO PARAMETERS. >:(",
                        "COIN":"[]\nNo parameters. :D",
                        "AXE":"[]\nNo parameters. :D",
                        "POISON MUSHROOM":"[]\nNO PARAMETERS. >:(",
                        "TEXT":"[offset,size,color,text]\noffset: vertical offset for the text, float\nsize: keep in mind that 1.0 is the size of 1 tile. float\ncolor: html color code, #FFFFFF for white\ntext: the text, string"}
          self.objtypelabel=wx.StaticText(self, pos=wx.Point(5,5), label="Object type (too ez)")
          self.objtypedesc=wx.StaticText(self, pos=wx.Point(200,5), label=str(self.objTextSelect["COIN"]))
          self.objtype=wx.ComboBox(self, id=wx.NewId(), style=wx.CB_READONLY, pos=wx.Point(5,25), size=wx.Size(180,20), choices=["GOOMBA",
                                                         "KOOPA",
                                                         "KOOPA TROOPA",
                                                         "FLYING FISH",
                                                         "UNSPELLABLE PLANT",
                                                         "HAMMER BRO",
                                                         "BOWSER",
                                                         "PLATFORM",
                                                         "BUS PLATFORM",
                                                         "SPRING",
                                                         "FLAG",
                                                         "FIRE TRAP",
                                                         "FIRE BLAST",
                                                         "LAUNCHER",
                                                         "MUSHROOM",
                                                         "FIRE FLOWER",
                                                         "ONEUP",
                                                         "STAR",
                                                         "GOLD FLOWER",
                                                         "COIN",
                                                         "AXE",
                                                         "POISON MUSHROOM",
                                                         "TEXT"], value="COIN")
          self.objtype.Bind(wx.EVT_COMBOBOX, self.changeObjType)
          self.parameters=wx.TextCtrl(self, id=wx.NewId(), value="0", pos=wx.Point(5,75), size=wx.Size(180,20), style= wx.TE_PROCESS_ENTER)
          self.parameters.Bind(wx.EVT_KEY_DOWN, self.changeParams)

          self.Bind(wx.EVT_IDLE, self.UpdateAll)
          

     def UpdateAll(self, event=None):
          global TOOLS
          if TOOLS=="SELECTION":
               global TYPE,POS,PARAMS
               for key, value in self.objTypeselect.items():
                    if value == TYPE:
                         self.objtype.SetValue(str(key))
               if TYPE != 253:
                    self.parameters.SetValue(str(str(str(PARAMS)[1:-1]).replace("'","")).replace(" ",""))
               else:
                    self.parameters.SetValue(str(PARAMS)[1:-1])
               self.objtypedesc.SetLabel(self.objTextSelect[str(self.objtype.GetValue())])
     def changeObjType(self, event=None):
          global TYPE,POS,PARAMS
          sel_value=self.objtype.GetValue()
          TYPE=self.objTypeselect[str(sel_value)]
          self.objtypedesc.SetLabel(self.objTextSelect[str(sel_value)])
     def changeParams(self, event=None):
          global TYPE,POS,PARAMS
          if not event == None:
               if not event.GetKeyCode() == wx.WXK_RETURN:
                    event.Skip()
                    return 0
               else:
                    if TOOLS!="SELECTION":
                         if "," in str(self.parameters.GetValue()):
                              paramfix=str(self.parameters.GetValue()).replace(', ',",")
                              paramsplit=str(self.parameters.GetValue()).split(",")
                              print(paramsplit)
                              for i in range(len(paramsplit)):
                                   paramsplit[i] = paramsplit[i]
                              PARAMS = paramsplit
                         else:
                              PARAMS = [str(self.parameters.GetValue()).replace('"',"")]
                         print(PARAMS)

          else:
               PARAMS = [str(self.parameters.GetValue())]

class warpPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(window.Size[0],200))
          self.SetBackgroundColour("LIGHT GRAY")

          self.dataselect={"NORMAL":0,
                           "UP":1,
                           "DOWN":2,
                           "LEFT":3,
                           "RIGHT":4}
          
          self.IDLabel=wx.StaticText(self, label="id (integer)", pos=(5,5))
          self.ID__=wx.TextCtrl(self, id=wx.NewId(), value="0", pos=wx.Point(5,25), size=wx.Size(135,20), style= wx.TE_PROCESS_ENTER)
          self.ID__.Bind(wx.EVT_KEY_DOWN, self.idChange)
          self.dataLabel=wx.StaticText(self, label="type (woah, too ez already)", pos=(5,55))
          self.data=wx.ComboBox(self, id=wx.NewId(), style=wx.CB_READONLY, pos=wx.Point(5,75), size=wx.Size(135,20), choices=["NORMAL","UP","DOWN","LEFT","RIGHT"], value="NORMAL")
          self.data.Bind(wx.EVT_COMBOBOX, self.changedataType)

          self.Bind(wx.EVT_IDLE, self.UpdateAll)
     def UpdateAll(self, event=None):
          global TOOLS,CURRENT_SELECTED_LEVEL_WARP
          if TOOLS=="SELECTION" and CURRENT_SELECTED_LEVEL_WARP!=None:
               global ID,POSWARP,DATA
               self.ID__.SetValue(str(ID))
               for key, value in self.dataselect.items():
                    if value == DATA:
                         self.data.SetValue(str(key))
     def idChange(self, event=None):
          global ID,POSWARP,DATA
          if not event == None:
               if not event.GetKeyCode() == wx.WXK_RETURN:
                    event.Skip()
                    return 0
               else:
                    if str(self.ID__.GetValue()).isnumeric():
                         ID = int(self.ID__.GetValue())
          else:
               ID = int(self.ID__.GetValue())
     def changedataType(self, event=None):
          global ID,POSWARP,DATA
          sel_value=self.data.GetValue()
          DATA=self.dataselect[str(sel_value)]

class worldPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(window.Size[0],200))
          self.SetBackgroundColour("LIGHT GRAY")

class levelPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(window.Size[0],200))
          self.SetBackgroundColour("LIGHT GRAY")
          self.levelNameLabel=wx.StaticText(self, label="id (integer)", pos=(5,5))
          self.levelName=wx.TextCtrl(self, id=wx.NewId(), value="0", pos=wx.Point(5,25), size=wx.Size(135,20), style= wx.TE_PROCESS_ENTER)
          self.levelName.Bind(wx.EVT_KEY_DOWN, self.nameChange)
     def nameChange(self, event=None):
          global WORLD_DATA
          print(WORLD_DATA[CURRENT_SELECTED_LEVEL]["name"])
          if not event == None:
               if not event.GetKeyCode() == wx.WXK_RETURN:
                    event.Skip()
                    return 0
               else:
                    WORLD_DATA[CURRENT_SELECTED_LEVEL]["name"] = str(self.levelName.GetValue())
          else:
               WORLD_DATA[CURRENT_SELECTED_LEVEL]["name"] = str(self.levelName.GetValue())
     def setValues(self):
          self.levelName.SetValue(WORLD_DATA[CURRENT_SELECTED_LEVEL]["name"])

class zonePanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(window.Size[0],200))
          self.SetBackgroundColour("LIGHT GRAY")
          self.zoneWidthLabel=wx.StaticText(self, label="Width:",pos=wx.Point(117,5))
          self.zoneWidth=wx.SpinCtrl(self, value="1", pos=wx.Point(160,5), size=wx.Size(55,20), min=1, max=4096)
          self.zoneWidth.Bind(wx.EVT_SPINCTRL, self.changezoneSize)
          self.zoneHeightLabel=wx.StaticText(self, label="Height:",pos=wx.Point(110,25))
          self.zoneHeight=wx.SpinCtrl(self, value="1", pos=wx.Point(160,25), size=wx.Size(55,20), min=1, max=16)
          self.zoneHeight.Bind(wx.EVT_SPINCTRL, self.changezoneSize)

          self.zoneColour=wx.ColourPickerCtrl(self, pos=(5,5), style=wx.CLRP_SHOW_LABEL)
          self.zoneColour.Bind(wx.EVT_COLOURPICKER_CHANGED, self.changezoneColour)

          self.musicselect={"OVERWORLD":"music/main0.mp3",
                            "UNDERGROUND":"music/main1.mp3",
                            "FISHES":"music/main2.mp3",
                            "CASTLE":"music/main3.mp3",
                            "ICE/SNOW":"music/main4.mp3",
                            "DESERT":"music/main5.mp3",
                            "HAUNTED HOUSE":"music/main6.mp3",}

          self.zoneMusic=wx.ComboBox(self, pos=(5,50), choices=["OVERWORLD", "UNDERGROUND", "FISHES", "CASTLE", "ICE/SNOW", "DESERT", "HAUNTED HOUSE"], value="OVERWORLD", style=wx.CB_READONLY)
          self.zoneMusic.Bind(wx.EVT_COMBOBOX, self.changezoneMusic)

          self.zoneReset=wx.Button(self, label="RESET", pos=(885,105))
          self.zoneReset.SetBackgroundColour(wx.Colour(255,0,0))

          self.zoneReset.Bind(wx.EVT_BUTTON,self.ResetLevel)

     def ResetLevel(self, event):
          global CURRENT_SELECTED_LEVEL_DATA
          CURRENT_SELECTED_LEVEL_DATA["data"]=trueresize(CURRENT_SELECTED_LEVEL_DATA["data"],(CURRENT_SELECTED_LEVEL_DATA["data"].shape[1],CURRENT_SELECTED_LEVEL_DATA["data"].shape[0]),30,True)
          CURRENT_SELECTED_LEVEL_DATA["obj"].clear()
          CURRENT_SELECTED_LEVEL_DATA["warp"].clear()
     def changezoneSize(self, event=None):
          global CURRENT_SELECTED_LEVEL_DATA
          if not CURRENT_SELECTED_LEVEL_DATA == None:
               CURRENT_SELECTED_LEVEL_DATA["data"]=trueresize(CURRENT_SELECTED_LEVEL_DATA["data"],(self.zoneWidth.GetValue(),self.zoneHeight.GetValue()),30)
     def changezoneColour(self, event=None):
          global CURRENT_SELECTED_LEVEL_DATA
          if not CURRENT_SELECTED_LEVEL_DATA == None:
               CURRENT_SELECTED_LEVEL_DATA["color"]=rgbtohex(*((self.zoneColour.GetColour()).Get(includeAlpha=False)))
     def changezoneMusic(self, event=None):
          global CURRENT_SELECTED_LEVEL_DATA
          if not CURRENT_SELECTED_LEVEL_DATA == None:
               sel_value=self.zoneMusic.GetValue()
               CURRENT_SELECTED_LEVEL_DATA["music"]=self.musicselect[str(sel_value)]
     def setValues(self):
          self.zoneWidth.SetValue(str(CURRENT_SELECTED_LEVEL_DATA["data"].shape[1]))
          self.zoneHeight.SetValue(str(CURRENT_SELECTED_LEVEL_DATA["data"].shape[0]))
          self.zoneColour.SetColour(wx.Colour(*hextorgb(str(CURRENT_SELECTED_LEVEL_DATA["color"])[1:])))
          for key, value in self.musicselect.items():
               if value == CURRENT_SELECTED_LEVEL_DATA["music"]:
                    self.zoneMusic.SetValue(str(key))


class EntryPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel,pos=wx.Point(5,(24*16)+35), size=wx.Size((24*27)+332,165))
          self.SetBackgroundColour('GRAY')
          
          self.scrollMenus=wx.ScrollBar(self, id=wx.NewId(), pos=wx.Point(150,5), size=wx.Size(window.Size[0]-175,20))
          self.scrollMenus.SetScrollbar(0,1,6,1)
          self.scrollMenus.Bind(wx.EVT_SCROLL, self.changeType)
          
          font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
          self.typeMenus=wx.StaticText(self, id=wx.NewId(), pos=wx.Point(0,0), size=wx.Size(150,30), style=wx.ALIGN_CENTRE_HORIZONTAL)
          self.typeMenus.SetFont(font)

          self.worldPanel=worldPanel(self, window)

          self.levelPanel=levelPanel(self, window)

          self.zonePanel=zonePanel(self, window)
          
          self.tilePanel=tilePanel(self, window)

          self.objectPanel=objectPanel(self, window)

          self.warpPanel=warpPanel(self,window)
          
          #self.tiledatalabel.SetForegroundColour("WHITE")



          self.changeType()
     def changeType(self, event=None):
          global CURRENT_DRAW_TYPE_SELECT, SELECTING_OBJS_OR_WARPS
          if event==None:
               self.typeMenus.SetLabel("World")
               CURRENT_DRAW_TYPE_SELECT = "TILE"
               self.worldPanel.Show(True)
               self.levelPanel.Show(False)
               self.zonePanel.Show(False)
               self.tilePanel.Show(False)
               self.objectPanel.Show(False)
               self.warpPanel.Show(False)
          else:
               num=event.GetPosition()
               if num==0:
                    self.typeMenus.SetLabel("World")
                    self.worldPanel.Show(True)
                    self.levelPanel.Show(False)
                    self.zonePanel.Show(False)
                    self.tilePanel.Show(False)
                    self.objectPanel.Show(False)
                    self.warpPanel.Show(False)
               if num==1:
                    self.typeMenus.SetLabel("Level")
                    self.worldPanel.Show(False)
                    self.levelPanel.Show(True)
                    self.zonePanel.Show(False)
                    self.tilePanel.Show(False)
                    self.objectPanel.Show(False)
                    self.warpPanel.Show(False)
               if num==2:
                    self.typeMenus.SetLabel("Zone")
                    self.worldPanel.Show(False)
                    self.levelPanel.Show(False)
                    self.zonePanel.Show(True)
                    self.tilePanel.Show(False)
                    self.objectPanel.Show(False)
                    self.warpPanel.Show(False)
               if num==3:
                    self.typeMenus.SetLabel("Tiles")
                    CURRENT_DRAW_TYPE_SELECT = "TILE"
                    self.worldPanel.Show(False)
                    self.levelPanel.Show(False)
                    self.zonePanel.Show(False)
                    self.tilePanel.Show(True)
                    self.objectPanel.Show(False)
                    self.warpPanel.Show(False)
               if num==4:
                    self.typeMenus.SetLabel("Objects")
                    CURRENT_DRAW_TYPE_SELECT = "OBJECT"
                    SELECTING_OBJS_OR_WARPS = "OBJ"
                    self.worldPanel.Show(False)
                    self.levelPanel.Show(False)
                    self.zonePanel.Show(False)
                    self.tilePanel.Show(False)
                    self.objectPanel.Show(True)
                    self.warpPanel.Show(False)
               if num==5:
                    self.typeMenus.SetLabel("Warps")
                    CURRENT_DRAW_TYPE_SELECT = "WARP"
                    SELECTING_OBJS_OR_WARPS = "WARP"
                    self.worldPanel.Show(False)
                    self.levelPanel.Show(False)
                    self.zonePanel.Show(False)
                    self.tilePanel.Show(False)
                    self.objectPanel.Show(False)
                    self.warpPanel.Show(True)

#            -------------       more windowing effects     -      - -- - -- - 
class Panelsz():
     def __init__(self, panelTo, windowing, functions):
          global SBW, SBH, CURRENT_DRAW_TYPE_SELECT
          
          self.panelTo=panelTo
          self.window=windowing

          viewButton = wx.Button(self.panelTo,label="View",style=1)
          viewButton.Bind(wx.EVT_BUTTON, functions[0])
          self.viewPanel = wx.Panel(self.window, id=wx.NewId(), pos=wx.Point(0,30),size=wx.Size(2000,2000))
          viewStandsForInferno = wx.StaticText(self.viewPanel, id=wx.NewId(), label="View", pos=wx.Point(10,5))
          
          self.drawPanel = DrawPanel(self.viewPanel, self.window)
          self.itemPanel = ItemPanel(self.viewPanel, self.window)
          self.entryPanel = EntryPanel(self.viewPanel, self.window)

          SBW=wx.SpinCtrl(self.viewPanel, id=wx.NewId(), value="1", pos=wx.Point(250,5), size=wx.Size(45,20), min=1,max=16)
          SBH=wx.SpinCtrl(self.viewPanel, id=wx.NewId(), value="1", pos=wx.Point(300,5), size=wx.Size(45,20), min=1,max=16)

          self.BrushBut=wx.Button(self.viewPanel, id=wx.NewId(), label="Brush", pos=wx.Point(50,5), size=wx.Size(50,20))
          self.BrushBut.Bind(wx.EVT_BUTTON, self.TOBRUSH)
          self.PickBut=wx.Button(self.viewPanel, id=wx.NewId(), label="Picker", pos=wx.Point(100,5),size=wx.Size(50,20))
          self.PickBut.Bind(wx.EVT_BUTTON, self.TOPICK)
          self.SelBut=wx.Button(self.viewPanel, id=wx.NewId(), label="Selection", pos=wx.Point(150,5),size=wx.Size(72,20))
          self.SelBut.Bind(wx.EVT_BUTTON, self.TOSEL)

          self.WhatSelection=wx.StaticText(self.viewPanel, id=wx.NewId(), label="You'd better be drawing "+CURRENT_DRAW_TYPE_SELECT.lower() + "s today.",
                                           pos=wx.Point(720,5))
          self.WhatSelection.Bind(wx.EVT_IDLE, self.UpdateDrawType)

          
          codeButton = wx.Button(self.panelTo,label="Code",style=1,pos=wx.Point(51,0))
          codeButton.Bind(wx.EVT_BUTTON, functions[1])
          self.codePanel = wx.Panel(self.window, id=wx.NewId(), pos=wx.Point(0,30),size=wx.Size(2000,2000))
          codeStandsForInferno = wx.StaticText(self.codePanel, id=wx.NewId(), label="Code", pos=wx.Point(10,5))
          self.codeText = wx.TextCtrl(self.codePanel, id=wx.NewId(), value="",style=wx.TE_MULTILINE | wx.TE_RICH, pos=wx.Point(10,25), size=wx.Size(self.window.Size[0]-26,self.window.Size[1]-130))

          testButton = wx.Button(self.panelTo,label="Test",style=1,pos=wx.Point(102,0))
          testButton.Bind(wx.EVT_BUTTON, functions[2])
          self.testPanel = wx.Panel(self.window, id=wx.NewId(), pos=wx.Point(0,30),size=wx.Size(2000,2000))

          self.gamePanel = TestPanel(self.testPanel, self.window)


     def UpdateDrawType(self, event):
          self.WhatSelection.SetLabel("You'd better be drawing "+CURRENT_DRAW_TYPE_SELECT.lower() + "s today.")

     def TOBRUSH(self, event):
          global TOOLS
          TOOLS="BRUSH"
     def TOPICK(self, event):
          global TOOLS
          TOOLS="PICKER"
     def TOSEL(self, event):
          global TOOLS
          TOOLS="SELECTION"
          #sizer.Fit(self.codePanel)
class SelectTile(wx.Dialog):
     def __init__(self):
          super().__init__(None, title = "Select tile", size = (390,502))
          self.scale=2
          self.yoffset=0

          self.Bind(wx.EVT_MOUSE_EVENTS, self.capture_mouse)
          
          self.fileimage=wx.Image("sources\\smb_map.png", type=wx.BITMAP_TYPE_PNG)
          self.spritesheet=self.Rescale(self.fileimage)
          self.tiles=create_sprites(self.spritesheet, self.scale)

          self.Bind(wx.EVT_PAINT, self.Redraw)
          self.Bind(wx.EVT_IDLE, self.Refreshi)
          
          self.Show(True)
     def Refreshi(self, event):
          self.Refresh(eraseBackground=False)
          if self.yoffset <= 0:
               self.yoffset=0
          if self.yoffset >= 2880:
               self.yoffset=2880
     def Redraw(self, event):
          dc=wx.BufferedPaintDC(self)
          dc.SetBackground(wx.Brush(wx.Colour(200,200,200)))
          dc.Clear()
          for x,y in itertools.product(range(12),range(15)):
               try:
                    dc.DrawBitmap(wx.Bitmap(self.tiles[x+((y+self.yoffset//32)*12)]), x*16*self.scale, y*16*self.scale, True)
               except:
                    pass
          try:
               dc.SetBrush(wx.Brush(wx.Colour(255,255,255),wx.BRUSHSTYLE_TRANSPARENT))
               dc.SetPen(wx.Pen(wx.Colour(0,255,255),width=2))
               dc.DrawRectangle(wx.Rect(self.mouse_pos[0],self.mouse_pos[1],16*self.scale,16*self.scale))
          except:
               pass
     def Rescale(self, image):
          imagewo = image.Scale(image.GetWidth()*self.scale, image.GetHeight()*self.scale, wx.IMAGE_QUALITY_NEAREST)
          return imagewo
     def capture_mouse(self, event):
          global SELECTING_TILES_FROM_SELECTOR, SPRITE_INDEX
          self.mx,self.my=event.GetPosition()
          self.mouse_pos=round(self.mx/(16*self.scale))*(16*self.scale),round(self.my/(16*self.scale))*(16*self.scale)
          self.selected_tile=self.mouse_pos[0]//(16*self.scale)+(((self.mouse_pos[1]+self.yoffset)//(16*self.scale))*12)
          #print(self.selected_tile)
          self.yoffset-=int((event.GetWheelRotation()/12)/10)*(16*self.scale)
          #print(self.yoffset)
          if event.ButtonDown(wx.MOUSE_BTN_LEFT):
               SELECTING_TILES_FROM_SELECTOR = True
               if self.selected_tile >= 1253:
                    self.selected_tile=1253
               SPRITE_INDEX = self.selected_tile
          if event.ButtonUp(wx.MOUSE_BTN_LEFT):
               SELECTING_TILES_FROM_SELECTOR = False
          self.SetFocus()

class Window(wx.Frame):
     DATA=""
     def __init__(self, title, size):
          super().__init__(parent=None,id=wx.ID_ANY, title=title, size=size, style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
          
          self.InitMenuBar()
          self.InitLikeEverything()
          self.CreateStatusBar()

          self.converter=Convert()
          
          self.Show(True)

     def InitMenuBar(self):
          menuBar = wx.MenuBar()

          filemenu = wx.Menu()

          newfile= filemenu.Append(wx.NewId(), "New", " New world *snuzzles on you*")

          openfilemenu = wx.Menu()

          opentxtfilemenu = openfilemenu.Append(wx.NewId(), "...txt", " Open a map from a txt owo")
          
          openlinkfilemenu = openfilemenu.Append(wx.NewId(), "...url", " Open a map from a url (not implemented yet, sowwy uwu)")

          filemenu.Append(wx.NewId(), "Open from...", openfilemenu)

          savefile = filemenu.Append(wx.ID_SAVEAS, "Save as...", " o//w//o")

          exitfile = filemenu.Append(wx.ID_CLOSE, "Exit", " Exit this program >:3")

          tilemenu = wx.Menu()
          selecttile= tilemenu.Append(wx.ID_ANY, "Select Tile", " DO THIS OR YOUR INSANITY WILL GROW ESPONENTIALLY")

          aboutmenu = wx.Menu()
          help__ = aboutmenu.Append(wx.NewId(), "Help", " help")

          menuBar.Append(filemenu, "File")
          menuBar.Append(tilemenu, "Tiles")
          menuBar.Append(aboutmenu, "Help")

          self.SetMenuBar(menuBar)

          self.Bind(wx.EVT_MENU, self.exit, exitfile)
          self.Bind(wx.EVT_MENU, self.OpenFILE, opentxtfilemenu)
          self.Bind(wx.EVT_MENU, self.SaveFILE, savefile)
          self.Bind(wx.EVT_MENU, self.NewFILE, newfile)
          self.Bind(wx.EVT_MENU, self.TILEPALETTE, selecttile)
     def InitInfo(self):
          infopanel=wx.Panel() # Daswef
     def InitLikeEverything(self):
          self.optionPanel = wx.Panel(self,id=wx.NewId(),pos=wx.Point(0,0),size=wx.Size(2000,25))
          self.PANELS=Panelsz(self.optionPanel,self,[self.ShowView,self.ShowCode,self.ShowTest])
          self.initshow()
     def TILEPALETTE(self, event):
          SelectTile()
     def NewFILE(self,event):
          dlg=wx.Dialog(None, title = "New world...", size = (250,150)) 
          panel = wx.Panel(dlg)

          levellabel=wx.StaticText(panel,label="Levels:",pos=(5,5))
          levelcount=wx.SpinCtrl(panel,value="1",min=1,max=8,pos=(55,5))

          zonelabel=wx.StaticText(panel,label="Zones:",pos=(5,30))
          zonecount= wx.TextCtrl(panel,pos=(50,30))
      
          release = wx.Button(panel, wx.ID_OK, label = "OK", size = (50,20), pos = (190,105))

          if dlg.ShowModal() == wx.ID_OK:
               levels = levelcount.GetValue()
               zones = str(zonecount.GetValue()).split(",")
               initial={"type":"game",
                             "resource":[{"id":"map","src":"img/game/smb_map.png"},{"id":"obj","src":"img/game/smb_obj.png"}]
                             ,"initial":0,"world":[]}
               for level in range(levels):
                    initial["world"].append({"id":level,"name":"World "+str(level+1),"initial":0,"zone":[]})
                    for zone in range(int(zones[level])):
                         initial["world"][level]["zone"].append({"id":zone,"initial":196608,"color":"#6B8CFF","music":"music/main0.mp3","data":[[0,1],[2,3]],"obj":[],"warp":[]})
               print(json.dumps(initial))
               self.DecodeRawFILE(json.dumps(initial))
                         
     def OpenFILE(self,event):
          global CURRENT_SELECTED_LEVEL_DATA,WORLD_DATA,OBJ_DF
          openFileDialog = wx.FileDialog(None, message="Open some world.",
          wildcard='Json files (*.json)|*.json|Text files (*.txt)|*.txt|All Files|*',
          style=wx.FD_OPEN)

          try:
               if openFileDialog.ShowModal() == wx.ID_CANCEL:
                     return wx.ID_CANCEL
          except Exception:
               wx.LogError('Save failed!')
               raise

          temporal=open(openFileDialog.GetPath(), "r")
          self.DATA=temporal.read()
          
          openFileDialog.Destroy()
          self.DecodeRawFILE(self.DATA)
          print(CURRENT_SELECTED_LEVEL_DATA)
          temporal.close()
     def DecodeRawFILE(self,datatoread):
          global CURRENT_SELECTED_LEVEL_DATA,WORLD_DATA,OBJ_DF
          self.PANELS.codeText.SetValue("")
          self.PANELS.codeText.write(datatoread)
          WORLD_DATA=self.converter.Convert(self.PANELS.codeText.GetValue())
          CURRENT_SELECTED_LEVEL_DATA={"id_zone":WORLD_DATA[0]["zones"][0]["id_zone"],
                                       "id_level":WORLD_DATA[0]["id"],
                                       "playerpos":WORLD_DATA[0]["zones"][0]["playerpos"],
                                       "color":WORLD_DATA[0]["zones"][0]["color"],
                                       "music":WORLD_DATA[0]["zones"][0]["music"],
                                       "data":numpy.array(WORLD_DATA[0]["zones"][0]["data"], dtype=numpy.int64),
                                       "obj":WORLD_DATA[0]["zones"][0]["obj"],
                                       "warp":WORLD_DATA[0]["zones"][0]["warp"]}
          self.PANELS.itemPanel.UpdateData()
          self.PANELS.entryPanel.zonePanel.setValues()
          OBJ_DF = pandas.DataFrame(CURRENT_SELECTED_LEVEL_DATA["obj"])
     def LinkFILE(self,event):
          pass
     def SaveFILE(self, event):
          global WORLD_DATA
          #print(WORLD_DATA)
          sampledata = self.converter.getRaw(self.PANELS.codeText.GetValue())
          world=sampledata["world"]
          #print(len(world),len(world[0]["zone"]))
          UpdateData()
          for levels in range(len(world)):
               world[levels]["id"]=WORLD_DATA[levels]["id"]
               world[levels]["name"]=WORLD_DATA[levels]["name"]
               for zones in range(len(world[levels]["zone"])):
                    world[levels]["zone"][zones]["id"]=WORLD_DATA[levels]["zones"][zones]["id_zone"]
                    world[levels]["zone"][zones]["initial"]=WORLD_DATA[levels]["zones"][zones]["playerpos"]
                    world[levels]["zone"][zones]["color"]=WORLD_DATA[levels]["zones"][zones]["color"]
                    world[levels]["zone"][zones]["music"]=WORLD_DATA[levels]["zones"][zones]["music"]
                    world[levels]["zone"][zones]["data"]=WORLD_DATA[levels]["zones"][zones]["data"]
                    world[levels]["zone"][zones]["obj"]=WORLD_DATA[levels]["zones"][zones]["obj"]
                    world[levels]["zone"][zones]["warp"]=WORLD_DATA[levels]["zones"][zones]["warp"]
          sampledata["world"]=world
          openFileDialog = wx.FileDialog(None, message="Save world.",
          wildcard='Json files (*.json)|*.json|Text files (*.txt)|*.txt|All Files|*',
          style=wx.FD_SAVE)

          try:
               if openFileDialog.ShowModal() == wx.ID_CANCEL:
                     return wx.ID_CANCEL
          except Exception:
               wx.LogError('Save failed!')
               raise

          temporal=open(openFileDialog.GetPath(), "w+")

          bruh=json.dumps(sampledata)

          temporal.write(bruh)
          temporal.close()
          

          
     def initshow(self):
          self.PANELS.viewPanel.Show(True)
          self.PANELS.codePanel.Show(False)
          self.PANELS.testPanel.Show(False)
          self.Layout()


     def ShowView(self, event):
          self.PANELS.viewPanel.Show(True)
          self.PANELS.codePanel.Show(False)
          self.PANELS.testPanel.Show(False)
          self.Layout()
          
     def ShowCode(self, event):
          self.PANELS.viewPanel.Show(False)
          self.PANELS.codePanel.Show(True)
          self.PANELS.testPanel.Show(False)
          self.Layout()

     def ShowTest(self, event):
          self.PANELS.viewPanel.Show(False)
          self.PANELS.codePanel.Show(False)
          self.PANELS.testPanel.Show(True)
          self.Layout()
          
     def exit(self, event):
          self.Destroy()
          exit()
   
app=wx.App(False)
app.locale=wx.Locale(wx.LANGUAGE_ENGLISH)
window=Window("Mario Royale Maker",(996,684))
app.MainLoop()
