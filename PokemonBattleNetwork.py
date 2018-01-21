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

tileWidth = 80
tileHeight = 40
size = width, height = tileWidth*6, tileHeight*5
screen = pygame.display.set_mode(size)

pygame.transform.scale(screen,(1366,768))
#resources
elements = ["null","fire","aqua","elec","wood","break","cursor","wind","sword"]
			#[name,damage,element,codes]
chipData = [["Air Shot", 10, 7,["*"]],["WideSwrd",10,8,["B"]],["Tackle",10,5,["B"]],["Target Shot",10,6,["A"]],["Shockwave",10,0,["A","B"]],["FireSword",10,1,["A"]],["AquaSword",10,2,["B"]],["ElecSword",10,3,["A"]],["BambSword",10,4,["B"]],["atk+10",0,0,["*"]],["+burn",0,0,["*"]],["+freeze",0,0,["*"]],["+paralyze",0,0,["*"]],["+ensare",0,0,["*"]],["SetRed",0,0,["*"]],["SetBlue",0,0,["*"]],["SetYellow",0,0,["*"]],["SetGreen",0,0,["*"]]]
pokemonSpriteSheet = spritesheet("diamond-pearl.png")
chipSpriteSheet = spritesheet("chip icons.png")
background = pygame.image.load("background.png")
backgroundRect = background.get_rect()	
tileBoarderStrip = spritesheet("tile borders.png").load_strip([0,0,80,40],3,colorkey=[0,0,0,255])
tileStrip = spritesheet("tiles.png").load_strip([0,0,80,40],5,colorkey=-1)
tileBoarderRects = []
tileRects = []
for i in range(6):
	tempTileRects = []
	tempBoarderRects = []
	for j in range(3):
		tempTileRects.append(Rect(i*tileWidth,j*tileHeight+tileWidth,80,40))
		tempBoarderRects.append(Rect(i*tileWidth,j*tileHeight+tileWidth,80,40))
	tileBoarderRects.append(tempBoarderRects)
	tileRects.append(tempTileRects)

pygame.font.init()
monospaceFont = pygame.font.SysFont("Monospace", 12, bold=True)
codeFont = pygame.font.SysFont("Monospace",7,bold=True)



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
		
class PokemonEntity():
	def __init__(self, pos, team, element):
		self.pos = pos
		self.team = team
		self.moveLock = False
		self.status = 0
		self.statusTimer = 0
		self.element = element #normal, fire, aqua, elec, wood, break, cursor, wind, sword
		self.visualOffset = [0,0]
		self.image = None
		self.rect = None
		
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
		if newX<0 or newX>5 or newY<0 or newY>2:	#catch out of bounds
			return
		for entity in pokemonEntities:	#catch collisions
			if entity.pos == self.pos:	#don't check self
				continue
			if entity.pos == [newX,newY]:
				return
			
			if False:	#prevent moving past enemy
				if entity.team == self.team:	#don't check teamates
					continue
				if self.team == 1 and newX > entity.pos[0]:
						return
				elif self.team ==2 and newX < entity.pos[0]:
						return
		self.move(newX, newY)
		
	def move(self,x,y):
		"""move to tile at x,y"""
		if self.statusTimer==0 or self.status<=2:
			newX = int(x)
			newY = int(y)
			if boardTeam[newX][newY]==0 or self.team==boardTeam[newX][newY]:
				#move allowed
				self.pos = [newX,newY]
			
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
		if typeEffectiveness(element,tileTypes[x][y])==2:
			effectiveness *= 2
			tileTypes[x][y] = 0
					
		if effectiveness==2:
			animations.append(Animation(self.pos,0,"super effective.png",[0,0,48,48],0,4))
		elif effectiveness==4:
			animations.append(Animation(self.pos,0,"super effective.png",[0,48,48,48],0,4))
		#print("dealt",damage*effectiveness)
		self.damage(damage*effectiveness)
		
		if status==1: #flinch
			self.status = 1
			self.statusTimer = 60
		if status>1 and self.statusTimer==0:
			#if you don't resist status type
			self.status = status
			#more time if you are weak to status type?
			self.statusTimer = 60
					
	def damage(self, damage):
		NotImplemented
		
	def draw(self):
		if self.image and self.rect:
			X = (self.pos[0]+self.visualOffset[0])*tileWidth+tileHeight
			Y = (self.pos[1]+self.visualOffset[1])*tileHeight+tileWidth
			self.rect.center = X,Y
			
			if not(self.status==1 and self.statusTimer%2==1): #don't draw every other frame if flinched
				screen.blit(self.image, self.rect)
				
			if self.status>1 and self.statusTimer>0:
				#draw status effect
				statusStrip = statusStrips[self.status-2]
				statusFrame = (60-self.statusTimer)%len(statusStrip)-1
				screen.blit(statusStrip[statusFrame], self.rect)
			
						
	def tick(self):
		if self.statusTimer>0:
			if self.status==2 and self.statusTimer%15==0: #burn damage over time
				self.hit(1,1,0)
			self.statusTimer -= 1
		x,y = self.pos

class Navi(PokemonEntity):
	def __init__(self, pos, team, element):
		PokemonEntity.__init__(self, pos, team, element)
		self.pokemon = pokemon(randint(1,493),randint(1,15))
		self.image = self.pokemon.image
		self.rect = self.pokemon.rect
		if self.team==1:
			self.image = pygame.transform.flip(self.image,True,False)
		self.totalDamage = 0
		self.healCooldown = 0
		
	def damage(self, damage):
		self.pokemon.totalStats[0] -= damage
	
	def draw(self):
		PokemonEntity.draw(self)
		HpTextShadow = monospaceFont.render(str(self.pokemon.totalStats[0]), False, (0,0,0))
		HpText = monospaceFont.render(str(self.pokemon.totalStats[0]), False, (255,255,255))
		X = self.pos[0]*tileWidth+tileHeight-10
		Y = self.pos[1]*tileHeight+tileWidth+25
		screen.blit(HpTextShadow,(X+1, Y+1))
		screen.blit(HpText,(X,Y))
		
	def tick(self):
		PokemonEntity.tick(self)
		x,y = self.pos
		if tileTypes[x][y]==self.element and self.healCooldown==0:
			self.pokemon.totalStats[0]+=1
			self.healCooldown=15
		self.healCooldown -= 1

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
		
		
class Custom():
	""""handles the data for the custom window"""
	def __init__(self, folder, customDraw):
		self.folder = folder[:]
		shuffle(self.folder)
		self.customDraw = customDraw
		self.hand = []
		self.refresh()
		self.extraMode = ["discard","recycle","restock"]
		self.extraUsed = False
		
		#resources for drawing
		self.cursorRect = Rect(0,0,18,18)
		self.cursorSprites = spritesheet("custom cursor.png").load_strip(self.cursorRect,2,colorkey=-1)
		self.customWindow = pygame.image.load("custom frame.png")
		self.customWindowRect = self.customWindow.get_rect()
		
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
		
	def refresh(self):
		"""draws a new hand and resets relevant data"""
			
		self.refillHand()
		self.extraUsed = False
		if len(self.hand)==0:
			self.cursor = -1
		else:
			self.cursor = 0

	def refillHand(self):
		#draw chips to refill hand		
		drawAmount = self.customDraw-len(self.hand)
		if len(self.folder) < drawAmount:
			drawAmount = len(self.folder)
		for i in range(drawAmount):
			if self.folder:
				self.hand.append(self.folder.pop())
			else:
				break	
		self.selectedCode = None
		self.selectedID = None
		self.selectedChips = []
		self.selected = [False for i in range(self.customDraw)]
		self.handSprites = [chipSpriteSheet.getSpriteById(chip[0],20,16,16,colorkey=0) for chip in self.hand]
		self.handRects = [handSprite.get_rect() for handSprite in self.handSprites]
				
	
		
	def moveCursor(self, direction):
		if direction=="up":
			if self.cursor>=5:
				self.cursor -= 5
			elif self.cursor <-1:
				self.cursor += 1			
		elif direction=="down":
			if self.cursor>=0 and self.cursor<len(self.hand)-5:
				self.cursor += 5
			elif self.cursor < 0:
				self.cursor -= 1
		elif direction=="left":
			if self.cursor>=0:
				if self.cursor%5==0:
					self.cursor = self.cursor//-5-1
				else:
					self.cursor -= 1
			else:
				self.cursor = self.cursor*-5 -1
			
		elif direction=="right":
			if self.cursor>=0:
				if self.cursor%5==4:
					self.cursor = (self.cursor+1)//-5
				elif self.cursor==len(self.hand)-1:
					self.cursor = self.cursor//-5-1
				else:
					self.cursor+=1
			else:
				self.cursor = (self.cursor+1)*-5
				
		#check bounds
		#print("cursor moved to",self.cursor)
		if self.cursor>=len(self.hand):
			self.cursor = len(self.hand)-1
		elif self.cursor<-2:
			self.cursor = -2
		#print("cursor at",self.cursor)
		
	def select(self):
		"""selects the chip at the current cursor position and adds it to selectedChips
			returns selectedChips if user selects OK"""
		#close custom
		if self.cursor==-1:
			#load selectedChips attacks into attackQueue
			attackQueue = []
			while self.selectedChips:
				currentChip = self.hand[self.selectedChips.pop(0)]
				if currentChip[0] == 9 and attackQueue: #if attack+10
					#print("found attack+")
					attackQueue[0].plusBonus += 10
				elif currentChip[0]>= 10 and currentChip[0]<14 and attackQueue: #+status
					attackQueue[0].status = currentChip[0]-8
				elif currentChip[0] in range(14,18) and attackQueue:
					effectNames = ["SetRed","SetBlue","SetYellow","SetGreen"]
					attackQueue[0].effects.append(effectNames[currentChip[0]-14])
				else:
					attackQueue.insert(0,ChipAttack(currentChip))
			#remove selected chips from hand
			newHand = []
			for i in range(len(self.hand)):
				if not self.selected[i]:
					newHand.append(self.hand[i])
			self.hand = newHand
			self.refresh()
			return attackQueue
			
		elif self.cursor==-2:
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
					self.folder = removedChips + self.folder
					
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
			
		elif self.cursor>=0 and self.cursor<len(self.hand):
			chipID,chipCode = self.hand[self.cursor]
			if len(self.selectedChips)<5 and not self.selected[self.cursor] and (self.selectedCode==None or self.selectedCode==chipCode or self.selectedID==chipID or (self.selectedCode!=-1 and chipCode=="*")):
				self.selectedChips.append(self.cursor) #select chip by adding it's cursor pos to self.selectedChips
				self.selected[self.cursor] = True
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
		screen.blit(self.customWindow, self.customWindowRect)
		#draw extra button
		if self.extraButtons:
			if self.extraUsed:
				screen.blit(self.extraButtons[1],(95,136,24,16))
			else:
				screen.blit(self.extraButtons[0],(95,136,24,16))
		#draw each chip
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
		chipImageStrip = spritesheet("chip images.png").load_strip([0,0,56,48],10)
		elementStrip = spritesheet("elements.png").load_strip([0,0,14,14],9,colorkey=-1)
		
		if self.cursor<0:
			chipID = len(chipImageStrip)-1
		else:
			currentChip = chipID,chipCode= self.hand[self.cursor]
			chipName = chipData[chipID][0]
			chipNameText = monospaceFont.render(chipName,False,(255,255,255))
			chipCodeText = monospaceFont.render(chipCode,False,(255,255,0))
			chipDamageText = monospaceFont.render("10",False,(255,255,255))
			screen.blit(chipNameText,(15,17))
			screen.blit(chipCodeText,(15,89))
			screen.blit(elementStrip[0],(25,89))#need to assign elements to chipIDs and damage
			screen.blit(chipDamageText,(69,89))
		if(chipID<len(chipImageStrip)):
			screen.blit(chipImageStrip[chipID],(15,29))
		
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
		if self.cursor<0:
			#replace this with a special cursor to fit OK button
			self.cursorRect.left = 95
			self.cursorRect.top = 79-28*self.cursor
		else:
			self.cursorRect.left = self.cursor%5*17+10
			self.cursorRect.top = self.cursor//5*28+107
		screen.blit(self.cursorSprites[customCounter//5], self.cursorRect)
		
class Editor():
	"""stores data for folder editing menu"""
	def __init__(self, folder):
		self.cursor = [0,0] #row of cursor
		self.offset = [0,0] #position to draw top of menu
		self.cursorSide = 0	#folder/pack 
		self.rows = 8
		self.folder = folder[:]
		self.selectedSide = None
		self.selectedIndex = None
		#create folder containing all chips
		self.allChips = []
		for i in range(len(chipData)):
			for code in chipData[i][3]:
				self.allChips.append([i,code])
		#print(self.allChips)
		#print("folder length",len(self.folder),"all length",len(self.allChips))
		
	def select(self):
		if self.selectedIndex == None:
			self.selectedSide = self.cursorSide
			self.selectedIndex = self.offset[self.cursorSide]+self.cursor[self.cursorSide]
		else:
			currentIndex = self.offset[self.cursorSide]+self.cursor[self.cursorSide]
			print("current Index",currentIndex)
			#double tap
			if self.cursorSide == self.selectedSide and self.selectedIndex == currentIndex:
				if self.cursorSide == 0:
					#remove chip from folder
					self.folder[self.selectedIndex] = None
				else:
					#add chip to folder
					try:
						self.folder[self.folder.index(None)] = self.allChips[self.selectedIndex]
					except:
						False
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
			
			self.selectedSide = None
			self.selectedIndex = None
		
						
		print("selected",self.selectedSide,self.selectedIndex)
		
	def scroll(self, direction):
		if self.cursorSide == 0:
			length = len(self.folder)
		else:
			length = len(self.allChips)
		if direction == "up":
			if self.cursor[self.cursorSide] > 0:
				self.cursor[self.cursorSide] -= 1
			elif self.offset[self.cursorSide] > 0:
				self.offset[self.cursorSide] -= 1
		elif direction == "down":
			if self.cursor[self.cursorSide] < self.rows-1:
				self.cursor[self.cursorSide] += 1
			elif self.offset[self.cursorSide] < length-self.rows:
				self.offset[self.cursorSide] += 1
		elif direction == "left":
			self.cursorSide = 0
		elif direction == "right":
			self.cursorSide = 1
		elif direction == "bigUp":
			if self.offset[self.cursorSide] >= self.rows:
				self.offset[self.cursorSide] -= self.rows
			else:
				self.offset[self.cursorSide] = 0
		elif direction == "bigDown":
			if self.offset[self.cursorSide] < length-2*self.rows:
				self.offset[self.cursorSide] += self.rows
			else:
				self.offset[self.cursorSide] = length-self.rows
		#print("cursor",self.cursor,"offset",self.offset)
	
	def draw(self):
		screen.blit(background,backgroundRect)
		
		#draw folder
		j = 0
		for something in [self.folder,self.allChips]:
			for i in range(self.offset[j],self.offset[j]+self.rows):
				if something[i] != None:
					chipId, chipCode = something[i]
					chipText = chipData[chipId][0]+chipCode
					displayText = monospaceFont.render(chipText,False,(0,0,0))
					screen.blit(displayText,(100*j,16*(i-self.offset[j])))
			j += 1
		#draw all chips
		#draw cursor
		if self.cursorSide == 0:
			cursor = "<"
		else:
			cursor = ">"
		screen.blit(monospaceFont.render(cursor,False,(0,0,0)),(80,16*self.cursor[self.cursorSide]))
		#draw selected cursor
		if self.selectedIndex is not None and self.selectedIndex >= self.offset[self.selectedSide] and self.selectedIndex < self.offset[self.selectedSide]+self.rows:
			if self.selectedSide == 0:
				cursor = "<"
			else:
				cursor = ">"
			x = 70+20*self.selectedSide
			y = 16*(self.selectedIndex-self.offset[self.selectedSide])
			#print(x,y)
			screen.blit(monospaceFont.render(cursor,False,(0,0,0)),(x,y))
				

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

class ChipAttack():
	"""A chip to be held in the attack queue, to track damage and bonuses. will be converted into an AttackEntity on use"""
	def __init__(self, Chip):
		self.Id, self.code = Chip
		self.name, self.damage, self.element, codes = chipData[self.Id]
		self.status = None
		self.effects = []	#a list of effects to be added ex:setgreen 
		self.plusBonus = 0
		self.multiplier = 1
		
	def use(self):
		"""converts self into attackEntity and returns it"""
		#create AttackEntity corresponding to chip
		attackAlias, subId = attackData[self.Id]
		return attackAlias(player, self, subId)
		
	def mergeBonuses(self, chipAttack):
		self.plusBonus += chipAttack.plusBonus
		self.multiplier *= chipAttack.multiplier
		self.effects += chipAttack.effects
		if chipAttack.addedStatus:
			self.addedStatus = chipAttack.addedStatus
		
		
		

class AttackEntity():
	"""	handles timing of attacks, created upon using an attack
		does not care about animation"""
	def __init__(self, user, chipAttack, endFrame):# damage, element, status, endFrame):
		#data from user
		self.user = user
		self.pos = user.pos[:] #want a copy of user's position
		self.team = user.team
		
		#data from chip
		self.chipAttack = chipAttack
		self.damage = (chipAttack.damage+chipAttack.plusBonus)*chipAttack.multiplier
		self.element = chipAttack.element
		if chipAttack.status:
			#print("changing status to",chipAttack.status)
			self.status = chipAttack.status
		
		self.endFrame = endFrame
		self.attackTimer = 0
		
		#self.strip = spritesheet(spriteFile).load_strip(spriteCoords,animationLength,colorkey=-1)
		#self.rect = Rect(spriteCoords)
		#self.animationDelay = animationDelay
		#self.repeatAnimation = repeatAnimation
			
		#move animation data into animation object
		#self.animation = Animation(user.pos[:], spriteFile, spriteCoords, animationDelay, endFrame)
		#animations.append(self.animation)
		
		
	def tick(self):
		"""called each frame to update animation"""
		self.attackTimer += 1
		
	def hitTile(self,pos):
		"""	hit tile at given position
			uses AttackEntity's damage, type, team, ect"""
		x,y = pos
		if x<0 or x>5 or y<0 or y>2:
			return False
		success = False
			
		
		#print("hitTile",pos)
		for entity in pokemonEntities:
			if entity.pos==pos and entity.team!=self.team:
				#print("hit",pos,"for",self.damage,"damage")
				entity.hit(self.damage, self.element, self.status)
				success = True
		#effects
		#if miss check tile element
		#if tile element is weak to attack set tile to null
		if typeEffectiveness(self.element,tileTypes[x][y])==2:
			#print("burnt tile",pos)
			tileTypes[x][y] = 0
		for effect in self.chipAttack.effects:
			if effect == "SetRed":
				tileTypes[x][y] = 1
			elif effect == "SetBlue":
				tileTypes[x][y] = 2
			elif effect == "SetYellow":
				tileTypes[x][y] = 3
			elif effect == "SetGreen":
				tileTypes[x][y] = 4
		return success
				

	def shootRow(self, pos):
		"""	shoots down row at pos
			shoots right if red team or left if blue team"""
		for entity in pokemonEntities:
			#not same team
			#in same row
			#right if red or left if blue
			if entity.team!=self.team and entity.pos[1]==pos[1] and ((self.team==1 and entity.pos[0]>pos[0]) or (self.team==2 and entity.pos[0]<pos[0])):
				#entity.hit(self.damage, self.element, self.status)
				self.hitTile(entity.pos)
				return
				
	def sliceWide(self, pos):
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
		if self.team==1:
			bestCol = 7
		elif self.team==2:
			bestCol = -1
		for entity in pokemonEntities:
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
	#difference = attackElement-defendElement
	#if difference==1 and attackElement!=5 and attackElement!=1:
	#elif difference==-3 and attackElement==1 or attackElement==5
			
class ShootAttack(AttackEntity):
	"""	a child of AttackEntity for shooting attacks, will call shootRow on shootFrame and will end on endFrame
		ToDo: get sprites and add a spriteSheet and extra data to select different sprites"""
	def __init__(self, user, chipAttack, subId):
		shootSubData = [[7, 9]]
		self.shootFrame, self.endFrame = shootSubData[subId]
		self.status = 0
		AttackEntity.__init__(self, user, chipAttack, self.endFrame)
		user.moveLock = True
		animations.append(Animation(user.pos[:], user.team, "shoot.png", [0,0,80,80], 0, 10))
		
	def tick(self):
		#player should be immobile upon activating
		#print("shoot tick",self.attackTimer)
		if self.attackTimer == self.shootFrame:	#could have this factor in speed
			self.shootRow(self.pos)
		if self.attackTimer >= self.endFrame:
			#free player
			self.user.moveLock = False
			
		super(ShootAttack, self).tick()
		
class SwordAttack(AttackEntity):
	def __init__(self, user, chipAttack, subId):
		swordSubData = [[7, 1, 9],[7, 1, 9],[7, 1, 9],[7, 1, 9],[7, 1, 9]]
		self.shootFrame, self.status, self.endFrame = swordSubData[subId]
		AttackEntity.__init__(self, user, chipAttack, self.endFrame)
		user.moveLock = True
		animations.append(Animation([user.pos[0]+1,user.pos[1]+1], user.team, "wideSword.png", [0,0,80,240], 0, 10))
		
	def tick(self):
		#player should be immobile upon activating
		#print("sword tick",self.attackTimer)
		if self.attackTimer == self.shootFrame:	#could have this factor in speed
			self.sliceWide(self.pos)
		if self.attackTimer >= self.endFrame:
			#free player
			self.user.moveLock = False
			
		super(SwordAttack, self).tick()
	
class MultiAttack(AttackEntity):
	"""	an attack entity that handles multihits
		creates an attack entity each interval for multiCount times"""
	def __init__(self, user, damage, element, status, multiCount, interval, attack):
		AttackEntity.__init__(self, user, multiCount*interval) #end time depends on number of hits
		
	def tick(self):
		if self.attackTimer%interval == 0:
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
		
		self.speed = self.distance/self.endFrame
		self.user.moveLock = True
		self.pos[0] += self.distance
		
	def tick(self):
		#move
		if self.attackTimer < self.endFrame/2:
			#add to user's position
			self.user.visualOffset[0] += self.speed
		#hit
		if self.attackTimer == self.endFrame/2:
			if self.hitTile(self.pos):
				animations.append(Animation(self.pos,0,"tackle.png",[0,0,80,80],0,5))
		#move back
		if self.attackTimer > self.endFrame/2:
			#add to user's position
			self.user.visualOffset[0]-=self.speed
		if self.attackTimer == self.endFrame:
			self.user.moveLock = False
		
		super(PhysicalAttack, self).tick()
		
		
class TargetAttack(AttackEntity):
	""" an attack that targets the nearest enemy"""
	def __init__(self, user, chipAttack, subId):
		targetSubData = [[9, 5, 3]]
		self.status = 1
		self.endFrame, self.hitFrame, self.maxRange = targetSubData[subId]
		AttackEntity.__init__(self, user, chipAttack, self.endFrame)
		
		self.user.moveLock = True
		target = self.nearestEnemy(self.pos,self.maxRange)
		if target:
			self.pos = target.pos[:]
		else:
			self.pos = [-10,-10]
		animations.append(Animation(self.pos, user.team, "target shot.png", [0,0,80,80], 0, 10))
	
	def tick(self):
		if self.attackTimer == self.hitFrame:
			self.hitTile(self.pos)
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
		movingSubData = [[30, 4]]
		endFrame, self.moveDelay = movingSubData[subId]
		AttackEntity.__init__(self, user, chipAttack, endFrame)
		
		
	def tick(self):
		#move every moveDelay frames
		if self.attackTimer%self.moveDelay == 0:
			animations.append(Animation(self.pos,self.team,"shockwave.png",[0,0,80,80],0,4))
			if self.team == 1:
				self.pos[0] += 1
			elif self.team == 2:
				self.pos[0] -= 1
			#if tile is broken quit
				#self.attackTimer = self.endFrame
			self.hitTile(self.pos)
		super(MovingTileAttack, self).tick()
		
#SlowBeamAttack - firebrn

class ThrowAttack(AttackEntity):
	"""a projectile is thrown 3 squares ahead"""
	def __init__(self, user, damage, element, team, status, endFrame):
		AttackEntity.__init__(self, user, damage, element, team, status, endFrame)
	
	def tick(self):
		super(SampleAttack, self).tick()
		
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
		
		

def drawAttackQueue():
	#draw text for first chip
	if attackQueue:
		topChip = attackQueue[len(attackQueue)-1]
		if topChip.Id<len(chipData):
			chipName = topChip.name#chipNames[topChip]
		else:
			chipName = "???"
		chipText = chipName+" "+str(topChip.damage)
	
		chipText += "+"+str(topChip.plusBonus)

		chipText += "x"+str(topChip.multiplier)
		currentChipText = monospaceFont.render(chipText,False,(0,0,0))
		screen.blit(currentChipText,(0,height-15))
	offset = len(attackQueue)*2
	for attack in attackQueue:
		#draw attack relative to player
		chipSprite = chipSpriteSheet.getSpriteById(attack.Id,20,16,16,colorkey=0)
		chipRect = chipSprite.get_rect()
		chipRect.center = player.pos[0]*tileWidth+tileWidth/2-offset, player.pos[1]*tileHeight+tileHeight-offset
		screen.blit(chipSprite,chipRect)
		offset-=2

	
def drawBoard():
	for i in range(6):
		for j in range(3):
			#check type
			screen.blit(tileBoarderStrip[boardTeam[i][j]], tileBoarderRects[i][j])
			screen.blit(tileStrip[tileTypes[i][j]], tileRects[i][j])
					
def drawGame():
	screen.blit(background, backgroundRect)
	drawBoard()
	#sort entities from back to front for drawing
	pokemonEntities.sort(key=lambda x: x.pos[1])
	for entity in pokemonEntities:	#draw all entities
		entity.draw()
			
	
	"""for attack in attackEntities:
		x = attack.pos[0]*tileWidth+tileHeight
		y = attack.pos[1]*tileHeight+tileWidth
		
		attack.rect.center = x,y
		attackFrame = attack.attackTimer-attack.animationDelay
		animationLength = len(attack.strip)-1
		if attackFrame>0:
			if attack.repeatAnimation:
				attackImage = attack.strip[attackFrame%animationLength]
			elif attackFrame <= animationLength:
				attackImage = attack.strip[attackFrame]
			else:
				continue
				
			if attack.team==1:
				attackImage = pygame.transform.flip(attackImage,True,False)
			screen.blit(attackImage, attack.rect)"""
			
			
	for animation in animations:
		screen.blit(animation.getImage(),animation.getRect())
		
	drawAttackQueue()
	
	customRect.right = frameCount*width/turnFrames
	screen.blit(customGauge,customRect)
	if frameCount >= turnFrames:
		timerText = monospaceFont.render("Press R to open custom!", False, (0,0,0))
		screen.blit(timerText,(0,0))
	

	


def TitleScreen():
	global pokemonEntities
	global custom
	global enemies	
	global gameTickAlias
	textsurface = monospaceFont.render("Press Enter to Start\nPress F to edit folder", False, (255,255,255))
	title = pygame.image.load("title.png")
	title2 = pygame.image.load("title2.png")
	
	screen.blit(title,(0,0))
	screen.blit(title2,(240 ,0))
	
	screen.blit(textsurface,(200,188))
	pygame.display.flip()
	for event in pygame.event.get():
		if event.type == pygame.KEYDOWN and event.key == K_RETURN:
			gameTickAlias = CustomTick
		if event.type == pygame.KEYDOWN and event.key == K_f:
			gameTickAlias = FolderTick
		if event.type == pygame.KEYDOWN and event.key == K_s:		
			custom = Custom(folder,10)
			enemies = [SandBag([4,1],0)]
			pokemonEntities = [player]+enemies
			gameTickAlias = CustomTick

def FolderTick():
	global gameTickAlias
	"""a menu to allow editing folder and other data related to the player"""
	#display folder and chips
	editor.draw()
	#scroll with buttons
	for event in pygame.event.get():
		if event.type == pygame.KEYDOWN and event.key == K_UP:
			editor.scroll("up")
		if event.type == pygame.KEYDOWN and event.key == K_DOWN:
			editor.scroll("down")
		if event.type == pygame.KEYDOWN and event.key == K_LEFT:
			editor.scroll("left")
		if event.type == pygame.KEYDOWN and event.key == K_RIGHT:
			editor.scroll("right")
		if event.type == pygame.KEYDOWN and event.key == K_PAGEUP:
			editor.scroll("bigUp")
		if event.type == pygame.KEYDOWN and event.key == K_PAGEDOWN:
			editor.scroll("bigDown")
		if event.type == pygame.KEYDOWN and event.key == K_SPACE:
			editor.select()
		if event.type == pygame.KEYDOWN and event.key == K_ESCAPE:
			#save changes
			print("exiting editor")
			custom.folder = editor.folder[:]
			gameTickAlias = TitleScreen
					
def BattleTick():
	global gameTickAlias
	global frameCount
	global attackQueue
	for event in pygame.event.get():
		if event.type == pygame.QUIT: 
			sys.exit()
		if event.type == pygame.KEYDOWN and event.key == K_LEFT:
			if not player.moveLock:
				player.moveDirection("left")
		if event.type == pygame.KEYDOWN and event.key == K_RIGHT:
			if not player.moveLock:
				player.moveDirection("right")
		if event.type == pygame.KEYDOWN and event.key == K_UP:
			if not player.moveLock:
				player.moveDirection("up")
		if event.type == pygame.KEYDOWN and event.key == K_DOWN:
			if not player.moveLock:
				player.moveDirection("down")
		if event.type == pygame.KEYDOWN and event.key == K_SPACE:
			if not player.moveLock:
				if attackQueue:				
					attack = attackQueue.pop()
					attackEntities.append(attack.use())					
					
		if event.type == pygame.KEYDOWN and event.key == K_r:
			if frameCount >= turnFrames:
				#print("enter custom")
				gameTickAlias = CustomTick
				frameCount = 0
					
	for enemy in enemies:
		if isinstance(enemy,Navi) and randint(0,20)==0:
			moves = ["left","right","up","down"]
			enemy.moveDirection(moves[randint(0,3)])
		#elif randint(0,40)==0:
		#	shootRow(enemy.pos,10,0,2,True)
			
	for entity in pokemonEntities:
		if isinstance(entity, Navi) and entity.pokemon.totalStats[0]<= 0:
			pokemonEntities.remove(entity)
			enemies.remove(entity)
			
	if not enemies:
		newBadGuy = Navi([5,1],2,randint(0,9))
		pokemonEntities.append(newBadGuy)
		enemies.append(newBadGuy)
		
	for attackEntity in attackEntities:
		attackEntity.tick()
		if attackEntity.attackTimer > attackEntity.endFrame:
			attackEntities.remove(attackEntity)		
			
	for animation in animations:
		if animation.animationTimer >= animation.endFrame:
			animations.remove(animation)
		animation.tick()
		
	for entity in pokemonEntities:
		entity.tick()
		
	drawGame()
	
	if frameCount >= turnFrames:
		frameCount = turnFrames
	else:
		frameCount += 1
		
	
selectedID = None #allows selecting same chip with different codes, None = no chips selected, -1 = non matching chips selected
def CustomTick():
	global gameTickAlias
	global attackQueue
	global customCounter
	"""open custom menu, handle cursor and chip selection, draw chips"""
	#drawCustom
	drawGame()
	custom.draw()
	
	for event in pygame.event.get():
		if event.type == pygame.QUIT: 
			sys.exit()
		if event.type == pygame.KEYDOWN and event.key == K_UP:
			custom.moveCursor("up")
		if event.type == pygame.KEYDOWN and event.key == K_DOWN:
			custom.moveCursor("down")
		if event.type == pygame.KEYDOWN and event.key == K_LEFT:
			custom.moveCursor("left")
		if event.type == pygame.KEYDOWN and event.key == K_RIGHT:
			custom.moveCursor("right")
		if event.type == pygame.KEYDOWN and event.key == K_RETURN:
			custom.cursor = -1
		if event.type == pygame.KEYDOWN and event.key == K_SPACE:
			selectedAttacks = custom.select()
			if selectedAttacks!=None:	#OK is pressed
				if selectedAttacks:	#don't overwrite if no attacks selected
					attackQueue = selectedAttacks
				gameTickAlias = BattleTick
		if event.type == pygame.KEYDOWN and event.key == K_BACKSPACE:
			custom.deselect()
			
				
				
	customCounter+=1
	if customCounter >= 10:
		customCounter = 0
		
def load(fileName):
	saveFile = open(fileName, "r")
	global folder
	folder = json.load(saveFile)
def save(fileName):
	saveFile = open(fileName, "w")
	json.dump(folder,saveFile)
	
attackData = [[ShootAttack, 0], [SwordAttack, 0], [PhysicalAttack, 0], [TargetAttack, 0], [MovingTileAttack, 0], [SwordAttack, 1], [SwordAttack, 2], [SwordAttack, 3],[SwordAttack, 4],[ShootAttack, 0]]		
	
#game
gameTickAlias = TitleScreen
boardTeam = [[1,1,1],[1,0,1],[0,0,0],[0,0,0],[2,0,2],[2,2,2]] #each row of board 0 = neutral, 1 = red, 2 = blue
tileTypes = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
folder = [[5,"A"],[5,"A"],[6,"B"],[6,"B"],[7,"A"],[7,"A"],[8,"B"],[8,"B"],[0,"*"],[0,"*"],[2,"B"],[2,"B"],[3,"A"],[3,"A"],[1,"B"],[1,"B"],[10,"*"],[10,"*"],[11,"*"],[11,"*"],[12,"*"],[12,"*"],[13,"*"],[13,"*"],[14,"*"],[15,"*"],[16,"*"],[17,"*"],[9,"*"],[9,"*"]]
player = Navi([1,1],1,randint(0,9))
enemies = [Navi([4,1],2,randint(0,9)),Navi([5,0],2,randint(0,9)),Navi([5,2],2,randint(0,9))]
pokemonEntities = []
pokemonEntities.append(player)
pokemonEntities += enemies
print(pokemonEntities)
attackEntities = []

#battle
turnFrames = 100
customGauge = pygame.image.load("custom guage.png")
customRect = Rect(0,0,width,height)
statusStrips = [spritesheet(statusFile).load_strip([0,0,80,80],statusImageCount,colorkey=-1) for statusFile,statusImageCount in [("burn.png",6),("freeze.png",10),("paralyze.png",4),("vines.png",1)]]	
frameCount = 0
attackQueue = []
animations = []

#custom
custom = Custom(folder, 5)
customCounter = 0
editor = Editor(folder)


while True:
	start = datetime.now()
	gameTickAlias()
	end = datetime.now()
	exec_time = end - start
	sleepTime = 1/30-exec_time.total_seconds()
		
	pygame.display.flip()
	if(sleepTime>0):
		time.sleep(sleepTime)
		
		
    
