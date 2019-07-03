import wx
import requests
import itertools
import numpy, json
from skimage.draw import line

locale = wx.Locale.GetSystemLanguage() 

CURRENT_SELECTED_LEVEL_DATA = None
CURRENT_SELECTED_LEVEL_OBJ_DATA =  None

WORLD_DATA=None

SPRITE_INDEX = 0
DEPTH = 0
TILE_DEF = 0
EXTRA_DATA = 0

class Convert:
     def __init__(self):
          pass
     def Convert(self, data):

          data=data.replace("'",'"')
          
          self.jsondata=json.loads(data)
          
          print(type(self.jsondata),self.jsondata)
          self.world_data=[]
          for i in range(len(self.jsondata["world"])):
               self.world_data.append(self.Level(i))
                           
          return self.world_data #numpy.array(level1data, dtype=numpy.int64)

     def getRaw(self, data):

          data=data.replace("'",'"')
          
          jsos=json.loads(data)
          return jsos
     
     def Level(self, which):
          print(len(self.jsondata["world"][which]["zone"]))
          return {"id":self.jsondata["world"][which]["id"],
                  "name":self.jsondata["world"][which]["name"],
                  "zones":[{"id_zone":self.jsondata["world"][which]["zone"][x]["id"],
                           "playerpos":self.jsondata["world"][which]["zone"][x]["initial"],
                           "color":self.jsondata["world"][which]["zone"][x]["color"],
                           "data":self.jsondata["world"][which]["zone"][x]["data"]
                           } for x in range(len(self.jsondata["world"][which]["zone"]))]}

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

def UpdateData():
     global WORLD_DATA,CURRENT_SELECTED_LEVEL_DATA
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["id"]=CURRENT_SELECTED_LEVEL_DATA["id_zone"]
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["playerpos"]=CURRENT_SELECTED_LEVEL_DATA["playerpos"]
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["color"]=CURRENT_SELECTED_LEVEL_DATA["color"] #Errrori dappertutto
     WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["data"]=CURRENT_SELECTED_LEVEL_DATA["data"].tolist()


#print(hextorgb("6B8CFF"))

class DrawPanel(wx.Panel):
     
     def __init__(self, panel, window):
          
          
          super().__init__(panel,pos=wx.Point(5,30), size=wx.Size(window.Size[0]-350,window.Size[1]-300))
          self.SetBackgroundColour(wx.Colour(150,150,150))
          self.rotation=0
          self.Bind(wx.EVT_MOUSE_EVENTS, self.capture_mouse)
          self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown) #         ---------------    Non funzionaaaaa!1!!! trova un modo idiota :P
          self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
          self.Bind(wx.EVT_PAINT, self.OnPaint)
          self.scale=2
          self.fileimage=wx.Image("sources\\spritesheet.png", type=wx.BITMAP_TYPE_PNG)
          self.spritesheet=self.fileimage.Scale(self.fileimage.GetWidth()*self.scale, self.fileimage.GetHeight()*self.scale, wx.IMAGE_QUALITY_NEAREST)
          self.images=self.create_sprites(self.spritesheet) # è la maschera
          #self.temp=self.spritesheet.Scale(self.spritesheet.GetWidth()*2, self.spritesheet.GetHeight()*2, wx.IMAGE_QUALITY_NEAREST)
          #bitme=wx.StaticBitmap(self, bitmap=wx.Bitmap(temp),pos=wx.Point(32, 32),size=wx.Size(1648*2,144*2))
          fileimagetwo=wx.Image("sources\\powerups.png", type=wx.BITMAP_TYPE_PNG)
          rescalepows=fileimagetwo.Scale(fileimagetwo.GetWidth()*self.scale, fileimagetwo.GetHeight()*self.scale, wx.IMAGE_QUALITY_NEAREST)
          self.powerups=self.create_powerups(rescalepows)
          #self.Bind(wx.EVT_ENTER_WINDOW, self.StartUpdating)
          #self.Bind(wx.EVT_LEAVE_WINDOW, self.EndUpdating)
          
          self.Bind(wx.EVT_IDLE, self.OnIdling)
          
          self.yoffset=0
          self.brushsize=[1,1]
          self.isVert=False
          self.isBrushActive=True
          self.isBrushing=False




     def OnIdling(self,event):
          self.Refresh(eraseBackground=False)
          #event.RequestMore()

     def OnPaint(self, event=None):
          global CURRENT_SELECTED_LEVEL_DATA,CURRENT_SELECTED_LEVEL_OBJ_DATA
          try:
               widthlevel=CURRENT_SELECTED_LEVEL_DATA["data"].shape[1]
               heightlevel=CURRENT_SELECTED_LEVEL_DATA["data"].shape[0]
               

               self.old_brush_pos=round(self.mx/(16*self.scale))*(16*self.scale),round(self.my/(16*self.scale))*(16*self.scale)
               
               dc = wx.BufferedPaintDC(self)
               dc.SetBackground(wx.Brush(wx.Colour(hextorgb(CURRENT_SELECTED_LEVEL_DATA["color"][1:]))))
               dc.Clear()

               
               camoffset=int(self.rotation/10)*2
               if (216-162) >= widthlevel:
                    ranges=(0,widthlevel)
               else:
                    if 0-camoffset < 0:
                         ranges=(0,(216-162)-camoffset)
                    elif (216-162)-camoffset > widthlevel:
                         ranges=self.oldranges
                    else:
                         ranges=(0-camoffset,(216-162)-camoffset)
               self.oldranges=ranges
               
               
               for x,y in itertools.product(range(ranges[0],ranges[1]),range(0,heightlevel)):
                    #print(x,y)
                    posx=((camoffset*16)+(x*16))*self.scale
                    posy=((self.yoffset*8)+y*16)*self.scale
                    
                    
                         #print(SPRITE_INDEX)
                    dc.DrawBitmap(wx.Bitmap(self.images[decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[0]]),posx,posy,True)
                    try:
                         if posx == self.brush_pos[0] and posy == self.brush_pos[1] and self.isBrushing == True:
                              poszero,posone=line(self.old_brush_pos[0],self.old_brush_pos[1],self.brush_pos[0],self.brush_pos[1])

                              poszerotrue = numpy.array([int((poszero[x])/(16*self.scale))-camoffset for x in range(len(poszero)) if not (poszero[x])%16*self.scale], dtype=numpy.int64)
                              posonetrue = numpy.array([int((posone[x])/(16*self.scale)) for x in range(len(posone)) if not (posone[x])%16*self.scale], dtype=numpy.int64)
                              #print(int(self.yoffset/10),camoffset)
                              for brushlenx,brushleny in itertools.product(range(self.brushsize[0]),range(self.brushsize[1])):
                                   CURRENT_SELECTED_LEVEL_DATA["data"][posonetrue+brushleny,poszerotrue+brushlenx] = encode(SPRITE_INDEX, DEPTH, TILE_DEF, EXTRA_DATA)
                    except:
                         pass
                    if decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[3] == 17 or decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[3] == 21:
                         if decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[2] == 81:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[0]), posx, posy, True)
                         if decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[2] == 82:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[1]), posx, posy, True)
                         if decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[2] == 83:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[2]), posx, posy, True)
                         if decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[2] == 84:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[3]), posx, posy, True)
                         if decode(CURRENT_SELECTED_LEVEL_DATA["data"][y,x])[2] == 86:
                              dc.DrawBitmap(wx.Bitmap(self.powerups[4]), posx, posy, True)
                    
                         #print("Error has occurred")

               if self.isBrushActive:
                    dc.SetPen(wx.Pen(wx.Colour(255,255,255,128+(128*int(self.isBrushing)))))
                    dc.SetBrush(wx.Brush(wx.Colour(0,0,0,128+(128*int(self.isBrushing))),wx.BRUSHSTYLE_FDIAGONAL_HATCH))

                    self.brush_pos=round(self.mx/(16*self.scale))*(16*self.scale),round(self.my/(16*self.scale))*(16*self.scale)
                    
                    dc.DrawRectangle(*self.brush_pos,16*self.brushsize[0]*self.scale,16*self.brushsize[1]*self.scale)
               
               if (216-162) >= widthlevel:
                    dc.DrawText("At first block " + str(-camoffset) + ", at last block " + str(widthlevel), 5, 5)
               else:
                    dc.DrawText("At first block " + str(-camoffset) + ", at last block " + str((216-162)-camoffset), 5, 5)
          except:
               pass


          #self.Refresh(eraseBackground=False)
          #self.Update()
          
     def capture_mouse(self, event):
          
          self.mx,self.my=event.GetPosition()
          if self.isVert:
               self.rotation-=(event.GetWheelRotation()/12)
          elif not self.isVert:
               self.yoffset+=(event.GetWheelRotation()/12)
          if event.ButtonDown(wx.MOUSE_BTN_LEFT):
               if self.isBrushActive:
                    self.isBrushing=True
                    #print("Is brushing, calm down")
          if event.ButtonUp(wx.MOUSE_BTN_LEFT):
               if self.isBrushActive:
                    self.isBrushing=False
                    #print("No more brushing, calm")

          #self.Refresh(eraseBackground=False)
          self.SetFocus()
          #print(self.rotation)
          #print()
          #self.Refresh(eraseBackground=False)
     def OnKeyDown(self, event):
          #self.Refresh(eraseBackground=False)
          if int(event.GetKeyCode()) == 306: #Shift mothafuca
               self.isVert= True
          #print(event.GetKeyCode())
     def OnKeyUp(self, event):
          if int(event.GetKeyCode()) == 306: #Shift mothafuca
               self.isVert= False
          #print(event.GetKeyCode())
     def create_sprites(self, image):
          sprite_list=[]
          for x,y in itertools.product(range(9),range(103)):
               #print(x,y)
               temp=image.GetSubImage(wx.Rect((y*16)*self.scale,(128*self.scale)-((x*16)*self.scale),16*self.scale,16*self.scale))
               #temp=image.Resize(wx.Size(32,32),wx.Point(x*16,144-(y*16)))
               sprite_list.append(temp)
          #del temp, anothertemp
          return sprite_list
     def create_powerups(self, image):
          pw_list=[]
          for i in range(5):
               temp=image.GetSubImage(wx.Rect(i*(16*self.scale),0,(16*self.scale),(16*self.scale)))

               pw_list.append(temp)
          return pw_list

class ItemPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel,pos=wx.Point(window.Size[0]-340,30), size=wx.Size(window.Size[0]-873,window.Size[1]-300))
          self.SetBackgroundColour('LIGHT GRAY')
          self.tree=wx.TreeCtrl(self, id=wx.NewId(), pos=wx.Point(0,0), size=wx.Size(327,125))
          
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
          global WORLD_DATA,CURRENT_SELECTED_LEVEL_DATA
          item=str(self.tree.GetItemText(event.GetItem()))
          parent=str(self.tree.GetItemText(self.tree.GetItemParent(event.GetItem())))
          print(item,parent,int(parent[6:]),int(item[5:]))
          if item.startswith("Zone") and parent.startswith("Level"):
               #print(WORLD_DATA[int(parent[6:])]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])])
               WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["id"]=CURRENT_SELECTED_LEVEL_DATA["id_zone"]
               WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["playerpos"]=CURRENT_SELECTED_LEVEL_DATA["playerpos"]
               WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["color"]=CURRENT_SELECTED_LEVEL_DATA["color"] #Errrori dappertutto
               WORLD_DATA[CURRENT_SELECTED_LEVEL_DATA["id_level"]]["zones"][int(CURRENT_SELECTED_LEVEL_DATA["id_zone"])]["data"]=CURRENT_SELECTED_LEVEL_DATA["data"].tolist()
               #print(WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])])
               CURRENT_SELECTED_LEVEL_DATA={"id_zone":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["id_zone"],
                                            "id_level":WORLD_DATA[int(parent[6:])]["id"],
                                            "playerpos":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["playerpos"],
                                            "color":WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["color"],
                                            "data":numpy.array(WORLD_DATA[int(parent[6:])]["zones"][int(item[5:])]["data"], dtype=numpy.int64)}
               


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

          self.tile_def=wx.ComboBox(self, id=wx.NewId(), style=wx.CB_READONLY, pos=wx.Point(285,75), size=wx.Size(160,20), choices=["AIR",
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
                                                                   
          
     def spriteindexChange(self, event):
          global SPRITE_INDEX,DEPTH,TILE_DEF,EXTRA_DATA
          if not event.GetKeyCode() == wx.WXK_RETURN:
               event.Skip()
               return 0
          else:
               SPRITE_INDEX = int(self.spriteindex.GetValue())
               self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))
     def depthChange(self, event):
          global SPRITE_INDEX,DEPTH,TILE_DEF,EXTRA_DATA

          DEPTH = int(bool(self.depth.GetValue()))
          self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))
     def tile_defChange(self, event):
          global SPRITE_INDEX,DEPTH,TILE_DEF,EXTRA_DATA
          sel_index=self.tile_def.GetCurrentSelection()

          if sel_index == 0: # AIR
               TILE_DEF=0
          if sel_index == 1: # SOLID STANDARD
               TILE_DEF=1
          if sel_index == 2: # AIR
               TILE_DEF=2
          if sel_index == 3: # AIR
               TILE_DEF=3
          if sel_index == 4: # AIR
               TILE_DEF=17
          if sel_index == 5: # AIR
               TILE_DEF=18
          if sel_index == 6: # AIR
               TILE_DEF=19
          if sel_index == 7: # AIR
               TILE_DEF=21
          if sel_index == 8: # AIR
               TILE_DEF=22
          if sel_index == 9: # AIR
               TILE_DEF=24
          if sel_index == 10: # AIR
               TILE_DEF=81
          if sel_index == 11: # AIR
               TILE_DEF=82
          if sel_index == 12: # AIR
               TILE_DEF=83
          if sel_index == 13: # AIR
               TILE_DEF=84
          if sel_index == 14: # AIR
               TILE_DEF=85
          if sel_index == 15: # AIR
               TILE_DEF=86
          if sel_index == 16: # AIR
               TILE_DEF=160
          
          self.tiledata.SetValue(str(encode(SPRITE_INDEX,DEPTH,EXTRA_DATA,TILE_DEF)))
          
class worldPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel, pos=wx.Point(0,30), size=wx.Size(window.Size[0],200))
          self.SetBackgroundColour("LIGHT GRAY")



class EntryPanel(wx.Panel):
     def __init__(self, panel, window):
          super().__init__(panel,pos=wx.Point(5,window.Size[1]-265), size=wx.Size(window.Size[0]-18,window.Size[1]-635))
          self.SetBackgroundColour('GRAY')
          
          self.scrollMenus=wx.ScrollBar(self, id=wx.NewId(), pos=wx.Point(150,5), size=wx.Size(window.Size[0]-175,20))
          self.scrollMenus.SetScrollbar(0,1,8,1)
          self.scrollMenus.Bind(wx.EVT_SCROLL, self.changeType)
          
          font = wx.Font(18, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
          self.typeMenus=wx.StaticText(self, id=wx.NewId(), pos=wx.Point(0,0), size=wx.Size(150,30), style=wx.ALIGN_CENTRE_HORIZONTAL)
          self.typeMenus.SetFont(font)

          self.worldPanel=worldPanel(self, window)
          
          self.tilePanel=tilePanel(self, window)
          
          #self.tiledatalabel.SetForegroundColour("WHITE")



          self.changeType()
     def changeType(self, event=None):
          if event==None:
               self.typeMenus.SetLabel("World")
               self.worldPanel.Show(True)
               self.tilePanel.Show(False)
          else:
               num=event.GetPosition()
               if num==0:
                    self.typeMenus.SetLabel("World")
                    self.worldPanel.Show(True)
                    self.tilePanel.Show(False)
               if num==1:
                    self.typeMenus.SetLabel("Level")
                    self.worldPanel.Show(False)
                    self.tilePanel.Show(False)
               if num==2:
                    self.typeMenus.SetLabel("Zone")
                    self.worldPanel.Show(False)
                    self.tilePanel.Show(False)
               if num==3:
                    self.typeMenus.SetLabel("Tiles")
                    self.worldPanel.Show(False)
                    self.tilePanel.Show(True)
               if num==4:
                    self.typeMenus.SetLabel("Objects")
                    self.worldPanel.Show(False)
                    self.tilePanel.Show(False)
               if num==5:
                    self.typeMenus.SetLabel("Warps")
                    self.worldPanel.Show(False)
                    self.tilePanel.Show(False)
               if num==6:
                    self.typeMenus.SetLabel("Clone")
                    self.worldPanel.Show(False)
                    self.tilePanel.Show(False)
               if num==7:
                    self.typeMenus.SetLabel("Replace")
                    self.worldPanel.Show(False)
                    self.tilePanel.Show(False)

#            -------------       more windowing effects     -      - -- - -- - 
class Panelsz():
     def __init__(self, panelTo, windowing, functions):
          
          self.panelTo=panelTo
          self.window=windowing

          viewButton = wx.Button(self.panelTo,label="View",style=1)
          viewButton.Bind(wx.EVT_BUTTON, functions[0])
          self.viewPanel = wx.Panel(self.window, id=wx.NewId(), pos=wx.Point(0,30),size=wx.Size(2000,2000))
          viewStandsForInferno = wx.StaticText(self.viewPanel, id=wx.NewId(), label="View", pos=wx.Point(10,5))
          self.drawPanel = DrawPanel(self.viewPanel, self.window)
          self.itemPanel = ItemPanel(self.viewPanel, self.window)
          self.entryPanel = EntryPanel(self.viewPanel, self.window)

          
          codeButton = wx.Button(self.panelTo,label="Code",style=1,pos=wx.Point(51,0))
          codeButton.Bind(wx.EVT_BUTTON, functions[1])
          self.codePanel = wx.Panel(self.window, id=wx.NewId(), pos=wx.Point(0,30),size=wx.Size(2000,2000))
          codeStandsForInferno = wx.StaticText(self.codePanel, id=wx.NewId(), label="Code", pos=wx.Point(10,5))
          self.codeText = wx.TextCtrl(self.codePanel, id=wx.NewId(), value="",style=wx.TE_MULTILINE | wx.TE_RICH, pos=wx.Point(10,25), size=wx.Size(self.window.Size[0]-26,self.window.Size[1]-130))

          #sizer.Fit(self.codePanel)
          


class Window(wx.Frame):
     DATA=""
     def __init__(self, title, size):
          super().__init__(parent=None,id=wx.ID_ANY, title=title, size=size, style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
          self.Show(True)
          
          #self.Bind(wx.EVT_MOTION, self.GetMouse)
          

          #self.Cursor(wx.StockCursor(wx.CURSOR_PENCIL))
          self.InitMenuBar()
          #self.switchpanel=wx.Panel(self)
          self.InitLikeEverything()
          #self.InitInfo()
          self.CreateStatusBar()

          self.converter=Convert()
          #self.Centre()
          #print(self.PANELS.drawPanel,self.basicallyEverything,)
          #self.Bind(wx.FULL_REPAINT_ON_RESIZE, self.basicallyEverything, self.PANELS.drawPanel)
          
     def InitMenuBar(self):
          menuBar = wx.MenuBar()

          filemenu = wx.Menu()

          openfilemenu = wx.Menu()

          opentxtfilemenu = openfilemenu.Append(wx.NewId(), "...txt", " Open a map from a txt owo")
          
          openlinkfilemenu = openfilemenu.Append(wx.NewId(), "...url", " Open a map from a url (not implemented yet, sowwy uwu)")

          filemenu.Append(wx.NewId(), "Open from...", openfilemenu)

          savefile = filemenu.Append(wx.ID_SAVEAS, "Save as...", " o//w//o")

          exitfile = filemenu.Append(wx.ID_CLOSE, "Exit", " Exit this program >:3")

          aboutmenu = wx.Menu()
          help__ = aboutmenu.Append(wx.NewId(), "Help", " help")

          menuBar.Append(filemenu, "File")
          menuBar.Append(aboutmenu, "Help")
          self.SetMenuBar(menuBar)

          self.Bind(wx.EVT_MENU, self.exit, exitfile)
          self.Bind(wx.EVT_MENU, self.OpenFILE, opentxtfilemenu)
          self.Bind(wx.EVT_MENU, self.SaveFILE, savefile)
     def InitInfo(self):
          infopanel=wx.Panel() # Daswef
     def InitLikeEverything(self):
          self.optionPanel = wx.Panel(self,id=wx.NewId(),pos=wx.Point(0,0),size=wx.Size(2000,25))
          self.PANELS=Panelsz(self.optionPanel,self,[self.ShowView,self.ShowCode])
          self.initshow()
     def OpenFILE(self,event):
          global CURRENT_SELECTED_LEVEL_DATA,WORLD_DATA
          openFileDialog = wx.FileDialog(None, message="Open some world.",
          wildcard='Text files (*.txt)|*.txt|All Files|*',
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
          self.PANELS.codeText.SetValue("")
          self.PANELS.codeText.write(self.DATA)
          WORLD_DATA=self.converter.Convert(self.PANELS.codeText.GetValue())
          CURRENT_SELECTED_LEVEL_DATA={"id_zone":WORLD_DATA[0]["zones"][0]["id_zone"],
                                       "id_level":WORLD_DATA[0]["id"],
                                       "playerpos":WORLD_DATA[0]["zones"][0]["playerpos"],
                                       "color":WORLD_DATA[0]["zones"][0]["color"],
                                       "data":numpy.array(WORLD_DATA[0]["zones"][0]["data"], dtype=numpy.int64)}
          self.PANELS.itemPanel.UpdateData()
          print(CURRENT_SELECTED_LEVEL_DATA)

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
               for zones in range(len(world[levels]["zone"])):
                    world[levels]["zone"][zones]["id"]=WORLD_DATA[levels]["zones"][zones]["id_zone"]
                    world[levels]["zone"][zones]["initial"]=WORLD_DATA[levels]["zones"][zones]["playerpos"]
                    world[levels]["zone"][zones]["color"]=WORLD_DATA[levels]["zones"][zones]["color"]
                    world[levels]["zone"][zones]["data"]=WORLD_DATA[levels]["zones"][zones]["data"]
          sampledata["world"]=world
          openFileDialog = wx.FileDialog(None, message="Save world.",
          wildcard='Text files (*.txt)|*.txt|All Files|*',
          style=wx.FD_SAVE)

          try:
               if openFileDialog.ShowModal() == wx.ID_CANCEL:
                     return wx.ID_CANCEL
          except Exception:
               wx.LogError('Save failed!')
               raise

          temporal=open(openFileDialog.GetPath(), "w+")

          bruh=json.dumps(sampledata)

          bruh=bruh.replace("'",'"')
          
          temporal.write(bruh)
          temporal.close()
          

          
     def initshow(self):
          self.PANELS.viewPanel.Show(True)
          self.PANELS.codePanel.Show(False)
          self.Layout()


     def ShowView(self, event):
          self.PANELS.viewPanel.Show(True)
          self.PANELS.codePanel.Show(False)
          self.Layout()
          
     def ShowCode(self, event):
          self.PANELS.viewPanel.Show(False)
          self.PANELS.codePanel.Show(True)
          self.Layout()
          
     def exit(self, event):
          self.Destroy()
          exit()
   
app=wx.App(False)
app.locale=wx.Locale(wx.LANGUAGE_ENGLISH)
window=Window("Mario Royale Maker",(1200,800))
app.MainLoop()
