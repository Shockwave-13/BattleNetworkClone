import sys, pygame
import json
from spritesheet import spritesheet
from pygame.locals import *
from pygame import Rect
from random import randint, shuffle
from datetime import datetime
import time
from pygame import PixelArray

pygame.init()
pygame.display.set_caption("Pokemon Battle Network")

#global resources
tileWidth = 80
tileHeight = 40
size = width, height = tileWidth*6, tileHeight*5
screen = pygame.display.set_mode(size)

elements = ["null","fire","aqua","elec","wood","break","cursor","wind","sword"]
			#[name, damage, element, status, codes]
chipData = [["Air Shot", 10, 7, 0, ["*"]],["WideSwrd",10,8, 1, ["B"]],["Tackle",10,5, 1, ["B"]],["Target Shot",10,6, 1, ["A"]],["Shockwave",10,0, 1, ["A","B"]],["FireSword",10,1,1,["A"]],["AquaSword",10,2,1,["B"]],["ElecSword",10,3,1,["A"]],["BambSword",10,4,1,["B"]],["atk+10",0,0,0,["*"]],["+burn",0,0,2,["*"]],["+freeze",0,0,3,["*"]],["+paralyze",0,0,4,["*"]],["+ensare",0,0,5,["*"]],["SetRed",0,0,0,["*"]],["SetBlue",0,0,0,["*"]],["SetYellow",0,0,0,["*"]],["SetGreen",0,0,0,["*"]]]
	
pokemonSpriteSheet = spritesheet("diamond-pearl.png")
chipSpriteSheet = spritesheet("chip icons.png")
background = pygame.image.load("background.png")
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


class Tickable():
	"""Interface for ticking objects"""
	def __init__(self):
		self.frame = 0

	def tick(self):
		self.frame += 1
		
class Expirable(Tickable):
	"""Interface for ticking objects that expire
		endFrame indicates what frame it can be removed on"""
	def __init__(self, endFrame):
		super().__init__()
		self.endFrame = endFrame
		

		
class pokemon():	
	def __init__(self, Id, level):
		self.Id = Id
		self.level = level
		self.IVs = [randint(0,31) for i in range(6)]
		self.nature = randint(0,24)
		self.EVs = [0 for i in range(6)]
		self.baseStats = [85,120,70,50,50,100] #staraptor's stats, need to get per species
		self.calculateStats()
		self.getSprite()
		
	def __str__(self):
		return pokemonNames[self.Id]
		
	def calculateStats(self):
		self.totalStats = [0,0,0,0,0,0]
		self.totalStats[0] = ((2*self.baseStats[0]+self.IVs[0]+self.EVs[0]//4)*self.level)//100+self.level+10
		for i in range(1,6):
			self.totalStats[i] = ((2*self.baseStats[i]+self.IVs[i]+self.EVs[i]//4)*self.level)//100+5#*natureBonus
		
	def getSprite(self):
		self.image = pokemonSpriteSheet.getSpriteById(self.Id-1, 28, tileWidth, tileWidth)
		self.rect = self.image.get_rect()

class Entity():
	"""an object that can occupy a tile on the board"""
	def __init__(self, pos):
		self.pos = pos

class TileClaim(Entity, Expirable):
	"""claims a tile for an entity to move to"""
	def __init__(self, pos, entity, endFrame):
		self.entity = entity
		Entity.__init__(self, pos)
		Expirable.__init__(self, endFrame)
		
	def tick(self):
		if self.frame == self.endFrame-1:
			self.entity.pos = self.pos
		Expirable.tick(self)
		

class PokemonEntity(Entity):
	"""an Entity that is also a pokemon that can move, be hit, be affected by status ect"""
	def __init__(self, pos, team, element):
		Entity.__init__(self,pos)
		self.team = team
		self.moveLock = False
		self.status = 0
		self.statusTimer = 0
		self.element = element #normal, fire, aqua, elec, wood, break, cursor, wind, sword
		self.visualOffset = [0,0]
		self.image = None
		self.rect = None
		self.moveCooldown = 0
		
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
			if not self.moveLock and self.moveCooldown==0 and (self.statusTimer==0 or self.status<=2):
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
						board.otherEntities.append(TileClaim([x,y],self,7))
						#self.pos = [x,y]
						self.moveCooldown = 11
			
	def hit(self, damage, element, status):
		if self.status==1 and self.statusTimer>0: #if flinched don't get hit
			return
		effectiveness = typeEffectiveness(element,self.element)
		#status bonus
		if self.statusTimer>0 and self.status>1:
			if (self.status, element) in [(2,7),(3,5),(4,6),(5,8)]:
				#double damage and end status
				effectiveness*=2
				self.statusTimer = 0
		#tile bonus
		x,y = self.pos
		if typeEffectiveness(element,board.tileTypes[x][y])==2:
			effectiveness *= 2
			board.tileTypes[x][y] = 0
					
		if effectiveness==2:
			board.animations.append(Animation(self.pos,0,"super effective.png",[0,0,48,48],0,4))
		elif effectiveness==4:
			board.animations.append(Animation(self.pos,0,"super effective.png",[0,48,48,48],0,4))
		#print("dealt",damage*effectiveness)
		self.damage(damage*effectiveness)
		
		if status==1: #flinch
			self.status = 1
			self.statusTimer = 120
		if status>1 and self.statusTimer==0:
			#if you don't resist status type
			self.status = status
			#more time if you are weak to status type?
			self.statusTimer = 90
					
	def damage(self, damage):
		NotImplemented
		
	def draw(self):
		if self.image and self.rect:
			moveOffset = abs(self.moveCooldown-5)+5
			X = (self.pos[0]+self.visualOffset[0])*tileWidth+tileHeight
			Y = (self.pos[1]+self.visualOffset[1])*tileHeight+tileWidth+moveOffset
			self.rect.center = X,Y
			
			if not(self.status==1 and self.statusTimer%4>1): #don't draw every 2 frames if flinched
				screen.blit(self.image, self.rect)
				
			if self.status>1 and self.statusTimer>0:
				#draw status effect
				statusStrip = statusStrips[self.status-2]
				statusFrame = (60-self.statusTimer)%len(statusStrip)-1
				screen.blit(statusStrip[statusFrame], self.rect)
							
	def tick(self):
		if self.statusTimer>0:
			if self.status==2 and self.statusTimer%12==0: #burn damage over time
				self.hit(1,1,0)
			self.statusTimer -= 1
		x,y = self.pos
		if self.moveCooldown>0:
			self.moveCooldown -= 1

class Navi(PokemonEntity):
	"""a Pokemon Entity that can hold chips"""
	def __init__(self, pos, team, element):
		PokemonEntity.__init__(self, pos, team, element)
		self.pokemon = pokemon(randint(1,493),randint(1,15))
		self.image = self.pokemon.image
		self.rect = self.pokemon.rect
		if self.team==1:
			self.image = pygame.transform.flip(self.image,True,False)
		self.healCooldown = 0
		self.attackQueue = []
		
	def damage(self, damage):
		self.pokemon.totalStats[0] -= damage
	
	def useChip(self):
		if not self.moveLock:
			if self.attackQueue:				
				attack = self.attackQueue.pop()
				board.addAttack(attack.use(self))
	
	def draw(self):
		PokemonEntity.draw(self)
		HpTextShadow = monospaceFont.render(str(self.pokemon.totalStats[0]), False, (0,0,0))
		HpText = monospaceFont.render(str(self.pokemon.totalStats[0]), False, (255,255,255))
		X = self.pos[0]*tileWidth+tileHeight-10
		Y = self.pos[1]*tileHeight+tileWidth+25
		if self.pokemon.totalStats[0]>0:
			screen.blit(HpTextShadow,(X+1, Y+1))
			screen.blit(HpText,(X,Y))
		offset = len(self.attackQueue)*2
		for attack in self.attackQueue:
			#draw attack relative to player
			chipSprite = chipSpriteSheet.getSpriteById(attack.Id,20,16,16,colorkey=0)
			chipRect = chipSprite.get_rect()
			chipRect.center = self.pos[0]*tileWidth+tileWidth/2-offset, self.pos[1]*tileHeight+tileHeight-offset
			screen.blit(chipSprite,chipRect)
			offset-=2
	
	def tick(self):
		PokemonEntity.tick(self)
		x,y = self.pos
		if board.tileTypes[x][y]==self.element and self.healCooldown==0:
			self.pokemon.totalStats[0]+=1
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
			currentChipText = monospaceFont.render(str(topChip),False,(0,0,0))
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
		if buttonInput[r] or buttonInput[l]:
			if board.frameCount >= board.turnFrames:
				#print("enter custom")
				game.state = "Custom"
				board.frameCount = 0
				
class Enemy(Navi):
	def __init__(self, pos, element):
		Navi.__init__(self, pos, 2, element)
		
	def tick(self):
		Navi.tick(self)
		if randint(0,40)==0:
			moves = ["left","right","up","down"]
			self.moveDirection(moves[randint(0,3)])
		elif randint(0,90)==0:
			self.useChip()
					
class SandBag(PokemonEntity):
	def __init__(self, pos, team):
		PokemonEntity.__init__(self, pos, team, 0)
		self.totalDamage = 0
		self.image = pygame.image.load("sandbag.png")
		self.rect = self.image.get_rect()
		
	def damage(self, damage):
		self.totalDamage += damage
		
	def draw(self):
		PokemonEntity.draw(self)
		damageText = monospaceFont.render(str(self.totalDamage),False,(0,0,0))
		X = self.pos[0]*tileWidth+tileHeight-10
		Y = self.pos[1]*tileHeight+tileWidth+25
		screen.blit(damageText,(X,Y))


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
		try:
			folder, customDraw, extraMode, = load()
		except:
			folder = defaultFolder
			customDraw = 5
			extraMode = []
		if mode == "sandbag":
			custom = Custom(folder, 10, extraMode)
			custom.refresh() 
			board = Board([player,SandBag([4,1],0)])
		else:
			custom = Custom(folder, customDraw, extraMode)
			shuffle(custom.folder)
			custom.refresh()
			board = Board([player, Enemy([4,1],randint(0,9)),Enemy([5,1],randint(0,9)),Enemy([5,2],randint(0,9))])
		
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
		self.title = pygame.image.load("title.png")
		self.title2 = pygame.image.load("title2.png")
		
	def draw(self):
		#draw title
		screen.blit(self.title,(0,0))
		screen.blit(self.title2,(240 ,0))
		#draw options
		options = ["Random Battle","Sandbag Practice","Folder Edit"]
		for i in range(3):
			screen.blit(monospaceFont.render(options[i], False, (255,255,255)), (width/2, height*.6+10*i))
		#draw cursor
			screen.blit(monospaceFont.render(">", False, (255,255,255)), (width/2-16, height*.6+10*self.cursor.pos))
				
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
				try:
					folder, customDraw, extraMode = load()
				except:
					folder = defaultFolder
				editor = Editor(folder)
				game.state = "Folder"
		
		

class Board():
	"""class to hold tiles and entities of a battle"""
	def __init__(self, entities):
		self.pokemonEntities = entities
		self.attackEntities = []
		self.hitBoxes = []
		self.animations = []
		self.otherEntities = []
		self.boardTeam = [[1,1,1],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[2,2,2]] #each row of board 0 = neutral, 1 = red, 2 = blue
		self.tileTypes = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
		self.turnFrames = 128
		self.timeFreeze = False
		self.timeFreezeStartup = 0
		self.activeTimeFreezeAttack = None
		
		#resources for drawing
		self.customGauge = pygame.image.load("custom guage.png")
		self.customRect = Rect(0,0,width,height)
		self.frameCount = 0
		self.tileBorderStrip = spritesheet("tile borders.png").load_strip([0,0,80,40],3,colorkey=[0,0,0,255])
		self.tileStrip = spritesheet("tiles.png").load_strip([0,0,80,40],5,colorkey=-1)
		self.tileRects = []
		self.tileBorderRects = []
		for i in range(6):
			self.tileRects.append([Rect(i*tileWidth,j*tileHeight+tileWidth,tileWidth,tileHeight) for j in range(3)])
			self.tileBorderRects.append([Rect(i*tileWidth,j*tileHeight+tileWidth,tileWidth,tileHeight) for j in range(3)])
	
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
		for entity in self.pokemonEntities+self.otherEntities:
			if entity.pos == pos:
				return True
		return False
	
	def draw(self):
		screen.blit(background, backgroundRect)
		#draw board tiles
		for i in range(6):
			for j in range(3):
				screen.blit(self.tileBorderStrip[self.boardTeam[i][j]], self.tileBorderRects[i][j])
				screen.blit(self.tileStrip[self.tileTypes[i][j]], self.tileRects[i][j])
		
		#draw hitboxes
		if not self.timeFreeze:
			for hitBox in self.hitBoxes:
				#if hitBox.team!=1:
				hitBox.draw()
			
				
		#sort entities from back to front for drawing
		self.pokemonEntities.sort(key=lambda x: x.pos[1])
		for entity in self.pokemonEntities:	#draw all entities
			entity.draw()				
				
		for animation in self.animations:
			screen.blit(animation.getImage(),animation.getRect())
			
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
			for entity in self.pokemonEntities:
				entity.tick()
				if isinstance(entity, Navi) and entity.pokemon.totalStats[0]<= 0:
					self.pokemonEntities.remove(entity)
				
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
				if animation.animationTimer >= animation.endFrame:
					self.animations.remove(animation)
		
			hasEnemies = False
			hasPlayer = False
			for entity in self.pokemonEntities:
				if isinstance(entity, Enemy):
					hasEnemies = True
				elif isinstance(entity, Player):
					hasPlayer = True
				elif isinstance(entity, SandBag):
					hasEnemies = True
			if not hasPlayer or not hasEnemies:
				game.endBattle()
				
			for hitbox in self.hitBoxes:
				hitbox.tick()
				if hitbox.frame >= hitbox.activeFrames+hitbox.warningFrames:
					self.hitBoxes.remove(hitbox)
						
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
				self.timeFreeze = False
				self.activeTimeFreezeAttack = None
			else:
				self.activeTimeFreezeAttack.draw()
				self.activeTimeFreezeAttack.tick()
		
		
class Custom():
	""""handles the data for the custom window"""
	def __init__(self, folder, customDraw, extraMode):
		self.folder = folder[:]
		self.customDraw = customDraw
		self.cursor = CustomCursor(customDraw)
		self.hand = []
		self.selectedChips = []
		self.extraMode = extraMode
		self.extraUsed = False
		self.counter = 0
		
		#shuffle(self.folder)
		#self.refresh()
		
		#resources for drawing
		self.cursorRect = Rect(0,0,18,18)
		self.cursorSprites = spritesheet("custom cursor.png").load_strip(self.cursorRect,2,colorkey=-1)
		self.customWindow = pygame.image.load("custom frame.png")
		self.customWindowRect = self.customWindow.get_rect()
		self.chipImageStrip = spritesheet("chip images.png").load_strip([0,0,56,48],10)
		self.elementStrip = spritesheet("elements.png").load_strip([0,0,14,14],9,colorkey=-1)
		
		extraButtonStrip = spritesheet("extra buttons.png").load_strip((0,0,24,16),10)
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
		for i in range(drawAmount):
			if self.folder:
				self.hand.append(self.folder.pop(0))
			else:
				break	
		self.selectedCode = None
		self.selectedID = None
		self.selectedChips = []
		self.selected = [False for i in range(self.customDraw)]
		self.handSprites = [chipSpriteSheet.getSpriteById(chip[0],20,16,16,colorkey=0) for chip in self.hand]
		self.handRects = [handSprite.get_rect() for handSprite in self.handSprites]

	def select(self):
		"""selects the chip at the current cursor position and adds it to selectedChips
			returns selectedChips if user selects OK"""
		#close custom
		if self.cursor.pos==-1:
			#load selectedChips attacks into attackQueue
			attackQueue = []
			
			for selectedChip in self.selectedChips:
				attackQueue.append(ChipAttack(self.hand[selectedChip]))
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
			if self.extraUsed:
				return
			self.extraUsed = True
			if "discard" in self.extraMode:
				#discard chips
				newHand = []
				removedChips = []
				for i in range(len(self.hand)):
					if not self.selected[i]:
						newHand.append(self.hand[i])
					else:
						removedChips.append(self.hand[i])
				if "recycle" in self.extraMode:
					self.folder += removedChips
					
				self.hand = newHand
				self.selectedChips = []
				self.selected = [False for i in range(len(self.hand))]
				self.selectedCode = None
				self.selectedID = None
				
				if "restock" in self.extraMode:
					self.refillHand()
					
			elif "shuffle" in self.extraMode:
				#shuffle all chips that aren't selected
				#remove all unselected chips
				unselectedChips = [self.hand[i] for i in range(len(self.hand)) if not self.selected[i]]
				#print("unselected:",unselectedChips)
				#add unselected chips to folder
				self.folder = self.folder + unselectedChips
				#print("folder:",self.folder)
				#shuffle folder
				shuffle(self.folder)
				#restock
				for i in range(len(self.hand)):
					if not self.selected[i]:
						self.hand[i] = self.folder.pop()
			#update sprites
			self.handSprites = [chipSpriteSheet.getSpriteById(chip[0],20,16,16,colorkey=0) for chip in self.hand]
			self.handRects = [handSprite.get_rect() for handSprite in self.handSprites]
			
		elif self.cursor.pos>=0 and self.cursor.pos<len(self.hand):
			chipID,chipCode = self.hand[self.cursor.pos]
			if len(self.selectedChips)<5 and not self.selected[self.cursor.pos] and (self.selectedCode==None or self.selectedCode==chipCode or self.selectedID==chipID or (self.selectedCode!=-1 and chipCode=="*")):
				self.selectedChips.append(self.cursor.pos) #select chip by adding it's cursor pos to self.selectedChips
				self.selected[self.cursor.pos] = True
				self.selectCode(chipID,chipCode)
		return None
			
	def deselect(self):
		"""deselects the last chip selected"""
		if len(self.selectedChips) > 0:
			self.selected[self.selectedChips.pop()] = False #pop and deselect chip
			#search selected chips to update selectedCode and selectedID
			#tempCode = None
			#tempID = None
			
			#run through selected chips again
			self.selectedCode = None
			self.selectedID = None
			for chipLocation in self.selectedChips:
				chipID,chipCode = self.hand[chipLocation]
				self.selectCode(chipID,chipCode)
				#if hand[chipLocation][1] != None and hand[chipLocation][1]!="*":
					#tempCode = hand[chipLocation][1]
					#break
			#selectedCode = tempCode
		
	def selectCode(self, chipID, chipCode):
		if self.selectedID==None:
			self.selectedID = chipID
		elif self.selectedID!=chipID:
			self.selectedID = -1
		
		if self.selectedCode==None and chipCode!="*":
			self.selectedCode = chipCode
		elif self.selectedCode!=chipCode and chipCode!="*":
			self.selectedCode = -1
		
		#print(self.selectedCode,self.selectedID)
		
	def draw(self):
		board.draw()
		screen.blit(self.customWindow, self.customWindowRect)
		#draw extra button
		if self.extraButtons:
			if self.extraUsed:
				screen.blit(self.extraButtons[1],(95,136,24,16))
			else:
				screen.blit(self.extraButtons[0],(95,136,24,16))
		#draw each chip
		if custom.hand:
			for i in range(len(self.hand)):
				self.handRects[i].left = i%5*17+11
				self.handRects[i].top = i//5*28+108
				
			for i in range(len(self.hand)):
				chipID, chipCode = self.hand[i]
				if not self.selected[i]:
					#if not selectable grey out
					if len(self.selectedChips)<5 and (self.selectedCode==None or self.selectedCode==chipCode or self.selectedID==chipID or (self.selectedCode!=-1 and chipCode=="*")):
						unGreySurface(self.handSprites[i])
					else:
						greySurface(self.handSprites[i])
						
					screen.blit(self.handSprites[i],self.handRects[i])
				
				code = codeFont.render(self.hand[i][1], False, (255,255,0))
				screen.blit(code,(self.handRects[i].left+4,self.handRects[i].top+15))
				
			#draw details of current chip
			
			if self.cursor.pos<0:
				chipID = len(self.chipImageStrip)-1
			else:
				currentChip = chipID,chipCode= self.hand[self.cursor.pos]
				chipName, chipDamage, chipElement, status, codes = chipData[chipID]
				chipNameText = monospaceFont.render(chipName,False,(255,255,255))
				chipCodeText = monospaceFont.render(chipCode,False,(255,255,0))
				chipDamageText = monospaceFont.render(str(chipDamage),False,(255,255,255))
				screen.blit(chipNameText,(15,17))
				screen.blit(chipCodeText,(15,89))
				screen.blit(self.elementStrip[chipElement],(25,89))
				if chipDamage > 0:
					screen.blit(chipDamageText,(69,89))
			if(chipID<len(self.chipImageStrip)):
				screen.blit(self.chipImageStrip[chipID],(15,29))
			
			#draw selectedChips chips
			pos = 0
			for chip in self.selectedChips:
				chipSprite = self.handSprites[chip]
				chipRect = self.handRects[chip]
				chipRect.left = 103
				chipRect.top = pos*17+17
				screen.blit(chipSprite,chipRect)
				pos += 1
			
		#draw cursor
		if self.cursor.pos<0:
			#replace this with a special cursor to fit OK button
			self.cursorRect.left = 95
			self.cursorRect.top = 79-28*self.cursor.pos
		else:
			self.cursorRect.left = self.cursor.pos%5*17+10
			self.cursorRect.top = self.cursor.pos//5*28+107
		screen.blit(self.cursorSprites[custom.counter//8], self.cursorRect)
		
	def tick(self):
		self.cursor.tick()
		if buttonDown[start]:
			self.cursor.pos = -1
		if buttonDown[a]:
			selectedAttacks = self.select()			
			if selectedAttacks!=None:	#OK is pressed
				if selectedAttacks:	#don't overwrite if no attacks selected
					player.attackQueue = selectedAttacks
				for enemy in board.pokemonEntities:
					if isinstance(enemy, Enemy):
						chipCount = randint(0,5)
						if chipCount > 0:
							enemy.attackQueue = []
							for i in range(chipCount):
								enemy.attackQueue.append(ChipAttack([0,"*"]))
							enemy.attackQueue = processAttackQueue(enemy.attackQueue)
				game.state = "Battle"
		if buttonDown[b]:
			self.deselect()
		
		self.counter+=1
		if self.counter >= 16:
			self.counter = 0
		
		
class Editor():
	"""stores data for folder editing menu"""
	def __init__(self, folder):
		#folder
		self.folder = folder[:]
		while len(self.folder)<30:
			self.folder.append(None)
		
		#pack
		#fill pack with all chips
		self.allChips = []
		for i in range(len(chipData)):
			for code in chipData[i][4]:
				self.allChips.append([i,code])
		
		self.rows = 7
		self.cursors = [ScreenScrollCursor(30,self.rows),ScreenScrollCursor(len(self.allChips),self.rows)]
		self.cursorSide = 0	#folder/pack 
		self.selectedSide = None
		self.selectedIndex = None
		
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
					self.folder[self.selectedIndex] = None
				else:
					#replace first empty chip in folder
					try:
						self.folder[self.folder.index(None)] = self.allChips[self.selectedIndex]
					except:
						NotImplemented
			#left(selected) to right (remove)
			elif self.selectedSide == 0 and self.cursorSide == 1:
				self.folder[self.selectedIndex] = self.allChips[currentIndex]
			#right to left
			elif self.selectedSide == 1 and self.cursorSide == 0:
				self.folder[currentIndex] = self.allChips[self.selectedIndex]
			#left to left
			elif self.selectedSide == 0 and self.cursorSide == 0:
				#swap
				a = self.folder[currentIndex]
				b = self.folder[self.selectedIndex]
				self.folder[currentIndex] = b
				self.folder[self.selectedIndex] = a
			
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
		if None not in self.folder:
			save(self.folder, 7, ["discard","restock","recycle"])
	
	def draw(self):
		screen.blit(background,backgroundRect)
		
		#draw folder and pack
		j = 0
		for currentFolder in [self.folder, self.allChips]:
			for i in range(self.cursors[j].offset, self.cursors[j].offset+self.rows):
				if i < len(currentFolder) and currentFolder[i] != None:
					chipId, chipCode = currentFolder[i]
					chipText = chipData[chipId][0]+chipCode
					displayText = monospaceFont.render(chipText, False, (0,0,0))
					screen.blit(displayText, (100*j, 16*(i-self.cursors[j].offset)))
			j += 1
		
		#draw cursor
		if self.cursorSide == 0:
			cursor = "<"
		else:
			cursor = ">"
		screen.blit(monospaceFont.render(cursor, False, (0,0,0)), (80, 16*(self.cursors[self.cursorSide].pos-self.cursors[self.cursorSide].offset)))
		
		#draw selected cursor
		if self.selectedIndex is not None and self.selectedIndex >= self.cursors[self.selectedSide].offset and self.selectedIndex < self.cursors[self.selectedSide].offset+self.rows:
			if self.selectedSide == 0:
				cursor = "<"
			else:
				cursor = ">"
			x = 70+20*self.selectedSide
			y = 16*(self.selectedIndex-self.cursors[self.selectedSide].offset)
			#print(x,y)
			screen.blit(monospaceFont.render(cursor,False,(0,0,0)),(x,y))
	
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


class ChipAttack():
	"""A chip to be held in the attack queue, to track damage and bonuses. will be converted into an AttackEntity on use"""
	def __init__(self, Chip):
		self.Id, self.code = Chip
		self.name, self.damage, self.element, self.status, codes = chipData[self.Id]
		self.effects = []	#a list of effects to be added ex:setgreen 
		self.plusBonus = 0
		self.multiplier = 1
	
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
		if self.Id < len(attackData):
			attackAlias, subId = attackData[self.Id]
			return attackAlias(user, self, subId)
		
	def mergeBonuses(self, chipAttack):
		self.plusBonus += chipAttack.plusBonus
		self.multiplier *= chipAttack.multiplier
		self.effects += chipAttack.effects
		if chipAttack.addedStatus:
			self.addedStatus = chipAttack.addedStatus
			
	def draw(self):
		"""draw chip for custom/folder"""
		NotImplemented
		
		
		
class AttackEntity(Expirable):
	"""	handles timing of attacks, created upon using an attack
		does not care about animation"""
	def __init__(self, user, chipAttack, endFrame):# damage, element, status, endFrame):
		#data from user
		self.user = user
		self.pos = user.pos[:] #want a copy of user's position
		
		#redundant data
		self.team = user.team
		#self.status = 0
		#self.element = chipAttack.element
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
		for entity in board.pokemonEntities:
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
				board.tileTypes[x][y] = 1
			elif effect == "SetBlue":
				board.tileTypes[x][y] = 2
			elif effect == "SetYellow":
				board.tileTypes[x][y] = 3
			elif effect == "SetGreen":
				board.tileTypes[x][y] = 4
		return success
				
	def shootRow(self, pos):
		NotImplementedError
		"""	shoots down row at pos
			shoots right if red team or left if blue team"""
		for entity in board.pokemonEntities:
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
		for entity in board.pokemonEntities:
			if entity.team==self.team or abs(self.pos[0]-entity.pos[0]>maxRange):
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
		user.moveLock = True
		board.animations.append(Animation(user.pos[:], user.team, "shoot.png", [0,0,80,80], 0, 10))
		
	def tick(self):
		#player should be immobile upon activating
		#print("shoot tick",self.frame)
		if self.frame == self.shootFrame:	#could have this factor in speed
			board.hitBoxes.append(Bullet(self, self.pos, .5))
		if self.frame >= self.endFrame:
			#free player
			self.user.moveLock = False
			
		AttackEntity.tick(self)
		
class SwordAttack(AttackEntity):
	def __init__(self, user, chipAttack, subId):
		swordSubData = [[7, 1, 9],[7, 1, 9],[7, 1, 9],[7, 1, 9],[7, 1, 9]]
		self.shootFrame, self.status, self.endFrame = swordSubData[subId]
		AttackEntity.__init__(self, user, chipAttack, self.endFrame)
		user.moveLock = True
		if self.user.team == 1:
			x = user.pos[0]+1
		else:
			x = user.pos[0]-1
		board.hitBoxes.append(HitBox(self,[x,user.pos[1]-1],[1,3],12,6))
		board.animations.append(Animation([x,user.pos[1]+1.5], user.team, "wideSword.png", [0,0,80,240], 0, 10))
		
	def tick(self):
		#player should be immobile upon activating
		#print("sword tick",self.frame)
		#if self.frame == self.shootFrame:	#could have this factor in speed
		#	self.sliceWide(self.pos)
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
		board.hitBoxes.append(HitBox(self,self.pos,[1,1],self.endFrame/2,self.endFrame/2))
		
	def tick(self):
		#move
		if self.frame < self.endFrame/2:
			#add to user's position
			self.user.visualOffset[0] += self.speed
		#hit
		#if self.frame == self.endFrame/2:
			#if self.hitTile(self.pos):
			#	board.animations.append(Animation(self.pos,0,"tackle.png",[0,0,80,80],0,5))
		#move back
		if self.frame > self.endFrame/2:
			#add to user's position
			self.user.visualOffset[0] -= self.speed
		if self.frame == self.endFrame:
			self.user.moveLock = False
		
		super(PhysicalAttack, self).tick()
				
class TargetAttack(AttackEntity):
	""" an attack that targets the nearest enemy"""
	def __init__(self, user, chipAttack, subId):
		targetSubData = [[18, 10, 3]]
		endFrame, self.hitFrame, self.maxRange = targetSubData[subId]
		AttackEntity.__init__(self, user, chipAttack, endFrame)
		
		#self.user.moveLock = True
		target = self.nearestEnemy(self.pos,self.maxRange)
		if target:
			hitPos = target.pos[:]
			board.hitBoxes.append(HitBox(self, hitPos, [1,1], self.hitFrame, endFrame-self.hitFrame))
			board.animations.append(Animation(hitPos, user.team, "target shot.png", [0,0,80,80], 0, 10))
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
		self.hitBox = MovingTileHitBox(self, self.pos, [1,0], self.moveDelay)
		board.hitBoxes.append(self.hitBox)
		
		
		
	def tick(self):
		#move every moveDelay frames
		if self.frame%self.moveDelay == 0:
			board.animations.append(Animation(self.hitBox.pos,self.team,"shockwave.png",[0,0,80,80],0,4))
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
		self.hitBox = MovingHitBox(self, self.user.pos[:], [1,1], [self.speed,0], 1000)
		board.hitBoxes.append(self.hitBox)
		self.axis = 1
		self.status = 4
		
	def tick(self):
		#check rows/cols to decide to turn
		#if there's an enemy on the opposite axis turn towards enemy
		if self.frame*self.speed%1 == 0:
			for entity in board.pokemonEntities:
				if entity.team!=self.team and entity.pos[self.axis] == self.hitBox.pos[self.axis]:
					#change direction
					self.hitBox.speed[self.axis] = self.speed
					self.axis = -self.axis+1
					self.hitBox.speed[self.axis] = 0
				#reverse at edge of field
					
					
		super().tick()

class Animation():
	"""animation object
		if animationLength is set, animation will repeat until endFrame
		
	"""
	def __init__(self, pos, team, spriteFile, spriteCoords, animationDelay, endFrame, animationLength=None):
		self.pos = pos
		self.team = team
		self.endFrame = endFrame
		self.rect = Rect(0,0,spriteCoords[2],spriteCoords[3])
		if animationLength==None:
			#animation doesn't repeat
			self.animationLength = endFrame
		else:
			self.animationLength = animationLength
		self.strip = spritesheet(spriteFile).load_strip(spriteCoords, self.animationLength, colorkey=-1)
		self.animationTimer = 0
	
	def tick(self):
		self.animationTimer += 1
		
	def getImage(self):
		image = self.strip[self.animationTimer%self.animationLength]
		if self.team == 1:
			image = pygame.transform.flip(image,True,False)
		return image
		
	def getRect(self):
		x = self.pos[0]*tileWidth+tileHeight
		y = self.pos[1]*tileHeight+tileWidth
		self.rect.center = x,y
		return self.rect
	
	def destroy(self):
		self.animationTimer = endFrame

class HitBox(Expirable):
	"""single instance of a hit that can last for multiple frames
		0 -> warning frames -> activeFrames"""
	def __init__(self, attack, pos, size, warningFrames, activeFrames):
		self.attack = attack
		self.pos = pos
		self.size = size
		self.warningFrames = warningFrames
		self.activeFrames = activeFrames
		self.victims = [] #keep track of who's been hit
		self.team = attack.user.team
		
		self.damage = attack.damage
		self.element = attack.chipAttack.element		
		self.status = attack.chipAttack.status
		
		self.tileSet = None 
		for effect in self.attack.chipAttack.effects:
			if effect == "SetRed":
				self.tileSet = 1
			elif effect == "SetBlue":
				self.tileSet = 2
			elif effect == "SetYellow":
				self.tileSet = 3
			elif effect == "SetGreen":
				self.tileSet = 4
		
		
		
		self.rect = Rect(self.pos[0], self.pos[1], size[0], size[1])
		
		self.image = pygame.image.load("warning panel.png")
		super().__init__(warningFrames+activeFrames)
		
	def hit(self):
		if self.frame == self.warningFrames: #on first active frame set tile
			self.setTile()
		for entity in board.pokemonEntities:
			entityX,entityY = entity.pos
			if entity not in self.victims and entity.team!=self.team and self.rect.collidepoint(entityX,entityY):
				entity.hit(self.damage, self.element, self.status)
				self.victims.append(entity)
			
	def setTile(self):
		x,y = self.pos
		if self.tileSet and x in range(6) and y in range(3):
			for i in range(x,x+self.size[0]):
				for j in range(y,y+self.size[1]):
					board.tileTypes[i][j] = self.tileSet
		
	def draw(self):
		#board should probably be responsible for drawing hitboxes
		#draw flashing yellow box if in warning frames and solid yellow if in active frames
		#if self.pos[1]>=0 and(self.frame > self.warningFrames or self.frame <= self.warningFrames and self.frame%8 < 4):
		x,y = self.pos
		try:
			for i in range(x,x+self.size[0]):
					for j in range(y,y+self.size[1]):
						screen.blit(self.image,(tileWidth*i,tileHeight*(j+2)))
		except:
			screen.blit(self.image,(tileWidth*x,tileHeight*(y+2)))
		screen.fill((255,255,0),rect=self.rect)
					
	def tick(self):
		if self.frame >= self.warningFrames and self.frame <= self.warningFrames+self.activeFrames:
			self.hit()
		super().tick()

class MovingTileHitBox(HitBox):
	"""HitBox that teleports between tiles rather than moving incrementally"""
	def __init__(self, attack, pos, direction, delay):
		HitBox.__init__(self, attack, pos, [1,1], 0, 18*delay)
		self.direction = direction[:] #relative position to move each frame
		if self.attack.user.team == 2:
			self.direction[0] *= -1
		self.delay = delay
	
	def hit(self):
		if self.frame%self.delay == 0:
			self.setTile()
		HitBox.hit(self)
	
	def tick(self):
		if self.frame%self.delay == 0:
			for i in range(2):
				self.pos[i] += self.direction[i]
			self.rect.topleft = self.pos
			
		x,y = self.pos
		if x not in range(6) or y not in range(3):
			self.frame = self.endFrame
		
		HitBox.tick(self)
	
class MovingHitBox(HitBox):
	def __init__(self, attack, pos, size, speed, activeFrames):
		HitBox.__init__(self, attack, pos, size, 0, activeFrames)
		self.speed = speed #distance to move each frame
		if self.attack.team == 2:
			self.speed[0]*=-1
		
	def tick(self):
		for i in range(2):
			self.pos[i] += self.speed[i]
		self.rect.topleft = self.pos
		HitBox.tick(self)

class Bullet(MovingHitBox):
	"""A moving hitbox that stops after hitting it's first victim"""
	def __init__(self, attack, pos, speed):
		MovingHitBox.__init__(self, attack, pos, [1,1], [speed,0], 6/speed)
		
	def tick(self):
		if self.victims:	#end if something has been hit
			self.frame = self.endFrame
		super().tick()
		
		
class TimeFreezeAttack(AttackEntity):
	def __init__(self, user, chipAttack, endFrame):
		AttackEntity.__init__(self, user, chipAttack, endFrame)
		self.nameText = monospaceFont.render(str(self.chipAttack),False,(0,0,0))
		
	def draw(self):
		NotImplemented
		
class StageChange(TimeFreezeAttack):
	def __init__(self, user, chipAttack, subId):
		TimeFreezeAttack.__init__(self, user, chipAttack, 90)
		self.subId = subId
		#make a new board with all tiles set to subId value
		self.oldBoardTypes = board.tileTypes[:]
		self.newBoardTypes = [[subId for i in range(3)] for j in range(6)]
		
	def tick(self):
		#flash new and old tiles for a few frames
		if self.frame%8<4:
			board.tileTypes = self.newBoardTypes
		else:
			board.tileTypes = self.oldBoardTypes
		TimeFreezeAttack.tick(self)

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
	saveFile = open("save.txt", "r")
	return json.load(saveFile)
	
def save(folder, customDraw, extraMode):
	#save folder, custom draw amount, extra button, 
	saveFile = open("save.txt", "w")
	json.dump([folder,customDraw,extraMode], saveFile)
	


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
defaultFolder = [[5,"A"],[5,"A"],[6,"B"],[6,"B"],[7,"A"],[7,"A"],[8,"B"],[8,"B"],[0,"*"],[0,"*"],[2,"B"],[2,"B"],[3,"A"],[3,"A"],[1,"B"],[1,"B"],[10,"*"],[10,"*"],[11,"*"],[11,"*"],[12,"*"],[12,"*"],[13,"*"],[13,"*"],[14,"*"],[15,"*"],[16,"*"],[17,"*"],[9,"*"],[9,"*"]]
attackData = [[ShootAttack, 0], [SwordAttack, 0], [PhysicalAttack, 0], [TargetAttack, 0], [MovingTileAttack, 0], [SwordAttack, 1], [SwordAttack, 2], [SwordAttack, 3],[SwordAttack, 4],[AttackEntity, 0],[AttackEntity, 0],[AttackEntity, 0],[PursuitAttack, 0],[AttackEntity, 0],[StageChange, 1],[StageChange, 2],[StageChange, 3],[StageChange, 4]]

try:
	folder = load()
except FileNotFoundError:
	folder = defaultFolder
	
	


game = Game()


#battle
statusStrips = [spritesheet(statusFile).load_strip([0,0,80,80],statusImageCount,colorkey=-1) for statusFile,statusImageCount in [("burn.png",6),("freeze.png",10),("paralyze.png",4),("vines.png",1)]]	


#custom
player = None
board = None
custom = None
editor = None

buttonHeld = {up:False, down:False, left:False, right:False, a:False, b:False, r:False, l:False, start:False, select:False}
buttonDown = dict(buttonHeld)
buttonInput = dict(buttonHeld)


#tickList = [board]


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
			
	game.tick()
	
	for i in buttonDown:
		buttonDown[i] = False
	end = datetime.now()
	exec_time = end - frameStartTime
	sleepTime = 1/60-exec_time.total_seconds()
		
	pygame.display.flip()
	if(sleepTime>0):
		time.sleep(sleepTime)
		
		
    
