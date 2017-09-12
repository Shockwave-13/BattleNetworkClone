import sys, pygame
from spritesheet import spritesheet
from pygame.locals import *
from pygame import Rect
from random import randint, shuffle
from datetime import datetime
import time
pygame.init()



size = width, height = 480, 200
tileWidth = 80
tileHeight = 40
turnFrames = 100
backgroundColor = 0, 0, 0
screen = pygame.display.set_mode(size)

#resources
pokemonSpriteSheet = spritesheet("diamond-pearl.png")
chipSpriteSheet = spritesheet("chip icons.png")
background = pygame.image.load("background.png")
backgroundRect = background.get_rect()

pygame.font.init()
monospaceFont = pygame.font.SysFont("Monospace", 12, bold=True)
codeFont = pygame.font.SysFont("Comic Sans MS",7,bold=True)

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
		self.moveLock = False
		
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
	def __init__(self, Id, code):
		self.Id = Id
		self.code = code
		
	def getIconSprite(self):
		self.icon = chipSpriteSheet.getSpriteById(self.Id,20,16,16)

class AttackEntity():
	"""handles animation and timing of attacks, should be created upon using an attack
	Data responsible for:
	pos
	team
	endFrame
	
	Data handled by children:
	animation?
	damage
	warning frames?
	movement
	
	"""
	def __init__(self, user, endFrame, spriteFile, spriteCoords):
		#self.pos = pos
		#self.team = team
		self.user = user
		self.pos = user.pos
		self.team = user.team
		self.attackTimer = 0
		self.endFrame = endFrame
		self.spritesheet = spritesheet(spriteFile)
		self.strip = self.spritesheet.load_strip(spriteCoords,endFrame,colorkey=-1)
		self.rect = Rect(0,0,80,80)
		#self.spritesheet = spritesheet("chip icons.png")
		#self.imageStrip = self.spritesheet.load_strip([0,0,16,16],20)
		
	def tick(self):
		"""called each frame, should update animation and """
		attackTimer += 1
		
		
class ShootAttack(AttackEntity):
	"""	a child of AttackEntity for shooting attacks, will call shootRow on shootFrame and will end on endFrame
		ToDo: get sprites and add a spriteSheet and extra data to select different sprites"""
	def __init__(self,user, damage, damageType, flinch, shootFrame, endFrame, spriteFile):
		AttackEntity.__init__(self, user, endFrame, spriteFile, [0,0,80,80])
		self.damage = damage
		self.damageType = damageType
		self.flinch = flinch
		self.shootFrame = shootFrame
		user.moveLock = True
		
	def tick(self):
		#player should be immobile upon activating
		print("shoot tick",self.attackTimer)
		if self.attackTimer == self.shootFrame:	#could have this factor in speed
			shootRow(self.pos, self.damage, self.damageType, self.team, self.flinch)
		if self.attackTimer >= self.endFrame:
			#free player
			self.user.moveLock = False
			
		self.attackTimer += 1
		
class SwordAttack(AttackEntity):
	def __init__(self,user, damage, damageType, flinch, shootFrame, endFrame, spriteFile):
		AttackEntity.__init__(self, user, endFrame, spriteFile, [0,0,160,120])
		self.damage = damage
		self.damageType = damageType
		self.flinch = flinch
		self.shootFrame = shootFrame
		user.moveLock = True
		
	def tick(self):
		#player should be immobile upon activating
		print("shoot tick",self.attackTimer)
		if self.attackTimer == self.shootFrame:	#could have this factor in speed
			sliceWide(self.pos, self.damage, self.damageType, self.team, self.flinch)
		if self.attackTimer >= self.endFrame:
			#free player
			self.user.moveLock = False
			
		self.attackTimer += 1
	
class MultiAttack(AttackEntity):
	"""	an attack entity that handles multihits
		creates an attack entity each interval for multiCount times"""
	def __init__(self,user, damage, damageType, flinch, multiCount, interval, attack):
		AttackEntity.__init__(self, user, multiCount*interval) #end time depends on number of hits
		
	def tick(self):
		if self.attackTimer%interval == 0:
			#clone attack
			attackClone = None
			AttackEntities.append(attackClone)
		
		
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
	
	for attack in attackEntities:
		x = attack.pos[0]*tileWidth+tileHeight
		y = attack.pos[1]*tileHeight+tileWidth
		
		attack.rect.center = x,y
		attackImage = attack.strip[attack.attackTimer%len(attack.strip)]
		if attack.team==1:
			attackImage = pygame.transform.flip(attackImage,True,False)
		screen.blit(attackImage, attack.rect)
		
	drawAttackQueue()
	
	if frameCount < turnFrames:
		timerText = monospaceFont.render(str(frameCount), False, (255,255,255))
	else:
		timerText = monospaceFont.render("Press R to open custom!", False, (255,255,255))

	screen.blit(timerText,(0,0))
	
def drawCustom(cursor):
	cursorSpriteSheet = spritesheet("custom cursor.png")
	cursorRect = Rect(0,0,18,18)
	cursorSprites = cursorSpriteSheet.load_strip(cursorRect,2,colorkey=-1)
	#cursorSprite = pygame.image.load("custom cursor.png")
	#cursorRect = cursorSprite.get_rect()
	
	customWindow = pygame.image.load("custom frame.png")
	customWindowRect = customWindow.get_rect()
	screen.blit(customWindow, customWindowRect)
	
	handSprites = [chipSpriteSheet.getSpriteById(chip[0],20,16,16,colorkey=0) for chip in hand]
	handRects = [handSprite.get_rect() for handSprite in handSprites]
	for i in range(len(hand)):
		handRects[i].left = i%5*17+11
		handRects[i].top = i//5*28+108
		
	#draw each chip
	for i in range(len(hand)):
		if not selected[i]:
			#chipSprite = chipSpriteSheet.getSpriteById(chip[0],20,16,16,colorkey=0)
			
			screen.blit(handSprites[i],handRects[i])
		
		code = codeFont.render(hand[i][1], False, (255,255,0))
		screen.blit(code,(handRects[i].left+4,handRects[i].top+15))
	#draw selectedChips chips
	pos = 0
	for chip in selectedChips:
		chipSprite = handSprites[chip]
		chipRect = handRects[chip]
		chipRect.left = 103
		chipRect.top = pos*17+17
		screen.blit(chipSprite,chipRect)
		pos += 1
	#draw cursor
	if cursor==-1:
		#replace this with a special cursor to fit OK button
		cursorRect.left = 95
		cursorRect.top = 107
	else:
		cursorRect.left = cursor%5*17+10
		cursorRect.top = cursor//5*28+107
	screen.blit(cursorSprites[customCounter//5], cursorRect)
	

def hitTile(pos, damage, damageType, team, flinch):
	#print("hitTile",pos)
	for entity in pokemonEntities:
		if entity.pos==pos and entity.team!=team:
			#print("hit",pos,"for",damage,"damage")
			entity.hit(damage, flinch)
			return True

def shootRow(pos, damage, damageType, team, flinch):
	#pos is tile of player
	if team == 1:
		#print("shooting right on row",pos[1])
		shootRange = range(pos[0],6)
	elif team == 2:
		#print("shooting left on row",pos[1])
		shootRange = range(pos[0],-1,-1)
	for i in shootRange:
		if hitTile((i,pos[1]),damage, damageType, team, flinch):
			return True

def sliceWide(pos, damage, damageType, team, flinch):
	if team ==1:
		x = pos[0]+1
	elif team==2:
		x = pos[0]-1
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
					#attackAlias = attackAliases[attackQueue.pop()]
					#attackAlias(player.pos,10,"lol there's no type yet",1,True)
				
					attackId = attackQueue.pop()			
					#create AttackEntity corresponding to chip 
					if attackId == 0:
						attackEntities.append(ShootAttack(player, 10, None, True, 7, 9, "shoot.png"))
					elif attackId == 1:
						attackEntities.append(SwordAttack(player, 10, None, True, 7, 9, "wideSword.png"))
					
		if event.type == pygame.KEYDOWN and event.key == K_r:
			if frameCount >= turnFrames:
				#print("enter custom")
				gameTickAlias = CustomTick
				frameCount = 0
					
	for enemy in enemies:
		if randint(0,10)==0:
			moves = ["left","right","up","down"]
			enemy.moveDirection(moves[randint(0,3)])
		#elif randint(0,40)==0:
		#	shootRow(enemy.pos,10,0,2,True)
			
	for entity in pokemonEntities:
		if entity.pokemon.totalStats[0]<= 0:
			pokemonEntities.remove(entity)
			enemies.remove(entity)
			
	if not enemies:
		print("good job")
		#gameTickAlias = TitleScreen
		
	for attackEntity in attackEntities:
		attackEntity.tick()
		if attackEntity.attackTimer > attackEntity.endFrame:
			attackEntities.remove(attackEntity)		
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
	global customCounter
	global selectedCode
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
			#close custom
			if cursor==-1:
				
				#load selectedChips attacks into attackQueue
				if selectedChips: #if player selects new chips don't keep ones from last turn
					attackQueue = []
				while len(selectedChips) > 0:
					attackQueue.append(hand[selectedChips.pop()][0])
				#remove selected chips from hand
				newHand = []
				for i in range(len(hand)):
					if not selected[i]:
						newHand.append(hand[i])
				hand = newHand
				#print("hand =",hand)
				#print("selectedChips =",selectedChips)
				#refill hand
				cursor = 0
				for i in range(customDraw-len(hand)):
					#print("refilled chip")
					if(folder):
						hand.append(folder.pop())
				#print(hand)
				#print("folder =",folder)
				selected = [False for i in range(customDraw)]
				selectedCode = None
						
				gameTickAlias = BattleTick
				
			#select current chip
			elif len(selectedChips) < 5 and not selected[cursor] and (selectedCode == None or hand[cursor][1] == selectedCode or hand[cursor][1] == "*"):
				selectedChips.append(cursor) #select chip by adding it's cursor pos to selectedChips
				selected[cursor] = True
				if hand[cursor][1]!="*":
					selectedCode = hand[cursor][1]
				
				#print(selectedCode)
				
				
				
		if event.type == pygame.KEYDOWN and event.key == K_BACKSPACE:
			#select current chip
			if len(selectedChips) > 0:
				selected[selectedChips.pop()] = False #pop and deselect chip
				#search selected chips to update selectedCode
				tempCode = None
				for chipLocation in selectedChips:
					if hand[chipLocation][1] != None and hand[chipLocation][1]!="*":
						tempCode = hand[chipLocation][1]
						break
				selectedCode = tempCode
	#print(selectedCode)
				
				
	customCounter+=1
	if customCounter >= 10:
		customCounter = 0
		
		
	
	
#game
attackAliases = [shootRow, sliceWide]
gameTickAlias = TitleScreen
boardTeam = [[1,1,1],[1,1,1],[1,0,1],[2,0,2],[2,2,2],[2,2,2]] #each row of board 0 = neutral, 1 = red, 2 = blue
tileTypes = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
folder = [[0,"A"],[1,"A"],[0,"A"],[1,"A"],[1,"A"],[0,"A"],[1,"A"],[0,"A"],[0,"A"],[1,"A"],[0,"A"],[0,"A"],[0,"A"],[1,"A"],[0,"A"],[0,"A"],[1,"A"],[0,"A"],[0,"A"],[1,"A"],[0,"A"],[0,"A"],[1,"A"],[0,"A"],[0,"A"],[1,"A"],[0,"A"],[0,"B"],[0,"A"],[1,"*"]]
shuffle(folder)
player = PokemonEntity((0,1),1)
enemies = [PokemonEntity((4,1),2)]
pokemonEntities = []
pokemonEntities.append(player)
pokemonEntities += enemies
attackEntities = []

#battle
frameCount = 0
attackQueue = []
customDraw = 30 #number of chips to draw each turn

#custom
hand = []
cursor = 0
for i in range(customDraw):
	hand.append(folder.pop())
selectedChips = []
selected = [False for i in range(customDraw)]
selectedCode = None
customCounter = 0

	
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
