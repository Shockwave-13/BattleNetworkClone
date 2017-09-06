import sys, pygame
from spritesheet import spritesheet
from pygame.locals import *
from random import randint
from datetime import datetime
import time
pygame.init()

size = width, height = 480, 200
tileWidth = 80
tileHeight = 40
turnFrames = 100
backgroundColor = 0, 0, 0
screen = pygame.display.set_mode(size)

pokemonEntities = []

boardTeam = [[1,1,1],[1,1,1],[1,0,1],[2,0,2],[2,2,2],[2,2,2]] #each row of board 0 = neutral, 1 = red, 2 = blue
tileTypes = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]

pokemonSpriteSheet = spritesheet("diamond-pearl.png")
chipSpriteSheet = spritesheet("chip icons.png")
background = pygame.image.load("background.png")
backgroundRect = background.get_rect()

pygame.font.init() # you have to call this at the start if you want to use this module.
monospaceFont = pygame.font.SysFont("Monospace", 12, bold=True)

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
	def __init__(self, pos, team):
		self.pos = pos
		self.team = team
		self.pokemon = pokemon(randint(1,493),randint(1,15))
		self.invulnTimer = 0
		
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
		"""attempts to move to tile at x,y"""
		newX = self.pos[0]+x
		newY = self.pos[1]+y
		if newX<0 or newX>5 or newY<0 or newY>2:	#catch out of bounds
			return
		for entity in pokemonEntities:	#catch collisions
			if entity.pos == self.pos:	#don't check self
				continue
			if entity.pos == (newX,newY):
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
		if boardTeam[x][y]==0 or self.team==boardTeam[x][y]:
			#move allowed
			self.pos = x,y
			
	def hit(self,damage,flinch):
		if self.invulnTimer == 0: #if flinched don't get hit
			self.pokemon.totalStats[0] -= damage
			if flinch:
				self.invulnTimer = 60
			
	def tick(self):
		if self.invulnTimer > 0 and gameTickAlias == BattleTick:
			self.invulnTimer -= 1
		

class Chip():
	def __init__(self, Id):
		self.Id = Id
		self.getIconSprite()
		
	def getIconSprite(self):
		self.icon = chipSpriteSheet.getSpriteById(self.Id,20,16,16)

class AttackEntity():
	"""handles animation and timing of attacks, should be created upon using an attack
	Data responsible for:
	Team
	animation
	damage
	
	"""
	def __init__(self, pos):
		self.pos = pos
		self.team = 1
		self.spritesheet = spritesheet("chip icons.png")
		self.imageStrip = self.spritesheet.load_strip([0,0,16,16],20)
		
	def tick(self):
		"""called each frame, should update animation and """
def drawAttackQueue():
	global attackQueue
	offset = len(attackQueue)*2
	for attack in attackQueue:
		#draw attack relative to player
		chipSprite = chipSpriteSheet.getSpriteById(attack,20,16,16,colorkey=0)
		chipRect = chipSprite.get_rect()
		chipRect.center = player.pos[0]*tileWidth+tileWidth/2-offset, player.pos[1]*tileHeight+tileHeight-offset
		screen.blit(chipSprite,chipRect)
		offset-=2

def drawBoard():
	for i in range(6):
		for j in range(3):
			#check type
			tile = pygame.image.load("tile path.png")
			tileRect = tile.get_rect()
			tileRect.top = j*tileHeight+tileWidth
			tileRect.left = i*tileWidth
			
			if boardTeam[i][j] == 0:
				tileFrameImage = "tile border gray.png"
			elif boardTeam[i][j] == 1:
				tileFrameImage = "tile border red.png"
			elif boardTeam[i][j] == 2:
				tileFrameImage = "tile border blue.png"
			
			#print("drawing tile",tileFrameImage,"at",i,j)
			tileFrame = pygame.image.load(tileFrameImage)
			tileFrameRect = tileFrame.get_rect()
			tileFrameRect.left = i*tileWidth
			tileFrameRect.top = j*tileHeight+tileWidth
			
			screen.blit(tile, tileRect)
			screen.blit(tileFrame, tileFrameRect)
					
def drawGame():
	screen.blit(background, backgroundRect)
	drawBoard()
	#sort entities from back to front for drawing
	pokemonEntities.sort(key=lambda x: x.pos[1])
	for entity in pokemonEntities:	#draw all entities
		entityX = entity.pos[0]*tileWidth+tileHeight
		entityY = entity.pos[1]*tileHeight+tileWidth
		entity.pokemon.rect.center = entityX, entityY
		if entity.team==1:
			entityImage = pygame.transform.flip(entity.pokemon.image,True,False)
		else:
			entityImage = entity.pokemon.image
		if entity.invulnTimer%2 == 0:
			screen.blit(entityImage, entity.pokemon.rect)
		
	for entity in pokemonEntities: 
		entityHpText = monospaceFont.render(str(entity.pokemon.totalStats[0]), False, (0,0,0))
		entityX = entity.pos[0]*tileWidth+tileHeight
		entityY = entity.pos[1]*tileHeight+tileWidth
		screen.blit(entityHpText,(entityX-10, entityY+25))
		
	drawAttackQueue()
	
	if frameCount < turnFrames:
		timerText = monospaceFont.render(str(frameCount), False, (255,255,255))
	else:
		timerText = monospaceFont.render("Press R to open custom!", False, (255,255,255))

	screen.blit(timerText,(0,0))
	

def hitTile(pos, damage, damageType, team, flinch):
	#print("hitTile",pos)
	for entity in pokemonEntities:
		if entity.pos==pos and entity.team!=team:
			#print("hit",pos,"for",damage,"damage")
			entity.hit(damage, flinch)
			return True

def shootRow(pos, damage, damageType, team, flinch):
	#pos is tile of player
	for i in range(pos[0],6):
		if hitTile((i,pos[1]),damage, damageType, team, flinch):
			return True

def sliceWide(pos, damage, damageType, team, flinch):
	x = pos[0]+1
	hitTile((x,pos[1]-1), damage, damageType, team, flinch)
	hitTile((x,pos[1]), damage, damageType, team, flinch)
	hitTile((x,pos[1]+1), damage, damageType, team, flinch)

def TitleScreen():
	global gameTickAlias
	textsurface = monospaceFont.render("Pokemon Battle Network", False, (255,255,255))
	screen.blit(textsurface,(40, 25))
	pygame.display.flip()
	for event in pygame.event.get():
		if event.type == pygame.KEYDOWN:
			gameTickAlias = CustomTick

				
def BattleTick():
	global gameTickAlias
	global frameCount
	global attackQueue
	global cursor
	global hand
	for event in pygame.event.get():
		if event.type == pygame.QUIT: 
			sys.exit()
		if event.type == pygame.KEYDOWN and event.key == K_LEFT:
			player.moveDirection("left")
		if event.type == pygame.KEYDOWN and event.key == K_RIGHT:
			player.moveDirection("right")
		if event.type == pygame.KEYDOWN and event.key == K_UP:
			player.moveDirection("up")
		if event.type == pygame.KEYDOWN and event.key == K_DOWN:
			player.moveDirection("down")
		if event.type == pygame.KEYDOWN and event.key == K_SPACE:
			if attackQueue:
				attackAlias = attackAliases[attackQueue.pop()]
				attackAlias((player.pos[0],player.pos[1]),10,"lol there's no type yet",1,True)
		if event.type == pygame.KEYDOWN and event.key == K_r:
			if frameCount >= turnFrames:
				#print("enter custom")
				gameTickAlias = CustomTick
				frameCount = 0
					
	for enemy in enemies:
		if randint(0,10)==0:
			moves = ["left","right","up","down"]
			enemy.moveDirection(moves[randint(0,3)])
			
	for entity in pokemonEntities:
		if entity.pokemon.totalStats[0]<= 0:
			pokemonEntities.remove(entity)
			enemies.remove(entity)
	if not enemies:
		print("good job")
		gameTickAlias = TitleScreen
			
	drawGame()
	
	if frameCount >= turnFrames:
		frameCount = turnFrames
	else:
		frameCount += 1
		
		
def CustomTick():
	global gameTickAlias
	global attackQueue
	global cursor
	global selectedChips
	global selected
	global hand
	"""open custom menu, handle cursor and chip selection, draw chips"""
	#drawCustom
	drawGame()
	drawCustom(cursor)
	
	
	
	
	oldCursor = cursor
	for event in pygame.event.get():
		if event.type == pygame.QUIT: 
			sys.exit()
		if event.type == pygame.KEYDOWN and event.key == K_RIGHT:
			if cursor == len(hand)-1:
				cursor = -1
			elif cursor==-1:
				cursor = 0
			elif cursor%5 == 4:
				cursor = -1
			elif cursor<len(hand)-1:
				cursor += 1
		if event.type == pygame.KEYDOWN and event.key == K_LEFT:
			if cursor==0 or cursor==5:
				cursor = -1
			elif cursor==-1:
				cursor = 4
			else:
				cursor -= 1
		if event.type == pygame.KEYDOWN and event.key == K_UP:
			if cursor>=5:
				cursor -= 5
		if event.type == pygame.KEYDOWN and event.key == K_DOWN:
			if cursor>=0 and cursor<len(hand)-5:
				cursor += 5
		if event.type == pygame.KEYDOWN and event.key == K_SPACE:
			#select current chip
			if cursor==-1:
				#close custom
				#load selectedChips attacks into attackQueue
				if selectedChips: #if player selects new chips don't keep ones from last turn
					attackQueue = []
				while len(selectedChips) > 0:
					attackQueue.append(hand[selectedChips.pop()])
				#remove selected chips from hand
				newHand = []
				for i in range(len(hand)):
					if not selected[i]:
						newHand.append(hand[i])
				hand = newHand
				print("hand =",hand)
				print("selectedChips =",selectedChips)
				#refill hand
				cursor = 0
				for i in range(customDraw-len(hand)):
					#print("refilled chip")
					if(folder):
						hand.append(folder.pop())
				print(hand)
				print("folder =",folder)
				selected = [False for i in range(customDraw)]
						
				gameTickAlias = BattleTick
			elif len(selectedChips) < 5 and not selected[cursor]:
				selectedChips.append(cursor) #select chip by adding it's cursor pos to selectedChips
				selected[cursor] = True
				
				
				
		if event.type == pygame.KEYDOWN and event.key == K_BACKSPACE:
			#select current chip
			if len(selectedChips) > 0:
				selected[selectedChips.pop()] = False #pop and deselect chip
		
		
		
	
	

attackAliases = [shootRow, sliceWide]
player = PokemonEntity((0,1),1)
enemies = [PokemonEntity((5,0),2),PokemonEntity((5,1),2),PokemonEntity((5,2),2)]
pokemonEntities.append(player)
pokemonEntities += enemies
frameCount = 0
gameTickAlias = TitleScreen
attackQueue = []
attackEntity = AttackEntity((0,0))
#shuffle folder at beginning of battle
folder = [0,1,0,1,1,0,1,0,0,1,0,0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0,1]
customDraw = 8 #number of chips to draw each turn
hand = []
cursor = 0
for i in range(customDraw):
	hand.append(folder.pop())
print("first hand =",hand)
selectedChips = []
selected = [False for i in range(customDraw)]

def drawCustom(cursor):
	cursorSprite = pygame.image.load("custom cursor.png")
	cursorRect = cursorSprite.get_rect()
	customWindow = pygame.image.load("custom frame.png")
	customWindowRect = customWindow.get_rect()
	screen.blit(customWindow, customWindowRect)
	#draw each chip
	pos = 0
	for chip in hand:
		if not selected[pos]:
			chipSprite = chipSpriteSheet.getSpriteById(chip,20,16,16,colorkey=0)
			chipRect = chipSprite.get_rect()
			chipRect.left = pos%5*17+11
			chipRect.top = pos//5*28+108
			screen.blit(chipSprite,chipRect)
		pos += 1
	#draw selectedChips chips
	pos = 0
	for chip in selectedChips:
		chipSprite = chipSpriteSheet.getSpriteById(hand[chip],20,16,16,colorkey=0)
		chipRect = chipSprite.get_rect()
		chipRect.left = 103
		chipRect.top = pos*17+17
		screen.blit(chipSprite,chipRect)
		pos += 1
	#draw cursor
	if cursor==-1:
		#replace this with a special cursor to fit OK button
		cursorRect.left = 5*17+10
		cursorRect.top = 107
	else:
		cursorRect.left = cursor%5*17+10
		cursorRect.top = cursor//5*28+107
	screen.blit(cursorSprite, cursorRect)
	
	


while True:
	start = datetime.now()
	gameTickAlias()
	end = datetime.now()
	exec_time = end - start
	sleepTime = 1/30-exec_time.total_seconds()
	for entity in pokemonEntities:
		entity.tick()
		
	pygame.display.flip()
	if(sleepTime>0):
		time.sleep(sleepTime)
