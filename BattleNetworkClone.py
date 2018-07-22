import sys, pygame
import json
from json import JSONDecodeError
from spritesheet import spritesheet
from pygame.locals import *
from random import randint, shuffle
from datetime import datetime
import time
from pygame import PixelArray, Surface, Rect
import math

pygame.init()
pygame.display.set_caption("Battle Network Clone")

#global resources
tileWidth = 40
tileHeight = 24
screenSize = width, height = 240, 160
scale = 3
displaySize = (width*scale, height*scale)
realScreen = pygame.display.set_mode(displaySize)
boardOffset = 80

elements = ["null","fire","aqua","elec","wood","break","cursor","wind","sword"]
#ToDo: move this to an external file
chipData = [
	#[name, dmg,elem,status, codes, mb, description]
	["AirShot"	, 20,7,0,["*"],		 4,["Knocks",	"enemy",	"back 1"]], 
	["WideSwrd"	, 80,8,1,["B"],		12,["Cuts enmy","in front!","Range: 3"]], 
	["Tackle"	, 40,5,1,["B"],		 6,["Tackle",	"1 sq ahd",	""]], 
	["TrgtShot"	, 60,6,1,["A"],		12,["Lock on",	"to clsest","enemy"]], 
	["Shockwav"	, 60,0,1,["A","B"],	10,["Shock",	"through",	"enemies"]], 
	["FireSwrd"	,130,1,1,["A"],		20,["Fire:",	"Cuts fwd",	"3 squares"]], 
	["AquaSwrd"	,150,2,1,["B"],		25,["Water:",	"Cuts fwd",	"3 squares"]], 
	["ElecSwrd"	,130,3,1,["A"],		23,["Elec:",	"Cuts fwd",	"3 squares"]], 
	["BambSwrd"	,140,4,1,["B"],		18,["Wood:",	"Cuts fwd",	"3 squares"]], 
	["atk+10"	,  0,0,0,["*"],		 4,["+10 for",	"selected",	"atk chip"]], 
	["+burn"	,  0,0,2,["*"],		30,["ignite",	"with fire","or N chip"]],
	["+freeze"	,  0,0,3,["*"],		30,["freeze",	"with aqua","or N chip"]],
	["+paralyz"	,  0,0,4,["*"],		30,["stun",		"with elec","or N chip"]], 
	["+ensare"	,  0,0,5,["*"],		30,["entwine",	"with wood","or N chip"]], 
	["SetRed"	,  0,0,0,["*"],		22,["lava panl","with fire","or N chip"]], 
	["SetBlue"	,  0,0,0,["*"],		20,["ice panl",	"with aqua","or N chip"]], 
	["SetYello"	,  0,0,0,["*"],		18,["elec panl","with elec","or N chip"]], 
	["SetGreen"	,  0,0,0,["*"],		10,["gras panl","with wood","or N chip"]], 
	["RockCube"	,  0,0,0,["*"],		 6,["Place a",	"RockCube",	"in front"]], 
	["DublCube"	,  0,0,0,["*"],		 6,["Place 2",	"RockCubes","opp sides"]], 
	["PanlGrab"	, 10,0,0,["*"],		 6,["Steals 1",	"enemy",	"square!"]], 
	["AreaGrab"	, 10,0,0,["*"],		 6,["Steals",	"left edge","from enmy"]],
	["GolmHit1"	,140,5,1,["B"],		17,["Hit 3panl","area arnd","front row"]],
	["AquaDrgn"	,130,2,1,["B"],		17,["Does","the","thing"]],
	["Boomer"	,100,4,0,["*"],		17,["Does","the","thing"]],
	
]
	
chipSpriteSheet = spritesheet("MMBN Assets/chip icons.png")
background = pygame.image.load("MMBN Assets/background.png")
backgroundRect = background.get_rect()	
pygame.font.init()
monospaceFont = pygame.font.SysFont("Monospace", 12, bold=True)
codeFont = pygame.font.SysFont("Monospace",7,bold=True)

up = K_UP
down = K_DOWN
left = K_LEFT
right = K_RIGHT
a = K_x
b = K_z
l = K_a
r = K_s
start = K_RETURN
select = K_BACKSPACE
debugPause = K_p
debugNextFrame = K_n

class Tickable():
	"""object that can be ticked each active frame"""
	def __init__(self):
		self.frame = 0

	def tick(self):
		self.frame += 1
		
class Expirable(Tickable):
	"""ticking object that expires
		expires when frame = endFrame"""
	def __init__(self, endFrame):
		super().__init__()
		self.endFrame = endFrame
		
	def expire(self):
		self.frame = self.endFrame
		
		
class Entity():
	"""an object that can have a position on the board"""
	def __init__(self, pos):
		self.pos = pos
		
class DrawableEntity(Entity):
	def __init__(self, pos, offset=[0,0], facing=1):
		super().__init__(pos)
		self.offset = offset
		self.offset[0]*=facing
		self.facing = facing
		
	def flip(self, facing=None):
		if facing!=self.facing:
			self.facing *= -1
			self.offset[0] *= -1
		
	def getPixelCoords(self):
		#translates pos into center x and y for screen
		x = (self.pos[0]+.5)*tileWidth + self.offset[0]	
		y = (self.pos[1]+.5)*tileHeight + self.offset[1] + boardOffset
		return x,y
		
class BattleEntity(DrawableEntity):
	"""an Entity that that can move, be hit, be affected by status ect"""
	def __init__(self, pos, team, element, name="Megaman", states=[], size=[64,54], offset=[6,-21], maxHp=randint(20,60)*5, statusEnabled=True):
		if team == 2:
			facing = -1
		else:
			facing = 1
		self.maxHp = maxHp
		self.hp = maxHp
		self.team = team
		self.moveLock = False
		self.status = 0
		self.statusTimer = 0
		self.element = element #normal, fire, aqua, elec, wood, break, cursor, wind, sword
		self.rect = Rect(0,0,size[0],size[1])
		#self.visualOffset = [0,0]
		super().__init__(pos, offset=offset[:], facing=facing)
		self.busterStrip = spritesheet("MMBN Assets/Entities/Megaman/buster.png").loadWholeStrip(imageCount=4, colorkey=-1)
		self.busterOffset = [39,19]
		self.statusEnabled = statusEnabled
		
		#initialize states - "stand" is the only required state
		self.stateStrips = {}
		for state in ["stand"]+states:
			stateStrip = spritesheet("MMBN Assets/Entities/"+name+"/"+name+" "+state+".png").loadWholeStrip(rect=self.rect, colorkey=-1)
			self.stateStrips[state] = stateStrip
		self.stateQueue = [] #[[state, index, duration],...]
		self.setState("stand",0,0)
		
		fire = spritesheet("MMBN Assets/Attacks/fire.png").loadWholeStrip(imageCount=5, colorkey=-1) 
		self.freeze = AnimationEntity(self.pos, "MMBN Assets/Attacks/freeze.png", [34,32], frameTimes=[60, 2, 2], colorkey=(0,0,0), facing=self.facing, offset=[-3,-22])
		paralyze = spritesheet("MMBN Assets/Attacks/paralyze.png").loadWholeStrip(rect=[0,0,80,80],colorkey=-1)
		self.vines = AnimationEntity(self.pos, "MMBN Assets/Attacks/vines.png", [47,49], frameDuration=3, colorkey=(0,0,0), offset=[-3,-21])
		self.statusStrips = [fire,None,paralyze,None]

	def moveDirection(self,direction):
		if direction == "up":
			self.moveRelative(0,-1)
		elif direction == "down":
			self.moveRelative(0,1)
		elif direction == "left":
			self.moveRelative(-1,0)
		elif direction == "right":
			self.moveRelative(1,0)
			
	def moveRelative(self,x,y):
		newX = self.pos[0]+x
		newY = self.pos[1]+y
		self.move(newX, newY)
		
	def move(self,x,y):
		"""move to tile at x,y"""
		if x in range(6) and y in range(3):	#catch out of bounds
			if not self.moveLock and self.state=="stand" and (self.statusTimer==0 or self.status<=2):
				if not board.tileOccupied([x,y]):
					
					"""#prevent moving past enemy
					if entity.pos == self.pos:	#don't check self
						continue
					if entity.team == self.team:	#don't check teamates
						continue
					if self.team == 1 and newX > entity.pos[0]:
							return
					elif self.team ==2 and newX < entity.pos[0]:
							return"""
					if board.boardTeam[x][y]==0 or self.team==board.boardTeam[x][y]:
						board.otherEntities.append(TileClaim([x,y],self,8))
						#self.pos = [x,y]
						if "move" in self.stateStrips:
							self.setStateSequence("move",[[0,1],[1,1],[2,1],[1,1],[0,1]], startUp=5, endLag=2, onlyIfEmpty=True) #TODO: make this use a default animation if one isn't defined in states
	
	def setState(self, state, index, duration):
		self.state = state
		self.stateIndex = index
		self.stateTimer = duration
		
	def setStateSequence(self, state, sequence, startUp=0, endLag=0, onlyIfEmpty=False):
		"""fill state queue with multiple indexes of same state with varying durations
			sequence - an array of the form[[stateIndex, duration],...]"""
		if not onlyIfEmpty or len(self.stateQueue)<=1: #only works if empty
			if startUp>0:
				self.stateQueue.append(["stand",0,startUp])
			for index, duration in sequence:
				self.stateQueue.append([state, index, duration])
			if endLag>0:
				self.stateQueue.append(["stand",0,endLag])
			
	def hit(self, damage, element, status):
		if self.status==1 and self.statusTimer>0: #if flinched don't get hit
			return
		effectiveness = typeEffectiveness(element,self.element)
		#status bonus
		if self.statusTimer>0 and self.status>1:
			if (self.status, element) in [(3,5),(4,6),(5,8)]:
				#double damage and end status
				effectiveness*=2
				self.statusTimer = 0
			elif self.status==2 and element==7:
				effectiveness*=2
				self.statusTimer = min([self.statusTimer+30,300]) #extend burn timer slightly when hit by wind
		#tile bonus
		x,y = self.pos
		if board.tileTypes[x][y]=="grass" and element==1:
			effectiveness *= 2
			board.tileTypes[x][y] = "null"
					
		if effectiveness==2:
			board.animations.append(AnimationEntity(self.pos,"MMBN Assets/super effective.png",(48,48)))
		elif effectiveness==4:
			board.animations.append(AnimationEntity(self.pos,"MMBN Assets/super effective 4x.png",(48,48)))#have to use different row in strip here
		#print("dealt",damage*effectiveness)
		self.damage(damage*effectiveness)
		
		if self.statusEnabled:
			if status==1: #flinch
				self.setState("hurt", 0, 22)
				self.status = 1
				self.statusTimer = 120
			if status>1 and self.statusTimer==0:
				#if you don't resist status type
				if typeEffectiveness(self.element, status-1)!=2:
					if status>2:
						self.setState("hurt", 0, 90)
					else:
						self.setState("hurt", 0, 20)
					self.status = status
					#more time if you are weak to status type?
					if typeEffectiveness(status-1, self.element)==2:
						self.statusTimer = 120
					else:
						self.statusTimer = 90
					
	def damage(self, damage):
		self.hp -= damage
	
	def cancelAttack(self):
		NotImplemented
		
	def draw(self):
		#set image to match current state
		self.image = self.stateStrips[self.state][self.stateIndex]
		if self.image:
			self.rect.center = self.getPixelCoords()
			
			if not(self.status==1 and self.statusTimer>0 and globalTimer%4>1): #don't draw every 2 frames if flinched
				screen.blit(pygame.transform.flip(self.image, self.facing==-1, False), self.rect)
				
			if self.status>1 and self.statusTimer>0:
				#draw status effect
				if self.status == 5:
					self.vines.pos = self.pos
					self.vines.draw()
					self.vines.tick()
				elif self.status == 3:
					self.freeze.pos = self.pos
					self.freeze.draw()
					self.freeze.tick()
				elif self.status == 2:
					offset = [randint(-16,16),randint(-32,0)]
					if globalTimer%4==0:
						board.animations.append(AnimationEntity(self.pos, "MMBN Assets/Attacks/fire.png", [24,23], frameDuration=2, facing=-self.facing, offset=offset[:]))
				else:
					statusStrip = self.statusStrips[self.status-2]
					statusFrame = (60-self.statusTimer)%len(statusStrip)-1
					screen.blit(statusStrip[statusFrame], self.rect)
		if self.state=="shoot":
			screen.blit(pygame.transform.flip(self.busterStrip[self.stateIndex], self.facing==-1, False), [self.rect[0]+self.busterOffset[0], self.rect[1]+self.busterOffset[1]])
								
	def tick(self):
		if self.statusTimer>0:
			if self.status==2 and self.statusTimer%12==0: #burn damage over time
				self.hit(1,1,0)
			self.statusTimer -= 1
		#x,y = self.pos
		if self.stateTimer==0:
			if self.stateQueue:
				#move to next state in sequence
				state, index, duration = self.stateQueue.pop(0)
				self.setState(state, index, duration)
			else:
				#go to stand
				self.setState("stand",0,0)
		if self.stateTimer > 0:
			self.stateTimer -= 1
		#print(self.state,self.stateIndex,self.stateTimer)
		"""if self.state!="stand" and self.stateTimer==0:
			self.state = "stand"
		#get rid of timings with animation timer
		elif self.state == "move":
			if self.stateTimer<=10 and self.stateTimer>=8:
				self.stateIndex+=1
			elif self.stateTimer<=7 and self.stateTimer>=5:
				self.stateIndex-=1
			if self.stateTimer == 0:
				self.setState("stand",0)
		elif self.state == "hurt":
			if self.stateTimer==0:
				self.setState("stand",0)"""
		if self.state=="shoot" and self.stateIndex==2 and self.stateTimer==0:
			board.hitboxes.append(Bullet(self.pos, 1*self.facing, damage=1, team=self.team, element=0))

class Navi(BattleEntity):
	"""a Battle Entity that can hold chips"""
	def __init__(self, pos, team, element):
		BattleEntity.__init__(self, pos, team, element, states=["stand", "move", "hurt", "shoot", "sword", "slide"])
		self.healCooldown = 0
		self.attackQueue = []
	
	def useChip(self):
		if not self.moveLock:
			if self.attackQueue:				
				attack = self.attackQueue.pop().use(self)
				if attack:
					board.addAttack(attack)
				else:
					board.animations.append(AnimationEntity(self.pos[:],"MMBN Assets/Attacks/puff.png",[30,30],frameDuration=2,offset=[0,-64])) #is supposed to float upwards, need to add movement to animations
	
	def draw(self):
		BattleEntity.draw(self)
		#draw hp
		HpTextShadow = monospaceFont.render(str(self.hp), False, (0,0,0))
		HpText = monospaceFont.render(str(self.hp), False, (255,255,255))
		X = (self.pos[0]+.5)*tileWidth
		Y = self.pos[1]*tileHeight+boardOffset+15
		if self.hp>0:
			screen.blit(HpTextShadow,(X+1, Y+1))
			screen.blit(HpText,(X,Y))
		#draw attack queue
		offset = len(self.attackQueue)*2
		for attack in self.attackQueue:
			#draw attack relative to player
			chipSprite = chipSpriteSheet.getSpriteById(attack.Id,22,14,14,colorkey=None)
			chipRect = Rect((0,0,14,14))
			chipSurface = Surface((16,16))
			chipSurface.fill((0,0,0))
			chipRect.center = (self.pos[0]+.5)*tileWidth-offset, self.pos[1]*tileHeight+boardOffset-offset-35
			chipSurface.blit(chipSprite,(1,1))
			screen.blit(chipSurface,chipRect)
			offset-=2
	
	def tick(self):
		BattleEntity.tick(self)
		x,y = self.pos
		if board.tileTypes[x][y]==self.element and self.healCooldown==0:
			self.hp+=1
			self.healCooldown=30
		self.healCooldown -= 1
		
class Player(Navi):
	"""Navi that looks at buttonInput"""
	def __init__(self, pos, element):
		Navi.__init__(self, pos, 1, element)
		
	def draw(self):
		Navi.draw(self)
		#draw text for first chip
		if self.attackQueue:
			topChip = self.attackQueue[len(self.attackQueue)-1]
			currentChipText = monospaceFont.render(str(topChip),False,(255,255,255))
			screen.blit(currentChipText,(0,height-15))
			
	def tick(self):
		Navi.tick(self)
		#look at buttonInput
		if buttonInput[up]:
			self.moveDirection("up")
		elif buttonInput[down]:
			self.moveDirection("down")
		elif buttonInput[left]:
			self.moveDirection("left")
		elif buttonInput[right]:
			self.moveDirection("right")
			
		if buttonDown[a]:
			self.useChip()
		elif buttonDown[b]:
			self.setStateSequence("shoot",[[0,1],[1,2],[2,2],[0,4]], startUp=5, onlyIfEmpty=True)
			
		if buttonDown[r] or buttonDown[l]:
			if board.frameCount >= board.turnFrames:
				game.state = "Custom"
				board.frameCount = 0
			else:
				self.flip()

class Enemy(Navi):
	"""Navi that acts on its own"""
	def __init__(self, pos, element):
		Navi.__init__(self, pos, 2, element)
		
	def tick(self):
		Navi.tick(self)
		if randint(0,30)==0:
			moves = ["left","right","up","down"]
			self.moveDirection(moves[randint(0,3)])
		elif randint(0,90)==0:
			self.useChip()
		elif randint(0,60)==0:
			self.setStateSequence("shoot",[[0,1],[1,2],[2,2],[0,4]],startUp=5)
					
class SandBag(BattleEntity):
	"""Battle Entity that counts up damage taken"""
	def __init__(self, pos, team):
		BattleEntity.__init__(self, pos, team, 0, name="sandbag", states=["stand", "hurt"], size=[31,41], offset=[0,-15])
		self.totalDamage = 0
		
	def damage(self, damage):
		self.totalDamage += damage
		
	def draw(self):
		BattleEntity.draw(self)
		damageText = monospaceFont.render(str(self.totalDamage),False,(0,0,0))
		X = (self.pos[0]+.5)*tileWidth-10
		Y = self.pos[1]*tileHeight+boardOffset+25
		screen.blit(damageText,(X,Y))

class TileClaim(Entity, Expirable):
	"""claims a tile for an entity to move to"""
	def __init__(self, pos, entity, endFrame):
		self.entity = entity
		Entity.__init__(self, pos)
		Expirable.__init__(self, endFrame)
		
	def tick(self):
		if self.entity.state == "move" and self.frame==self.endFrame:
			self.entity.pos = self.pos
		Expirable.tick(self)
		

class Game():
	"""controls the game state and which objects to tick"""
	def __init__(self):
		self.state = "TitleScreen"
		self.titleScreen = TitleScreen()
		
	def startBattle(self, mode):
		"""load folder and start a battle in the given mode"""
		global custom
		global board
		global player
		
		self.state = "Custom"
		player = Player([1,1],randint(0,9))
		folder, customDraw, extraMode, = load()
		
		if mode == "sandbag":
			custom = Custom(folder, 10, extraMode)
			custom.refresh() 
			board = Board([player, SandBag([4,1],2)], redRows=4)
		else:
			custom = Custom(folder, customDraw, extraMode)
			custom.folder.shuffle()
			custom.refresh()
			board = Board([player, Enemy([4,1],1),Enemy([5,1],2),Enemy([5,2],4)])
		
	def endBattle(self):
		self.state = "TitleScreen"
		
	def tick(self):
		if self.state == "Battle":
			board.draw()
			board.tick()
		elif self.state == "Custom":
			board.draw()
			custom.draw()
			custom.tick()
		elif self.state == "TitleScreen":
			self.titleScreen.draw()
			self.titleScreen.tick()
		elif self.state == "Folder":
			editor.draw()
			editor.tick()
			

class Cursor():
	"""class to navigate a menu using cursor"""
	def __init__(self, size, vertical, wrap):
		self.pos = 0
		self.size = size#length
		self.vertical = vertical #if true cursor uses up/down if false cursor uses left/right
		self.wrap = wrap #true if cursor is allowed to wrap
		self.state = 0
		self.currentInput = None
		self.buttons = [up, down, left, right]
	
	def move(self, direction):
		if self.vertical:
			if direction == up:
				self.pos -= 1
			elif direction == down:
				self.pos += 1
		else :
			if direction == right:
				self.pos += 1
			elif direction == left:
				self.pos -= 1
				
		if self.wrap:
			if self.pos >= self.size:
				self.pos = 0
			elif self.pos < 0:
				self.pos = self.size-1
		
	def select(self):
		return self.pos
		
	def tick(self):
		#get input
		#if no input go to state 0
		#if any input go to state 1
		#if same input state += 1
		#on states 2 and 23 move 1
		#on state 27 go ot state 23
		if self.currentInput == None:
			for button in self.buttons:
				if buttonHeld[button]:
					self.currentInput = button
					self.state = 1
					break
		elif buttonHeld[self.currentInput]:
			if self.state == 27:
				self.state = 23
			else:
				self.state += 1
		else:
			self.state = 0
			self.currentInput = None
			
		if self.state == 4 or self.state == 23:
			self.move(self.currentInput)
			
class CustomCursor(Cursor):
	"""cursor for custom window"""
	def __init__(self, size):
		Cursor.__init__(self, size, False, True)
		
	def move(self, direction):
		if direction==up:
			if self.pos>=5:
				self.pos -= 5
			elif self.pos <-1:
				self.pos += 1			
		elif direction==down:
			if self.pos>=0 and self.pos<self.size-5:
				self.pos += 5
			elif self.pos < 0:
				self.pos -= 1
		elif direction==left:
			if self.pos>=0:
				if self.pos%5==0:
					self.pos = self.pos//-5-1
				else:
					self.pos -= 1
			else:
				self.pos = self.pos*-5 -1
			
		elif direction==right:
			if self.pos>=0:
				if self.pos%5==4:
					self.pos = (self.pos+1)//-5
				elif self.pos==self.size-1:
					self.pos = self.pos//-5-1
				else:
					self.pos+=1
			else:
				self.pos = (self.pos+1)*-5
				
		#check bounds
		#print("cursor moved to",self.pos)
		if self.pos>=self.size:
			self.pos = self.size-1
		elif self.pos<-2:
			self.pos = -2
		#print("cursor at",self.pos)
		
		self.moveCooldown = 4

class ScreenScrollCursor(Cursor):
	"""a cursor that can only display a number of items at a time"""
	def __init__(self, size, screenSize):
		Cursor.__init__(self, size, True, False)
		self.screenSize = screenSize
		self.offset = 0 #position to draw top of menu
		self.buttons = [up, down, left, right, l, r]
	
	def move(self, direction):
		if direction == up:
			if self.pos > 0:
				self.pos -= 1
				if self.offset > self.pos:
					self.offset -= 1
		elif direction == down:
			if self.pos < self.size-1:
				self.pos += 1
				if self.pos >= self.offset+self.screenSize:
					self.offset += 1
		elif direction == l:
			if self.offset >= self.screenSize:
				self.pos -= self.screenSize
				self.offset -= self.screenSize
			else:
				self.pos -= self.offset #maybe
				self.offset = 0
		elif direction == r:
			if self.offset < self.size-2*self.screenSize:
				self.pos += self.screenSize
				self.offset += self.screenSize
			else:
				self.pos += self.size-self.screenSize-self.offset
				self.offset = self.size-self.screenSize


class TitleScreen():
	"""the title screen allows selecting a mode to play"""
	def __init__(self):
		self.cursor = Cursor(3, True, True)
		self.image = pygame.image.load("MMBN Assets/Menus/title3.png")
		self.cursorImage = pygame.image.load("MMBN Assets/Menus/cursor.png")
		
	def draw(self):
		#draw title
		screen.blit(self.image,(0,0))
		#draw options
		options = ["Random Battle","Sandbag Practice","Folder Edit"]
		for i in range(3):
			screen.blit(monospaceFont.render(options[i], False, (255,255,255)), (60, 116+10*i))
		#draw cursor
			screen.blit(self.cursorImage, (50-globalTimer%18//6, 116+10*self.cursor.pos))
				
	def tick(self):
		self.cursor.tick()
		if buttonDown[a]:
			choice = self.cursor.select()
			if choice == 0:
				game.startBattle("normal")
			elif choice == 1:
				game.startBattle("sandbag")
			elif choice == 2:
				global editor
				folder, customDraw, extraMode = load()
				editor = Editor(folder)
				game.state = "Folder"
		
		
class Board():
	"""class to hold tiles and entities of a battle"""
	def __init__(self, entities, redRows=3):
		tileTypes = ["null", "volcano", "ice", "moveUp", "grass"]
		self.battleEntities = entities
		self.attackEntities = []
		self.hitboxes = []
		self.animations = []
		self.otherEntities = []
		self.boardTeam = [[1,1,1] for i in range(redRows)] + [[2,2,2] for i in range(6-redRows)] #each row of board 0 = neutral, 1 = red, 2 = blue
		self.tileTypes = [["null" for i in range(3)] for i in range(6)]
		self.turnFrames = 256
		self.timeFreeze = False
		self.timeFreezeStartup = 0
		self.activeTimeFreezeAttack = None
		
		#resources for drawing
		self.tileGroups = {}
		for tileType in tileTypes:
			for color in ["red","blue"]:
				self.tileGroups[color+tileType] = spritesheet("MMBN Assets/Board/tile "+color+" "+tileType+".png").loadStripGroup([0,0,tileWidth,tileHeight],colorkey=(0,0,0))
		self.customGauge = pygame.image.load("MMBN Assets/Custom/custom guage.png")
		self.customRect = Rect(0,0,width,height)
		self.frameCount = 0
		self.nubStrip = spritesheet("MMBN Assets/Board/tile nubs.png").loadWholeStrip(rect=[0,0,40,6],colorkey=(255,255,255))
		self.tileRects = []
		#self.tileBorderRects = []
		for i in range(6):
			self.tileRects.append([Rect(i*tileWidth,j*tileHeight+boardOffset,tileWidth,tileHeight) for j in range(3)])
			#self.tileBorderRects.append([Rect(i*tileWidth,j*tileHeight+tileWidth,tileWidth,tileHeight) for j in range(3)])
	
	def addAttack(self, attack):
		if attack:
			if isinstance(attack,TimeFreezeAttack):
				self.timeFreeze = True
				self.timeFreezeStartup = 60
				self.activeTimeFreezeAttack = attack
			else:
				self.attackEntities.append(attack)
	
	def tileOccupied(self, pos):
		#returns true if there's an entity or tileclaim at pos
		for entity in self.battleEntities+self.otherEntities:
			if entity.pos == pos:
				return True
		return False
		
	def setTile(self, x, y, tile):
		#check if legal
		if tile and x in range(6) and y in range(3):
			self.tileTypes[x][y] = tile
		
	def burnTile(self, x, y, element):
		#if element beats tile type at x,y set to null tile
		if x in range(6) and y in range(3):
			if element==1 and self.tileTypes[x][y]=="grass":
				self.tileTypes[x][y] = "null"
	
	def frontTile(self, y, team):
		#find the frontmost tile of the given row and team
		#doesn't work for surrounded boards
		if team == 1:
			direction = 1
			frontRow = 0
		else:
			direction = -1
			frontRow = 5
		for i in range(frontRow, 5-frontRow+direction, direction):
			if board.boardTeam[i][y] != team:
				return [i-direction, y]

	def frontRow(self, team):
		#find team's first row
		#doesn't work for surrounded boards
		if team == 1:
			minMaxAlias = max
			frontRow = 0
		else:
			minMaxAlias = min
			frontRow = 5
		#take min/max of firstTile for each row
		for y in range(3):
			frontRow = minMaxAlias(self.frontTile(y, team)[0], frontRow)
		return frontRow

	def draw(self):
		screen.blit(background, backgroundRect)
		#draw board tiles
		for i in range(6):
			for j in range(3):
				#screen.blit(self.tileBorderStrip[self.boardTeam[i][j]], self.tileBorderRects[i][j])
				#screen.blit(self.tileStrip[self.tileTypes[i][j]], self.tileRects[i][j])
				if self.boardTeam[i][j] == 2:
					color = "blue"
				else:
					color = "red"
				currentGroup = self.tileGroups[color+self.tileTypes[i][j]]
				currentTileStrip = currentGroup[j]
				screen.blit(currentTileStrip[globalTimer//4%len(currentTileStrip)], self.tileRects[i][j])
			#draw nubs at bottom
			screen.blit(self.nubStrip[self.boardTeam[i][2]-1], (tileWidth*i,tileHeight*3+boardOffset))
					
		#draw hitboxes
		if not self.timeFreeze:
			for hitbox in self.hitboxes:
				#if hitbox.team!=1:
				hitbox.draw()
			
				
		#sort entities from back to front for drawing
		self.battleEntities.sort(key=lambda x: x.pos[1])
		for entity in self.battleEntities:	#draw all entities
			entity.draw()				
				
		for animation in self.animations:
			animation.draw()
			
		if self.timeFreeze and self.timeFreezeStartup > 0:
			if self.activeTimeFreezeAttack.user.team == 1:
				screen.blit(self.activeTimeFreezeAttack.nameText,(40,40))
			else:
				screen.blit(self.activeTimeFreezeAttack.nameText,(width-104,40))		
		
		self.customRect.right = self.frameCount*width/self.turnFrames
		screen.blit(self.customGauge,self.customRect)
		if self.frameCount >= self.turnFrames:
			timerText = monospaceFont.render("Press R to open custom!", False, (0,0,0))
			screen.blit(timerText,(0,0))
			
	def tick(self):
		if not self.timeFreeze:
			for entity in self.battleEntities:
				entity.tick()
				if isinstance(entity, BattleEntity) and entity.hp<= 0:
					self.battleEntities.remove(entity)
				
			for entity in self.otherEntities:
				entity.tick()
				if isinstance(entity, TileClaim) and entity.frame>entity.endFrame:
					self.otherEntities.remove(entity)
			
			for attackEntity in self.attackEntities:
				attackEntity.tick()
				if attackEntity.frame > attackEntity.endFrame:
					self.attackEntities.remove(attackEntity)		
				
			for animation in self.animations:
				animation.tick()
				if animation.frame >= animation.endFrame:
					self.animations.remove(animation)
		
			hasEnemies = False
			hasPlayer = False
			for entity in self.battleEntities:
				if isinstance(entity, Enemy):
					hasEnemies = True
				elif isinstance(entity, Player):
					hasPlayer = True
				elif isinstance(entity, SandBag):
					hasEnemies = True
			if not hasPlayer or not hasEnemies:
				game.endBattle()
				
			for hitbox in self.hitboxes:
				hitbox.tick()
				if hitbox.frame >= hitbox.activeFrames+hitbox.warningFrames:
					self.hitboxes.remove(hitbox)
						
			if self.frameCount >= self.turnFrames:
				self.frameCount = self.turnFrames
			else:
				self.frameCount += 1
		elif self.timeFreezeStartup>0:
			#display the name of the time freeze attack and allow counters
			
			self.timeFreezeStartup -= 1
		elif self.activeTimeFreezeAttack:
			#only tick the time freeze attack
			if self.activeTimeFreezeAttack and self.activeTimeFreezeAttack.frame == self.activeTimeFreezeAttack.endFrame:
				#expire timeFreezeAttack
				self.timeFreeze = False
				self.activeTimeFreezeAttack = None
			else:
				self.activeTimeFreezeAttack.tick()

		
class Custom():
	""""handles the data for the custom window"""
	def __init__(self, folder, customDraw, extraMode):
		self.folder = folder
		self.customDraw = customDraw
		self.cursor = CustomCursor(customDraw)
		self.hand = []
		self.selectedChips = []
		self.extraMode = extraMode
		self.extraUsed = False
		self.hasReg = self.folder.regIndex is not None
		self.hidden = False
		
		#shuffle(self.folder)
		#self.refresh()
		
		#resources for drawing
		self.cursorRect = Rect(0,0,18,18)
		self.cursorSprites = spritesheet("MMBN Assets/Custom/custom cursor.png").load_strip(self.cursorRect,2,colorkey=-1)
		self.customWindow = pygame.image.load("MMBN Assets/Custom/custom window.png")
		self.customWindowRect = self.customWindow.get_rect()
		#self.chipImageStrip = spritesheet("chip images.png").load_strip([0,0,56,48],10)
		#self.elementStrip = spritesheet("elements.png").load_strip([0,0,14,14],9,colorkey=-1)
		self.handRects = [Rect(i%5*16+9,i//5*24+105,14,14) for i in range(10)]
		self.regClampStrip = spritesheet("MMBN Assets/Custom/reg clamp.png").loadWholeStrip(rect=(0,0,21,18),colorkey=-1)
		extraButtonStrip = spritesheet("MMBN Assets/Custom/extra buttons.png").load_strip((0,0,24,16),10)
		if self.extraMode:
			self.extraButtons = None
			if "discard" in self.extraMode:
				if "recycle" in self.extraMode and "restock" in self.extraMode:
					extraButtonId = 2
				elif "recycle" in self.extraMode:
					extraButtonId = 3
				elif "restock" in self.extraMode:
					extraButtonId = 1
				else:
					extraButtonId = 0
			elif "shuffle" in self.extraMode:
				extraButtonId = 4
			self.extraButtons = [extraButtonStrip[extraButtonId],extraButtonStrip[extraButtonId+5]]
		else:
			self.extraButtons = None
		
	def refresh(self):
		"""draws a new hand and resets relevant data"""
		self.refillHand()
		self.extraUsed = False
		self.cursor = CustomCursor(len(self.hand))

	def refillHand(self):
		#draw chips to refill hand		
		drawAmount = self.customDraw-len(self.hand)
		if len(self.folder) < drawAmount:
			drawAmount = len(self.folder)
		for dealtChip in self.folder.deal(drawAmount):
			self.hand.append(dealtChip)
		self.selectedCode = None
		self.selectedID = None
		self.selectedChips = []
		self.selected = [False for i in range(self.customDraw)]
	
	
	def select(self):
		"""selects the chip at the current cursor position and adds it to selectedChips
			returns selectedChips if user selects OK"""
		self.hidden = False
		#close custom
		if self.cursor.pos==-1:
			#load selectedChips attacks into attackQueue
			attackQueue = []
			if 0 in self.selectedChips:
				self.hasReg = False
			for selectedChip in self.selectedChips:
				attackQueue.append(self.hand[selectedChip])
			attackQueue = processAttackQueue(attackQueue)
			#remove selected chips from hand
			newHand = []
			for i in range(len(self.hand)):
				if not self.selected[i]:
					newHand.append(self.hand[i])
			self.hand = newHand
			self.refresh()
			return attackQueue
			
		elif self.cursor.pos==-2:
			if not self.extraUsed:
				if "discard" in self.extraMode and self.selectedChips:
					
					if 0 in self.selectedChips:
						self.hasReg = False
					#discard chips
					newHand = []
					removedChips = []
					for i in range(len(self.hand)):
						if not self.selected[i]:
							newHand.append(self.hand[i])
						else:
							removedChips.append(self.hand[i])
					if "recycle" in self.extraMode:
						self.folder.chips += removedChips
						
					self.hand = newHand
					self.selectedChips = []
					self.selected = [False for i in range(len(self.hand))]
					self.selectedCode = None
					self.selectedID = None
					
					if "restock" in self.extraMode:
						self.refillHand()
					self.extraUsed = True
						
				elif "shuffle" in self.extraMode:
					#shuffle all chips that aren't selected
					#remove all unselected chips
					unselectedChips = [self.hand[i] for i in range(len(self.hand)) if not self.selected[i] and not(self.hasReg and i==0)] 
					#print("unselected:",unselectedChips)
					#add unselected chips to folder
					self.folder.chips += unselectedChips
					#print("folder:",self.folder)
					#shuffle folder
					shuffle(self.folder.chips)
					#restock
					for i in range(len(self.hand)):
						if not self.selected[i] and not(self.hasReg and i==0):
							self.hand[i] = self.folder.deal(1)[0]
					self.extraUsed = True
				
				
		elif self.cursor.pos>=0 and self.cursor.pos<len(self.hand):
			selectedChip = self.hand[self.cursor.pos]
			if len(self.selectedChips)<5 and not self.selected[self.cursor.pos] and (self.selectedCode==None or self.selectedCode==selectedChip.code or self.selectedID==selectedChip.Id or (self.selectedCode!=-1 and selectedChip.code=="*")):
				self.selectedChips.append(self.cursor.pos) #select chip by adding it's cursor pos to self.selectedChips
				self.selected[self.cursor.pos] = True
				self.selectCode(selectedChip.Id,selectedChip.code)
			
	def deselect(self):
		"""deselects the last chip selected"""
		self.hidden = False
		if len(self.selectedChips) > 0:
			self.selected[self.selectedChips.pop()] = False #pop and deselect chip
			#search selected chips to update selectedCode and selectedID
			#run through selected chips again
			self.selectedCode = None
			self.selectedID = None
			for chipLocation in self.selectedChips:
				currentChip = self.hand[chipLocation]
				self.selectCode(currentChip.Id,currentChip.code)
		
	def selectCode(self, chipID, chipCode):
		if self.selectedID==None:
			self.selectedID = chipID
		elif self.selectedID!=chipID:
			self.selectedID = -1
		
		if self.selectedCode==None and chipCode!="*":
			self.selectedCode = chipCode
		elif self.selectedCode!=chipCode and chipCode!="*":
			self.selectedCode = -1
		

		
	def draw(self):
		board.draw()
		if not self.hidden:
			screen.blit(self.customWindow, self.customWindowRect)
			#draw extra button
			if self.extraButtons:
				if self.extraUsed:
					screen.blit(self.extraButtons[1],(92,136,24,16))
				else:
					screen.blit(self.extraButtons[0],(92,136,24,16))
					
			if custom.hand:
				#draw each chip
				for i in range(len(self.hand)):
					currentChip = self.hand[i]
					#chipID, chipCode = self.hand[i]
					icon = currentChip.icon
					if not self.selected[i]:
						#if not selectable grey out
						if len(self.selectedChips)>=5 or currentChip.code!="*" and currentChip.code!=self.selectedCode and self.selectedCode!=None:
							greySurface(icon)
						else:#len(self.selectedChips)<5 and (self.selectedCode==None or self.selectedCode==chipCode or self.selectedID==chipID or (self.selectedCode!=-1 and chipCode=="*")):
							unGreySurface(icon)
							
						screen.blit(icon,self.handRects[i])
					
					code = codeFont.render(currentChip.code, False, (255,255,0))
					screen.blit(code,(self.handRects[i].left+4,self.handRects[i].top+15))
					
				#draw details of current chip
				if self.cursor.pos >= 0:
					currentChip = self.hand[self.cursor.pos]
					screen.blit(currentChip.chipWindow,(10,22))
					chipNameText = monospaceFont.render(currentChip.name,False,(255,255,255))
					screen.blit(chipNameText,(15,12))
				
				#draw selectedChips chips
				pos = 0
				for chipIndex in self.selectedChips:
					selectedRect = Rect(97,pos*16+25,14,14)
					screen.blit(self.hand[chipIndex].icon,selectedRect)
					pos += 1
			
			if self.hasReg:
				screen.blit(self.regClampStrip[globalTimer%16//8],(4,103))
			
			#draw cursor
			if self.cursor.pos<0:
				#replace this with a special cursor to fit OK button
				self.cursorRect.left = 95
				self.cursorRect.top = 91-22*self.cursor.pos
			else:
				self.cursorRect.left = self.cursor.pos%5*16+7
				self.cursorRect.top = self.cursor.pos//5*24+103
			screen.blit(self.cursorSprites[globalTimer%16//8], self.cursorRect)
		
	def tick(self):
		self.cursor.tick()
		if buttonDown[start]:
			self.cursor.pos = -1
		if buttonDown[a]:
			selectedAttacks = self.select()			
			if selectedAttacks!=None:	#OK is pressed
				if selectedAttacks:	#don't overwrite if no attacks selected
					player.attackQueue = selectedAttacks
				for enemy in board.battleEntities:
					if isinstance(enemy, Enemy):
						chipCount = randint(0,5)
						if chipCount > 0:
							enemy.attackQueue = []
							for i in range(chipCount):
								enemy.attackQueue.append(ChipAttack([randint(0, len(chipData)-1),"*"]))
							enemy.attackQueue = processAttackQueue(enemy.attackQueue)
				game.state = "Battle"
		if buttonDown[b]:
			self.deselect()
		if buttonDown[l]:
			game.endBattle()
		if buttonDown[select]:
			self.hidden = not self.hidden

		
class Editor():
	"""stores data for folder editing menu"""
	def __init__(self, folder):
		#folder
		self.folder = folder
		#while len(self.folder)<30:
		#	self.folder.append(None)
		#self.folder = Folder(self.folder)
		
		#pack
		#fill pack with all chips
		self.pack = []
		for i in range(len(chipData)):
			for code in chipData[i][4]:
				self.pack.append([i,code])
		self.pack = Folder(self.pack)
		
		self.rows = 7
		self.cursors = [ScreenScrollCursor(30,self.rows),ScreenScrollCursor(len(self.pack),self.rows)]
		self.cursorSide = 0	#folder/pack 
		self.selectedSide = None
		self.selectedIndex = None
		
		self.background = pygame.image.load("MMBN Assets/Menus/folder menu.png")
		self.editorthing = pygame.image.load("MMBN Assets/Menus/folder editor.png")
		self.cursorImage = pygame.image.load("MMBN Assets/Menus/cursor.png")
		self.regFrame = pygame.image.load("MMBN Assets/Menus/reg frame.png")
		self.tagFrame = pygame.image.load("MMBN Assets/Menus/tag frame.png")
		
		
	def select(self):
		currentIndex = self.cursors[self.cursorSide].pos
		#print("current Index",currentIndex)
		if self.selectedIndex == None:
			self.selectedSide = self.cursorSide
			self.selectedIndex = currentIndex
		else:
			#double tap
			if self.cursorSide == self.selectedSide and self.selectedIndex == currentIndex:
				if self.cursorSide == 0:
					#remove chip from folder
					self.folder.chips[self.selectedIndex] = None
				else:
					#replace first empty chip in folder
					if None in self.folder.chips:
						self.folder.chips[self.folder.chips.index(None)] = self.pack.chips[self.selectedIndex]
					
			#left(selected) to right (remove)
			elif self.selectedSide == 0 and self.cursorSide == 1:
				self.folder.chips[self.selectedIndex] = self.pack.chips[currentIndex]
			#right to left
			elif self.selectedSide == 1 and self.cursorSide == 0:
				self.folder.chips[currentIndex] = self.pack.chips[self.selectedIndex]
			#left to left
			elif self.selectedSide == 0 and self.cursorSide == 0:
				#swap
				a = self.folder.chips[currentIndex]
				b = self.folder.chips[self.selectedIndex]
				self.folder.chips[currentIndex] = b
				self.folder.chips[self.selectedIndex] = a
				#swap reg/tag index
			
			self.deselect()
	
	def deselect(self):
		self.selectedSide = None
		self.selectedIndex = None
						
	def scroll(self, direction):
		if direction == "left":
			self.cursorSide = 0
		elif direction == "right":
			self.cursorSide = 1
		
	def save(self):
		if None not in self.folder.chips:
			save(self.folder, 7, ["discard","restock","recycle"])
	
	def draw(self):
		screen.blit(self.background,backgroundRect)
		if self.cursorSide == 0:
			x = 1
			currentFolder = self.folder
			hOffset = 104
		else:
			x = -478+width-1
			currentFolder = self.pack
			hOffset = 10
		screen.blit(self.editorthing,(x,16))
			
		currentCursor = self.cursors[self.cursorSide]
		displayRange = range(currentCursor.offset, currentCursor.offset+self.rows)
		
		#draw folder or pack
		for i in range(self.rows):
			drawIndex = i+currentCursor.offset
			if drawIndex < len(currentFolder) and currentFolder.chips[drawIndex] != None:
				currentChip = currentFolder.chips[drawIndex]
				displayText = monospaceFont.render(currentChip.name, False, (255,255,255))
				codeText = monospaceFont.render(currentChip.code, False, (255,255,255))
				screen.blit(displayText, (hOffset+16, 16*i+33))
				elementStrip = spritesheet("MMBN Assets/elements.png").load_strip([0,0,14,14],9,colorkey=-1)
				screen.blit(elementStrip[currentChip.element], (hOffset+80,16*i+33))
				screen.blit(codeText, (hOffset+16+64+16, 16*i+33))
				screen.blit(currentChip.icon,(hOffset,16*i+33))
		
		#draw reg frame
		if self.cursorSide == 0 and self.folder.regIndex in displayRange:
			screen.blit(self.regFrame, (97,(self.folder.regIndex-currentCursor.offset+2)*16))
		#draw tag frames
		if self.folder.tagIndexes:
			for tagIndex in self.folder.tagIndexes:
				if self.cursorSide == 0 and tagIndex in displayRange:
					screen.blit(self.tagFrame, (97,(tagIndex-currentCursor.offset+2)*16))
		#draw cursor
		screen.blit(self.cursorImage, (hOffset-12-globalTimer%18//6, 16*(self.cursors[self.cursorSide].pos-self.cursors[self.cursorSide].offset)+35))
		
		#draw currentChip
		currentChip = currentFolder.chips[currentCursor.pos]
		if currentChip:
			screen.blit(currentChip.chipSurface,(8+150*self.cursorSide,17))
		#draw selected cursor
		if self.selectedIndex is not None and self.selectedSide == self.cursorSide and self.selectedIndex in displayRange:
			x = hOffset-8-globalTimer%18//6
			y = 16*(self.selectedIndex-self.cursors[self.selectedSide].offset)+35
			if globalTimer%2:
				screen.blit(self.cursorImage,(x,y))
	
			
	def tick(self):
		#scroll with buttons
		self.cursors[self.cursorSide].tick()
		
		if buttonDown[left]:
			self.scroll("left")
		elif buttonDown[right]:
			self.scroll("right")
		elif buttonDown[a]:
			self.select()
		elif buttonDown[b]:
			if self.selectedIndex == None:
				self.save()
				game.state = "TitleScreen"
			else:
				self.deselect()
		elif buttonDown[select]:
			if self.cursorSide == 0:
				self.folder.regIndex = self.cursors[self.cursorSide].pos

				
class ChipAttack():
	"""A chip to be held in the attack queue, to track damage and bonuses. will be converted into an AttackEntity on use"""
	def __init__(self, chip):
		self.Id, self.code = chip
		self.name, self.damage, self.element, self.status, codes, self.mb, self.description = chipData[self.Id]
		self.effects = []	#a list of effects to be added ex:setgreen 
		self.plusBonus = 0
		self.multiplier = 1
		
		self.chipWindow = self.getChipWindow()
		self.chipSurface = self.getChipSurface()
		self.icon = chipSprite = chipSpriteSheet.getSpriteById(self.Id,22,14,14,colorkey=None)
	
	def __str__(self):
		if self.Id<len(chipData):
			chipText = self.name
		else:
			chipText = "???"
		if self.damage>0:
			chipText += " "+str(self.damage)
		if self.plusBonus>0:
			chipText += "+"+str(self.plusBonus)
		if self.multiplier!=1:
			chipText += "x"+str(self.multiplier)
		return chipText
	
	def use(self, user):
		"""converts self into attackEntity and returns it"""
		#create AttackEntity corresponding to chip
		try:
			attackAlias, subId = attackData[self.Id]
			return attackAlias(user, self, subId)
		except KeyError:
			return None
			
			
	def mergeBonuses(self, chipAttack):
		self.plusBonus += chipAttack.plusBonus
		self.multiplier *= chipAttack.multiplier
		self.effects += chipAttack.effects			
				
	def getChipWindow(self):
		#return a surface with the image and data for a chip
		chipImageStrip = spritesheet("MMBN Assets/chip images.png").loadWholeStrip(rect=[0,0,56,48])
		elementStrip = spritesheet("MMBN Assets/elements.png").load_strip([0,0,14,14],9,colorkey=-1)
		chipWindow = Surface((66,66))
		chipWindow.set_colorkey((0,0,0))
		if self.Id < len(chipData):
			chipCodeText = monospaceFont.render(self.code,False,(255,255,0))
			self.damageText = monospaceFont.render(str(self.damage),False,(255,255,255))
			chipWindow.blit(chipCodeText,(1,53))
			chipWindow.blit(elementStrip[self.element],(15,51))
			if self.damage > 0:
				if self.damage >=100:
					chipWindow.blit(self.damageText,(43,53))
				else:
					chipWindow.blit(self.damageText,(50,53))
			if(self.Id<len(chipImageStrip)):
				chipWindow.blit(chipImageStrip[self.Id],(5,2))
		return chipWindow	

	def getChipSurface(self):
		battleChipSurface = Surface((80,134))
		battleChipSurface.set_colorkey((0,0,0))
		battleChipImage = pygame.image.load("MMBN Assets/Menus/battlechip.png")
		battleChipSurface.blit(battleChipImage,(0,0))
		battleChipSurface.blit(self.getChipWindow(),(7,2))
		for i, line in enumerate(self.description):
			lineText = monospaceFont.render(line,False,(1,1,1))
			battleChipSurface.blit(lineText,(8,70+i*16))
		return battleChipSurface
			
			
	def draw(self):
		"""draw chip for custom/folder"""
		NotImplemented

class Folder():
	"""represents the folder containing battle chips"""
	def __init__(self, chipList=[], regIndex=None, tagIndexes=None):
		"""initialize folder from list of chip Ids and codes"""
		self.chips = []
		self.discardedChips = []
		for chip in chipList:
			self.chips.append(ChipAttack(chip))
		self.regIndex = regIndex
		self.tagIndexes = tagIndexes
	
	def shuffle(self):
		regChip = None
		if self.regIndex is not None:
			regChip = self.chips.pop(self.regIndex)
			self.chips.insert(self.regIndex,None) #placeholder so indexes remain correct
		if self.tagIndexes:
			#get tag chips
			tagChips = []
			for index in self.tagIndexes:
				tagChips.append(self.chips[index])
			#treat tag chips as one chip
			self.chips[self.tagIndexes[0]] = "tag"	#this is where the tag chips will be inserted
			self.chips[self.tagIndexes[1]] = None	#placeholder to remove second chip
			
			
		shuffle(self.chips)
		if regChip:
			self.chips.insert(0,regChip)
			self.chips.remove(None) #remove placeholder
		if self.tagIndexes:
			#insert tag chips together
			tagLocation = self.chips.index("tag")
			for tagChip in tagChips:
				self.chips.insert(tagLocation, tagChip)
				tagLocation+=1
			self.chips.remove("tag")
			self.chips.remove(None) #remove placeholder
		#need to handle reg/tag chips
	
	def deal(self, dealAmount):
		"""return amount of chips and mark as discarded"""
		hand = []
		for i in range(dealAmount):
			if self.chips:
				hand.append(self.chips.pop(0))
			else:
				break
		return hand
			
	def __len__(self):
		return  len(self.chips)
		
	def __repr__(self):
		chipList = []
		for chip in self.chips:
			chipList.append(chip.Id, chip.code)
		return chipList

		
class AttackEntity(Expirable):
	"""	handles timing of attacks, created upon using an attack
		does not care about animation"""
	def __init__(self, user, chipAttack, endFrame):# damage, element, status, endFrame):
		#data from user
		self.user = user
		self.pos = user.pos[:] #want a copy of user's position
		
		#redundant data
		self.team = user.team
		self.status = chipAttack.status
		self.element = chipAttack.element
		#if chipAttack.status:
			#print("changing status to",chipAttack.status)
		#	self.status = chipAttack.status
		
		#data from chip
		self.chipAttack = chipAttack
		self.damage = (chipAttack.damage+chipAttack.plusBonus)*chipAttack.multiplier
		
		Expirable.__init__(self, endFrame)
		
	def hitTile(self,pos):
		NotImplementedError
		"""	hit tile at given position
			uses AttackEntity's damage, type, team, ect"""
		x,y = pos
		if x<0 or x>5 or y<0 or y>2:
			return False
		success = False
			
		
		#print("hitTile",pos)
		for entity in board.battleEntities:
			if entity.pos==pos and entity.team!=self.team:
				#print("hit",pos,"for",self.damage,"damage")
				entity.hit(self.damage, self.element, self.status)
				success = True
		#effects
		#if miss check tile element
		#if tile element is weak to attack set tile to null
		if typeEffectiveness(self.element,board.tileTypes[x][y])==2:
			#print("burnt tile",pos)
			board.tileTypes[x][y] = 0
		for effect in self.chipAttack.effects:
			if effect == "SetRed":
				board.tileTypes[x][y] = "volcano"
			elif effect == "SetBlue":
				board.tileTypes[x][y] = "ice"
			elif effect == "SetYellow":
				board.tileTypes[x][y] = "moveUp"
			elif effect == "SetGreen":
				board.tileTypes[x][y] = "grass"
		return success
				
	def shootRow(self, pos):
		NotImplementedError
		"""	shoots down row at pos
			shoots right if red team or left if blue team"""
		for entity in board.battleEntities:
			#not same team
			#in same row
			#right if red or left if blue
			if entity.team!=self.team and entity.pos[1]==pos[1] and ((self.team==1 and entity.pos[0]>pos[0]) or (self.team==2 and entity.pos[0]<pos[0])):
				#entity.hit(self.damage, self.element, self.status)
				self.hitTile(entity.pos)
				return
				
	def sliceWide(self, pos):
		NotImplementedError
		#print("slice wide on",pos)
		if self.team ==1:
			x = pos[0]+1
		elif self.team==2:
			x = pos[0]-1
		self.hitTile([x,pos[1]-1])
		self.hitTile([x,pos[1]])
		self.hitTile([x,pos[1]+1])
		
	def nearestEnemy(self, pos, maxRange):
		"""returns nearest enemy by column"""
		target = None
		if self.user.team==1:
			bestCol = 7
		elif self.user.team==2:
			bestCol = -1
		for entity in board.battleEntities:
			if entity.team==self.team or entity.team==0 or abs(self.pos[0]-entity.pos[0]>maxRange):
				continue
			if self.team==1:
				if entity.pos[0]<bestCol and entity.pos[0]>self.pos[0]: #target must be in front of player
					bestCol = entity.pos[0]
					target = entity					
			elif self.team==2 and entity.pos[0]<self.pos[0]:
				if entity.pos[0] > bestCol:
					bestCol = entity.pos[0]
					target = entity
		return target
	
class ShootAttack(AttackEntity):
	"""	a child of AttackEntity for shooting attacks, will call shootRow on shootFrame and will end on endFrame
		ToDo: get sprites and add a spriteSheet and extra data to select different sprites"""
	def __init__(self, user, chipAttack, subId):
		shootSubData = [[7, 9]]
		self.shootFrame, endFrame = shootSubData[subId]
		self.status = 0
		AttackEntity.__init__(self, user, chipAttack, endFrame)
		user.setStateSequence("shoot",[[0,1],[1,2],[2,2],[0,4]],startUp=5)
		user.moveLock = True
		
	def tick(self):
		#player should be immobile upon activating
		#print("shoot tick",self.frame)
		if self.frame == self.shootFrame:	#could have this factor in speed
			board.hitboxes.append(Bullet(self.pos, .5*self.user.facing, attack=self))
		if self.frame >= self.endFrame:
			#free player
			self.user.moveLock = False
			
		AttackEntity.tick(self)
		
class SwordAttack(AttackEntity):
	def __init__(self, user, chipAttack, subId):
		swordSubData = [[7, 1, 35],[7, 1, 35],[7, 1, 35],[7, 1, 35],[7, 1, 35]]
		self.shootFrame, self.status, endFrame = swordSubData[subId]
		AttackEntity.__init__(self, user, chipAttack, endFrame)
		user.moveLock = True
		x = user.pos[0]+self.user.facing
		y = user.pos[1]
		board.hitboxes.append(Hitbox([x,y], [1,3], 12, 6, attack=self))
		self.animation = AnimationEntity([x,y], "MMBN Assets/Attacks/widesword.png", [37,71], frameTimes=[6,4,3], facing=self.user.facing, offset=[-4,-16])
		user.setStateSequence("sword",[[0,14],[1,2],[2,2],[3,14]],startUp=5)
		
	def tick(self):
		#player should be immobile upon activating
		#print("sword tick",self.frame)
		#if self.frame == self.shootFrame:	#could have this factor in speed
		#	self.sliceWide(self.pos)
		if self.frame == 19:
			board.animations.append(self.animation)
		if self.frame >= self.endFrame:
			#free player
			self.user.moveLock = False
			
		super(SwordAttack, self).tick()
	
class MultiAttack(AttackEntity):
	"""	an attack entity that handles multihits
		creates an attack entity each interval for multiCount times"""
	def __init__(self, user, damage, element, status, multiCount, interval, attack):
		AttackEntity.__init__(self, user, multiCount*interval) #end time depends on number of hits
		
	def tick(self):
		if self.frame%interval == 0:
			#clone attack
			attackClone = None
			AttackEntities.append(attackClone)
		super(MultiAttack, self).tick()
			
class PhysicalAttack(AttackEntity):
	def __init__(self, user, chipAttack, subId):
		physicalSubData = [[1, 10]]
		self.distance, self.endFrame = physicalSubData[subId]
		self.status = 1
		AttackEntity.__init__(self, user, chipAttack, self.endFrame)
		
		if self.user.team == 2:
			self.distance *= -1
			
		self.speed = self.distance/self.endFrame
		self.user.moveLock = True
		self.pos[0] += self.distance
		board.hitboxes.append(Hitbox(self.pos,[1,1],self.endFrame/2,self.endFrame/2, attack=self))
		
	def tick(self):
		#move
		if self.frame < self.endFrame/2:
			#add to user's position
			#self.user.visualOffset[0] += self.speed
			NotImplemented
		#hit
		#if self.frame == self.endFrame/2:
			#if self.hitTile(self.pos):
			#	board.animations.append(Animation(self.pos,0,"tackle.png",[0,0,80,80],0,5))
		#move back
		if self.frame > self.endFrame/2:
			#add to user's position
			#self.user.visualOffset[0] -= self.speed
			NotImplemented
		if self.frame == self.endFrame:
			self.user.moveLock = False
		
		super(PhysicalAttack, self).tick()
				
class TargetAttack(AttackEntity):
	""" an attack that targets the nearest enemy"""
	def __init__(self, user, chipAttack, subId):
		targetSubData = [[18, 13, 3]]
		endFrame, self.hitFrame, self.maxRange = targetSubData[subId]
		AttackEntity.__init__(self, user, chipAttack, endFrame)
		
		#self.user.moveLock = True
		target = self.nearestEnemy(self.pos,self.maxRange)
		if target:
			hitPos = target.pos[:]
			board.hitboxes.append(Hitbox(hitPos, [1,1], self.hitFrame, endFrame-self.hitFrame, attack=self))
			board.animations.append(AnimationEntity(hitPos, "MMBN Assets/Attacks/lockon.png", [55,55], frameDuration=3))
		else:
			self.frame = self.endFrame
			self.user.moveLock = False
	
	def tick(self):
		if self.frame == self.hitFrame:
			#self.hitTile(self.pos)
			self.user.moveLock = False
		
		super(TargetAttack, self).tick()
		
class GuardAttack(AttackEntity):
	"""Shield then reflect"""
	def __init__(self, user, damage, element, status, endFrame, spriteFile, animationDelay):
		AttackEntity.__init__(self, user, damage, element, status, endFrame, spriteFile, [0,0,80,80], animationDelay, False)
		#give user invincibility and moveLock
		self.user.moveLock = True
		self.user.status = 1
		self.user.statusTimer = endFrame

	def tick(self):
		#check if hit
		#can't do this yet
		super(SampleAttack, self).tick()

class MovingTileAttack(AttackEntity):
	"""attack moves along tiles"""
	def __init__(self, user, chipAttack, subId):
		movingSubData = [[60, 8]]
		self.status = 1
		endFrame, self.moveDelay = movingSubData[subId]
		AttackEntity.__init__(self, user, chipAttack, endFrame)
		self.hitbox = MovingTileHitbox(self.pos, [1,0], self.moveDelay, attack=self)
		board.hitboxes.append(self.hitbox)
		user.setStateSequence("slide",[[0,14],[1,2],[2,2],[3,14]],startUp=5)
		
	def tick(self):
		#move every moveDelay frames
		if self.frame%self.moveDelay == 1 and self.hitbox.pos[0] in range(6) and self.hitbox.pos[1] in range(3):
			board.animations.append(AnimationEntity(self.hitbox.pos[:],"MMBN Assets/Attacks/shockwave.png",[50,44],facing=self.user.facing, offset=[-6,-17]))
			#if tile is broken quit
				#self.frame = self.endFrame
		super(MovingTileAttack, self).tick()
		
class ThrowAttack(AttackEntity):
	"""a projectile is thrown 3 squares ahead"""
	def __init__(self, user, damage, element, team, status, endFrame):
		AttackEntity.__init__(self, user, damage, element, team, status, endFrame)
	
	def tick(self):
		super(SampleAttack, self).tick()

class PursuitAttack(AttackEntity):
	"""entity chases nearest player"""
	def __init__(self, user, chipAttack, subId):
		AttackEntity.__init__(self, user, chipAttack, 1000)
		self.speed = 0.01
		self.hitbox = MovingHitbox(self.user.pos[:], [1,1], [self.speed,0], 1000, attack=self)
		board.hitboxes.append(self.hitbox)
		self.axis = 1
		self.status = 4
		
	def tick(self):
		#check rows/cols to decide to turn
		#if there's an enemy on the opposite axis turn towards enemy
		if self.frame*self.speed%1 == 0:
			for entity in board.battleEntities:
				if entity.team!=self.team and entity.pos[self.axis] == self.hitbox.pos[self.axis]:
					#change direction
					self.hitbox.speed[self.axis] = self.speed
					self.axis = -self.axis+1
					self.hitbox.speed[self.axis] = 0
				#reverse at edge of field
					
					
		super().tick()

class FrontTileAttack(AttackEntity):
	def __init__(self, user, chipAttack, subId):
		super().__init__(user, chipAttack, 1)
		oppositeTeam = [2,1][user.team-1]
		board.hitboxes.append(Hitbox(board.frontTile(user.pos[1], oppositeTeam), [1,3], 10, 4, attack=self))

class UTurnAttack(AttackEntity):
	def __init__(self, user, chipAttack, subId):
		super().__init__(user, chipAttack, 1)
		distances = [[2,1,2],[5,2,5]][subId]
		direction = [1,0][subId]
		pos = [[self.nearestEnemy(user.pos,5).pos[0],0],[0,2]][subId]
		speed = [.2,.25][subId]
		
		oppositeTeam = [2,1][user.team-1]
		board.hitboxes.append(UTurnHitbox(pos, [1,1], speed, direction, distances, False, attack=self))	#pos needs to be nearest enemy, not front row
		

class AnimationCounter():
	"""animation counter object
		frameDuration - length of each frame
		animationLength - total length of animation, will loop if longer than number of frames
		useGlobalTimer - if True will use global timer instead of self.frame
		frameTimes - will take an array for the duration of each frame in the animation
		frameSequence - list of each frame to use in order
	"""
	def __init__(self, numberOfFrames, frameDuration=1, animationLength=None, frameTimes=None, frameSequence=None):
		self.frameDuration = frameDuration
		self.frameSequence = frameSequence
				
		#create frameSequence from frameTimes
		if frameTimes:
			self.animationLength = 0
			self.frameSequence = []
			for i in range(len(frameTimes)):
				self.animationLength += frameTimes[i]
				for j in range(frameTimes[i]):
					self.frameSequence.append(i)
			#print(self.frameSequence)
			
		elif animationLength == None:
			self.animationLength = numberOfFrames*frameDuration
		
		
	def getImageIndex(self, frame):
		#returns what image of the animation should be displayed given a frame number
		currentFrame = frame%self.animationLength
		if self.frameSequence:
			imageIndex = self.frameSequence[currentFrame]
		else:
			imageIndex = currentFrame//self.frameDuration
		return imageIndex
	
class Animation(Expirable):
	"""Animation that uses an animation counter"""
	def __init__(self, spriteFile, size, frameDuration=1, animationLength=None, useGlobalTimer=False, facing=1, frameTimes=None, frameSequence=None, colorkey=-1):
		self.rect = Rect(0,0,size[0],size[1])
		self.useGlobalTimer = useGlobalTimer
		#load strip
		self.strip = spritesheet(spriteFile).loadWholeStrip(rect=self.rect, colorkey=colorkey)
		if facing == -1:
			for i in range(len(self.strip)):
				self.strip[i] = pygame.transform.flip(self.strip[i], True, False)
		
		self.counter = AnimationCounter(len(self.strip), frameDuration=frameDuration, animationLength=animationLength, frameTimes=frameTimes, frameSequence=frameSequence)
		super().__init__(self.counter.animationLength)
	
	def tick(self):
		super().tick()
		
	def getImage(self):
		if self.useGlobalTimer:
			timer = globalTimer
		else:
			timer = self.frame
		
		image = self.strip[self.counter.getImageIndex(timer)]
		return image
		
	def getRect(self):
		return self.rect

class AnimationEntity(Animation, DrawableEntity):
	def __init__(self, pos, spriteFile, size, frameDuration=1, animationLength=None, useGlobalTimer=False, facing=1, offset=[0,0], frameTimes=None, frameSequence=None, colorkey=-1):
		DrawableEntity.__init__(self, pos, offset)
		Animation.__init__(self, spriteFile, size, frameDuration, animationLength, useGlobalTimer, facing, frameTimes, frameSequence, colorkey)

	def draw(self):
		self.rect.center = self.getPixelCoords()
		screen.blit(self.getImage(), self.rect)
		
		
class Hitbox(Expirable):
	"""single instance of a hit that can last for multiple frames
		0 -> warning frames -> activeFrames
	"""
	def __init__(self,  pos, size, warningFrames, activeFrames, attack=None, damage=0, team=0, element=0, status=0):
		self.attack = attack
		self.pos = pos[:]
		self.size = size
		self.warningFrames = warningFrames
		self.activeFrames = activeFrames
		self.victims = [] #keep track of who's been hit
		
		
		self.updateCorners()
		
		self.tileSet = None 
		if attack:
			self.damage = attack.damage
			self.team = attack.team
			self.element = attack.element
			self.status = attack.status
			for effect in self.attack.chipAttack.effects:
				if effect == "SetRed":
					self.tileSet = "volcano"
					break
				elif effect == "SetBlue":
					self.tileSet = "ice"
					break
				elif effect == "SetYellow":
					self.tileSet = "moveUp"
					break
				elif effect == "SetGreen":
					self.tileSet = "grass"
					break
		else:
			self.damage = damage
			self.team = team
			self.element = element
			self.status = status
		
		
		self.image = pygame.image.load("MMBN Assets/Board/tile warning.png")
		self.image = pygame.transform.scale(self.image, (tileWidth*size[0],tileHeight*size[1]))
		super().__init__(warningFrames+activeFrames)
		
	def hit(self):
		for entity in board.battleEntities:
			entityX,entityY = entity.pos
			if entity not in self.victims and entity.team!=self.team and entityX>=self.x0 and entityX<self.x1 and entityY>=self.y0 and entityY<self.y1:
				entity.hit(self.damage, self.element, self.status)
				self.victims.append(entity)
		if self.frame == self.warningFrames: #on first active frame set tile
			self.setTile()
	
	def updateCorners(self):
		x,y = self.pos
		self.x0 = x-self.size[0]/2
		self.x1 = x+self.size[0]/2
		self.y0 = y-self.size[1]/2
		self.y1 = y+self.size[1]/2
					
	def setTile(self):
		#for each tile in range
		for i in range(int(math.ceil(self.x0)),int(math.floor(self.x1))+1):
			for j in range(int(math.ceil(self.y0)),int(math.floor(self.y1))+1):
				board.setTile(i, j, self.tileSet)
				board.burnTile(i, j, self.element)
		
	def draw(self):
		#board should probably be responsible for drawing hitboxes
		#draw flashing yellow box if in warning frames and solid yellow if in active frames
		x,y = self.pos
		if self.pos[1]>=0 and(self.frame > self.warningFrames or self.frame <= self.warningFrames and self.frame%8 < 4):
			X = tileWidth*(x-self.size[0]//2)
			Y = tileHeight*(y-self.size[1]//2)+boardOffset
			screen.blit(self.image,(X,Y))
			#print(X,Y)
			#screen.fill((255,255,0),rect=self.rect)
					
	def tick(self):
		if self.frame >= self.warningFrames and self.frame <= self.warningFrames+self.activeFrames:
			self.hit()
		super().tick()

class StealHitbox(Hitbox):
	"""hitbox that steals panels if it misses"""
	#don't need to override init
	def hit(self):
		#hit then steal panels except for misses
		Hitbox.hit(self)
		victimPositions = []
		for victim in self.victims:
			victimPositions.append(victim.pos)
		for otherEntity in board.otherEntities:
			victimPositions.append(otherEntity.pos)
		
		#for each tile in range	
		for i in range(int(math.ceil(self.x0)),int(math.floor(self.x1))+1):
			for j in range(int(math.ceil(self.y0)),int(math.floor(self.y1))+1):
				if [i,j] not in victimPositions:
					#also have to check for tileClaims
					#steal panel unless it's the last column
					if i!=0 and i!=5: 
						board.boardTeam[i][j] = self.team

class MultiHitbox(Hitbox):
	"""
		hitbox that can hit multiple times
			0 -> warningFrames -> {activeFrames -> delayBetweenHits -> activeFrames} * numberOfHits
	"""
	def __init__(self,  pos, size, warningFrames, activeFrames, numberOfHits, delayBetweenHits=0, attack=None, damage=0, team=0, element=0, status=0):
		Hitbox.__init__(self,  pos, size, warningFrames, activeFrames, attack=attack, damage=damage, team=team, element=element, status=status)
	
	def tick(self):
		#when new hit starts refresh victims
		if self.frame-self.warningFrames%self.activeFrames+self.delayBetweenHits == 0: #not sure about this
			self.victims = []
		Hitbox.tick(self)
	
class MovingTileHitbox(Hitbox):
	"""Hitbox that teleports between tiles rather than moving incrementally"""
	def __init__(self, pos, direction, delay,  attack=None, damage=0, team=0, element=0, status=0):
		Hitbox.__init__(self, pos, [1,1], 0, 18*delay, attack=attack, damage=damage, team=team, element=element, status=status)
		self.direction = direction[:] #relative position to move each frame
		if self.team == 2:
			self.direction[0] *= -1
		self.delay = delay
	
	def hit(self):
		if self.frame%self.delay == 0:
			self.setTile()
		Hitbox.hit(self)
	
	def tick(self):
		if self.frame%self.delay == 0:
			for i in range(2):
				self.pos[i] += self.direction[i]
			self.updateCorners()
			
		x,y = self.pos
		if x not in range(6) or y not in range(3):
			self.frame = self.endFrame
		
		Hitbox.tick(self)
	
class MovingHitbox(Hitbox):
	"""	Hitbox that moves incrementally each tick
		speed = [x,y] - distance in board units the hitbox moves each frame
	"""
	def __init__(self, pos, size, speed, activeFrames, attack=None, damage=0, team=0, element=0, status=0):
		Hitbox.__init__(self, pos, size, 0, activeFrames, attack=attack, damage=damage, team=team, element=element, status=status)
		self.speed = speed #distance to move each frame
		#if self.team == 2:
		#	self.speed[0]*=-1
		
	def tick(self):
		for i in range(2):
			self.pos[i] += self.speed[i]
		self.updateCorners()
		Hitbox.tick(self)

class UTurnHitbox(MovingHitbox):
	"""moving hitbox that turns
		NumberOfTurns redundant
		starting direction - up down left right? could be [1,0][0,1][-1,0][0,-1]
		clockwise/counterclockwise
		distances - [distance for number of turns]"""
	def __init__(self, pos, size, speed, direction, distances, clockwise, attack=None, damage=0, team=0, element=0, status=0):
		#calculate active frames
		self.directionSequence = [[1,0],[0,1],[-1,0],[0,-1]]
		self.direction = direction #index of directionSequence
		self.cumulativeDistances = []
		cumulativeDistance = 0
		for distance in distances:
			cumulativeDistance += distance
			self.cumulativeDistances.append(cumulativeDistance)
		print(self.cumulativeDistances)
			
		self.distances = distances
		self.clockwise = clockwise
		self.moveIndex = 0
		self.speedMagnitude = speed
		
		activeTime=0
		for distance in distances:
			activeTime += distance/speed
		print("active time = ",activeTime)
		super().__init__(pos, size, [speed*i for i in self.directionSequence[self.direction]], activeTime, attack=attack, damage=damage, team=team, element=element, status=status)
		
	def tick(self):
		#change direction once current distance has been reached
		currentDistance = self.distances[self.moveIndex]
		#rotate direction
		if self.frame*self.speedMagnitude >= self.cumulativeDistances[self.moveIndex]:
			self.moveIndex+=1
			print(self.frame)
			if self.clockwise:
				increment = 1
			else:
				increment = -1
			self.direction = (self.direction+increment)%4
			self.speed = [self.speedMagnitude*i for i in self.directionSequence[self.direction]]
			print("speed updated to",self.speed)
		super().tick()
		

class Bullet(MovingHitbox):
	"""A moving hitbox that stops after hitting it's first victim"""
	def __init__(self, pos, speed, attack=None, damage=0, team=0, element=0, status=0):
		MovingHitbox.__init__(self, pos, [1,1], [speed,0], 6/abs(speed), attack=attack, damage=damage, team=team, element=element, status=status)
		
	def tick(self):
		if self.victims:	#end if something has been hit
			self.frame = self.endFrame
			return
		super().tick()
		
		
class TimeFreezeAttack(AttackEntity):
	def __init__(self, user, chipAttack, endFrame):
		AttackEntity.__init__(self, user, chipAttack, endFrame)
		self.nameText = monospaceFont.render(str(self.chipAttack),False,(0,0,0))
		self.hitboxes = [] #keep track of hitboxes instead of board
	
	def tick(self):
		#tick hitboxes
		for hitbox in self.hitboxes:
			hitbox.tick()
			hitbox.draw()
		super().tick()
				
class StageChange(TimeFreezeAttack):
	def __init__(self, user, chipAttack, subId):
		TimeFreezeAttack.__init__(self, user, chipAttack, 90)
		tile = ["volcano", "ice", "moveUp", "grass"]
		
		self.subId = subId
		#make a new board with all tiles set to subId value
		self.oldBoardTypes = board.tileTypes[:]
		self.newBoardTypes = [[tile[subId-1] for i in range(3)] for j in range(6)]
		
	def tick(self):
		#flash new and old tiles for a few frames
		if self.frame%8<4:
			board.tileTypes = self.newBoardTypes
		else:
			board.tileTypes = self.oldBoardTypes
		TimeFreezeAttack.tick(self)

class SummonAttack(TimeFreezeAttack):
	def __init__(self, user, chipAttack, objectId):
		objects = ["rockcube"]
		destination = user.pos[:]
		destination[0] += user.facing
		self.obstacle = BattleEntity(destination, 0, 0, name=objects[objectId], size=[30,37], offset=[0,-12], statusEnabled=False, maxHp=200)
		TimeFreezeAttack.__init__(self, user, chipAttack, 90)
		
	def tick(self):
		if self.frame == 30:
			board.battleEntities.append(self.obstacle) #ToDo: check for collisions
		super().tick()

class DoubleSummon(TimeFreezeAttack):
	def __init__(self, user, chipAttack, objectId):
		objects = ["rockcube"]
		destinations = [None,None]
		if user.pos == [2,1]:
			destinations[0] = [1,1]
		else:
			destinations[0] = user.pos[:]
			destinations[0][0] += user.facing
		destinations[1] = [-destinations[0][0]+5,-destinations[0][1]+2]
		self.obstacles = [BattleEntity(destinations[i], 0, 0, name=objects[objectId], size=[30,37], offset=[0,-12], statusEnabled=False, maxHp=200) for i in range(2)]
		TimeFreezeAttack.__init__(self, user, chipAttack, 90)
		
	def tick(self):
		if self.frame == 20:
			for obstacle in self.obstacles:
				board.battleEntities.append(obstacle) #ToDo: check for collisions
		super().tick()

class StealAttack(TimeFreezeAttack):
	def __init__(self, user, chipAttack, subId):
		startup = 10
		activeFrames = 1
		super().__init__(user, chipAttack, startup+activeFrames)
		oppositeTeam = [2,1][user.team-1]
		#ToDo: add animations
		if subId == 0:
			#PanlGrab - 1x1 hitbox on front tile
			self.hitboxes.append(StealHitbox(board.frontTile(user.pos[1], oppositeTeam), [1,1], startup, activeFrames, attack=self))
		elif subId == 1:
			#AreaGrab - 1x3 hitbox on front row
			self.hitboxes.append(StealHitbox([board.frontRow(oppositeTeam),1], [1,3], startup, activeFrames, attack=self))
	


def greySurface(surface):
	surface.lock()
	arr = PixelArray(surface)
	arr.replace((232,216,128),(183,183,183))
	surface.unlock()
	
def unGreySurface(surface):
	surface.lock()
	arr = PixelArray(surface)
	arr.replace((183,183,183),(232,216,128))
	surface.unlock()

			
def typeEffectiveness(attackElement, defendElement):
	#print(attackElement,"->",defendElement)
	if attackElement == 0:
		return 1
	attackRing = (attackElement-1)//4
	defendRing = (defendElement-1)//4
	if attackRing==defendRing:
		if attackElement == defendElement+1 or attackElement== defendElement-3:
			return 2
	return 1

	
def load():
	try:
		saveFile = open("Data/save.txt", "r")
		loadData = json.load(saveFile)
	except:
		print("error with saveFile")
		try:
			loadData = json.load(open("Data/DefaultSave.txt","r"))
		except:
			print("error loading default save")
			loadData = [[0,"*"] for i in range(30)]+[None,None], 7, ["discard","restock","recycle"]
	[chipList,regIndex,tagIndexes], drawAmount, extraMode = loadData
	return Folder(chipList, regIndex, tagIndexes), drawAmount, extraMode
		
def save(folder, customDraw, extraMode):
	#save folder, custom draw amount, extra button,
	chipIdList = []
	for chip in folder.chips:
		chipIdList.append([chip.Id,chip.code])
	saveFile = open("Data/save.txt", "w")
	json.dump([[chipIdList,folder.regIndex,folder.tagIndexes],customDraw,extraMode], saveFile)

	
def processAttackQueue(attackQueue):
	newAttackQueue = []
	for attack in attackQueue:
		if newAttackQueue:
			bottomChip = newAttackQueue[0]
			if attack.Id == 9 and newAttackQueue and bottomChip.damage>0: #add atk+10 to chips that can deal damage
				#print("found attack+")
				bottomChip.plusBonus += 10
			elif attack.Id>= 10 and attack.Id<14 and newAttackQueue and bottomChip.damage>0 and (bottomChip.element==0 or bottomChip.element==attack.Id-9): #+status to damaging null or same element chip
				bottomChip.status = attack.Id-8
			elif attack.Id in range(14,18) and newAttackQueue and bottomChip.damage>0 and (bottomChip.element==0 or bottomChip.element==attack.Id-13): #attach setColor to damaging null or same element chip
				effectNames = ["SetRed","SetBlue","SetYellow","SetGreen"]
				bottomChip.effects.append(effectNames[attack.Id-14])
			else:
				newAttackQueue.insert(0,attack)
		else:
			newAttackQueue.insert(0,attack)
	return newAttackQueue


#game
attackData = {
	0:[ShootAttack, 0], 
	1:[SwordAttack, 0], 
	2:[PhysicalAttack, 0], 
	3:[TargetAttack, 0], 
	4:[MovingTileAttack, 0], 
	5:[SwordAttack, 1], 
	6:[SwordAttack, 2], 
	7:[SwordAttack, 3], 
	8:[SwordAttack, 4], 
	14:[StageChange, 1],
	15:[StageChange, 2], 
	16:[StageChange, 3], 
	17:[StageChange, 4], 
	18:[SummonAttack, 0], 
	19:[DoubleSummon, 0], 
	20:[StealAttack, 0], 
	21:[StealAttack, 1], 
	22:[FrontTileAttack, 0],
	23:[UTurnAttack, 0],
	24:[UTurnAttack, 1]
}
folder = load()
game = Game()

#custom
player = None
board = None
custom = None
editor = None

buttonHeld = {up:False, down:False, left:False, right:False, a:False, b:False, r:False, l:False, start:False, select:False, debugPause:False, debugNextFrame:False}
buttonDown = dict(buttonHeld)
buttonInput = dict(buttonHeld)


globalTimer = 0


debugPaused = False
while True:
	frameStartTime = datetime.now()
	
	for event in pygame.event.get():
		if event.type == pygame.QUIT: 
			sys.exit()
		if event.type == pygame.KEYUP:
			buttonHeld[event.key] = False
		if event.type == pygame.KEYDOWN:
			buttonHeld[event.key] = True
			buttonDown[event.key] = True
	#merge button inputs
	for i in buttonHeld:
		buttonInput[i] = buttonHeld[i] or buttonDown[i]
	if buttonDown[debugPause]:
		debugPaused = not debugPaused
	
	if not debugPaused or debugPaused and buttonDown[debugNextFrame]:
		screen = Surface(screenSize)
		screen.fill((0,0,0))
		game.tick()
		globalTimer += 1
		
		screen = pygame.transform.scale(screen, (width*scale,height*scale))
	realScreen.blit(screen,(0,0))
	
	for i in buttonDown:
		buttonDown[i] = False
	end = datetime.now()
	exec_time = end - frameStartTime
	sleepTime = 1/60-exec_time.total_seconds()
	
	
	pygame.display.flip()
	if(sleepTime>0):
		time.sleep(sleepTime)
		
		
    
