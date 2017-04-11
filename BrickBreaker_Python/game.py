# -*- coding: cp1252 -*-
try:
    # para Python2
    import Tkinter as tk 
except ImportError:
    # para Python3
    import tkinter as tk 
import random
import math
import copy
import time
import serial


ser = serial.Serial()
ser.port="COM1"
ser.baudrate=9600
ser.parity=serial.PARITY_NONE
ser.stopbits=serial.STOPBITS_ONE
ser.bytesize=serial.EIGHTBITS



#Main,Canvas
class Game(tk.Canvas):
    textDisplayed = False
    linesNb = 20
    seconds = 0

    #Propiedades de la barra
    barHeight = 20	 #Altura de la barra	
    barSpeed = 30        #Velocidad de la barra

    #Propiedades de la pelota
    ballSpeed = 4	 #Velocidad de la pelota

    #Propiedades de los ladrillos
    bricks = []
    bricksWidth = 50
    bricksHeight = 20
    bricksNbByLine = 16
    bricksColors = {
        "r": "#e74c3c",
        "g": "#2ecc71",
        "b": "#3498db",
        "t": "#1abc9c",
        "p": "#9b59b6",
        "y": "#f1c40f",
        "o": "#e67e22",
    }

    #Propiedades de la pantalla
    screenHeight = 500
    screenWidth = bricksWidth*bricksNbByLine

    #Metodo inicializa atributos 
    def __init__(self, root):
        tk.Canvas.__init__(self, root, bg="#ffffff", bd=0, highlightthickness=0, relief="ridge", width=self.screenWidth, height=self.screenHeight)
        self.pack()
        self.timeContainer = self.create_text(self.screenWidth/2, self.screenHeight*4/5, text="00:00:00", fill="#cccccc", font=("Arial", 30), justify="center")
        self.shield = self.create_rectangle(0, 0, 0, 0, width=0)
        self.bar = self.create_rectangle(0, 0, 0, 0, fill="#7f8c8d", width=0)
        self.ball = self.create_oval(0, 0, 0, 0, width=0)
        self.ballNext = self.create_oval(0, 0, 0, 0, width=0, state="hidden")
        self.level(1)
        self.nextFrame()

    
    #Este metodo se llama cada vez que un nivel es cargado
    #Restea todas las propiedades de los elementos 
    def reset(self):
        self.barWidth = 100
        self.ballRadius = 7
        self.coords(self.shield, (0, self.screenHeight-5, self.screenWidth, self.screenHeight))
        self.itemconfig(self.shield, fill=self.bricksColors["b"], state="hidden")
        self.coords(self.bar, ((self.screenWidth - self.barWidth)/2, self.screenHeight - self.barHeight, (self.screenWidth + self.barWidth)/2, self.screenHeight))
        self.coords(self.ball, (self.screenWidth/2 - self.ballRadius, self.screenHeight - self.barHeight - 2*self.ballRadius, self.screenWidth/2 + self.ballRadius, self.screenHeight - self.barHeight))
        self.itemconfig(self.ball, fill="#2c3e50")
        self.coords(self.ballNext, tk._flatten(self.coords(self.ball)))
        self.effects = {
            "ballFire": [0, 0],
            "barTall": [0, 0],
            "ballTall": [0, 0],
            "shield": [0, -1],
        }
        self.effectsPrev = copy.deepcopy(self.effects)
        self.ballThrown = False
        self.keyPressed = [False, False]
        self.losed = False
        self.won = False
        self.ballAngle = math.radians(90)
        for brick in self.bricks:
            self.delete(brick)
            del brick

    
    #Este metodo carga el nivel leyendo el archivo .txt
    def level(self, level):
        self.reset()
        self.levelNum = level
        self.bricks = []
        try:
            file = open(str(level)+".txt")
            content = list(file.read().replace("\n", ""))[:(self.bricksNbByLine*self.linesNb)]
            file.close()
            for i, el in enumerate(content):
                col = i%self.bricksNbByLine
                line = i//self.bricksNbByLine
                if el != ".":
                    self.bricks.append(self.create_rectangle(col*self.bricksWidth, line*self.bricksHeight, (col+1)*self.bricksWidth, (line+1)*self.bricksHeight, fill=self.bricksColors[el], width=2, outline="#ffffff"))
        
	#Si no hay ningun otro nivel para cargar el juego se acaba y la pantalla con el tiempo del jugador se despliega
        except IOError:
            self.displayText("GAME ENDED IN\n" + "%02d mn %02d sec %02d" % (int(self.seconds)//60, int(self.seconds)%60, (self.seconds*100)%100), hide = False)
            return
        self.displayText("LEVEL\n"+str(self.levelNum))

    #Este metodo se llama cada 1/60 de segundo
    #Refresca las propiedades de todos los elementos (posiciones, colisiones...)
    def nextFrame(self):
        if self.ballThrown and not(self.textDisplayed):
            self.moveBall()
            
        if not (self.textDisplayed):
            self.puertoSerial()
	    self.updateTime()
            
        '''if not(self.textDisplayed):
            '''
            
        self.updateEffects()

        if self.keyPressed[0]:
            self.moveBar(-game.barSpeed)
        elif self.keyPressed[1]:
            self.moveBar(game.barSpeed)

        if not(self.textDisplayed):
            if self.won:
                self.displayText("WON!", callback = lambda: self.level(self.levelNum+1))
            elif self.losed:
                self.displayText("LOST!", callback = lambda: self.level(self.levelNum))
        
        #Este metodo se llama cada 1/60 de segundo (60 frames por segundo)
        self.after(int(1000/60), self.nextFrame)

    
    
    #Mueve la barra  'x' pixeles horizontalmente
    #Si la pelota no se ha lanzado tambien se mueve
    def moveBar(self, x):
        barCoords = self.coords(self.bar)
        if barCoords[0] < 10 and x < 0:
            x = -barCoords[0]
        elif barCoords[2] > self.screenWidth - 10 and x > 0:
            x = self.screenWidth - barCoords[2]
        
        self.move(self.bar, x, 0)
        if not(self.ballThrown):
            self.move(self.ball, x, 0)
        

    
    #Este metodo se llama cada frame, mueve la pelota
    #Computa:
    #Colisiones entre la pelota y los ladrillos/paleta/pantalla
    #La posicion de la pelota usando los atributos de "ballAngle" y "ballSpeed"
    #Effectos de los ladrillos especiales 
    def moveBall(self):
        self.move(self.ballNext, self.ballSpeed*math.cos(self.ballAngle), -self.ballSpeed*math.sin(self.ballAngle))
        ballNextCoords = self.coords(self.ballNext)
        
        #Colisiones entre pelota y ladrillos
        i = 0
        while i < len(self.bricks):
            collision = self.collision(self.ball, self.bricks[i])
            collisionNext = self.collision(self.ballNext, self.bricks[i])
            if not collisionNext:
                brickColor = self.itemcget(self.bricks[i], "fill")
                #efecto "barTall" ladrillos verdes
                if brickColor == self.bricksColors["g"]:
                    self.effects["barTall"][0] = 1
                    self.effects["barTall"][1] = 240
                #efecto "shield" ladrillos azul
                elif brickColor == self.bricksColors["b"]:
                    self.effects["shield"][0] = 1
                #efecto "ballFire" ladrillos morados
                elif brickColor == self.bricksColors["p"]:
                    self.effects["ballFire"][0] += 1
                    self.effects["ballFire"][1] = 240
                #efecto "ballTall" ladrillos turquesa
                elif brickColor == self.bricksColors["t"]:
                    self.effects["ballTall"][0] = 1
                    self.effects["ballTall"][1] = 240

                if not(self.effects["ballFire"][0]):
                    if collision == 1 or collision == 3:
                        self.ballAngle = math.radians(180) - self.ballAngle
                    if collision == 2 or collision == 4:
                        self.ballAngle = -self.ballAngle
                
                #Si el ladrillo es rojo se convierte en naranja
                if brickColor == self.bricksColors["r"] :
                    self.itemconfig(self.bricks[i], fill=self.bricksColors["o"])
                #Si el ladrillo es naranja se convierne en amarillo
                elif brickColor == self.bricksColors["o"] :
                    self.itemconfig(self.bricks[i], fill=self.bricksColors["y"])
                #Si el ladrillo es amarillo(o cualquier otro colo que no sea rojo o naranja) se destruye
                else:
                    self.delete(self.bricks[i])
                    del self.bricks[i]
            i += 1

        self.won = len(self.bricks) == 0

	#Colisiones entre la pelota y la pantalla
        if ballNextCoords[0] < 0 or ballNextCoords[2] > self.screenWidth:
            self.ballAngle = math.radians(180) - self.ballAngle
        elif ballNextCoords[1] < 0:
            self.ballAngle = -self.ballAngle
        elif not(self.collision(self.ballNext, self.bar)):
            ballCenter = self.coords(self.ball)[0] + self.ballRadius
            barCenter = self.coords(self.bar)[0] + self.barWidth/2
            angleX = ballCenter - barCenter
            angleOrigin = (-self.ballAngle) % (3.14159*2)
            angleComputed = math.radians(-70/(self.barWidth/2)*angleX + 90)
            self.ballAngle = (1 - (abs(angleX)/(self.barWidth/2))**0.25)*angleOrigin + ((abs(angleX)/(self.barWidth/2))**0.25)*angleComputed
        elif not(self.collision(self.ballNext, self.shield)):
            if self.effects["shield"][0]:
                self.ballAngle = -self.ballAngle
                self.effects["shield"][0] = 0
            else :
                self.losed = True

        self.move(self.ball, self.ballSpeed*math.cos(self.ballAngle), -self.ballSpeed*math.sin(self.ballAngle))
        self.coords(self.ballNext, tk._flatten(self.coords(self.ball)))

    #Este metodo se llama cada frame para calcular el tiempo restante de los efectos
    def updateEffects(self):
        for key in self.effects.keys():
            if self.effects[key][1] > 0:
                self.effects[key][1] -= 1
            if self.effects[key][1] == 0:
                self.effects[key][0] = 0
        
        #efecto "ballFire" 
        if self.effects["ballFire"][0]:
            self.itemconfig(self.ball, fill=self.bricksColors["p"])
        else:
            self.itemconfig(self.ball, fill="#2c3e50")

        #efecto "barTall"
        if self.effects["barTall"][0] != self.effectsPrev["barTall"][0]:
            diff = self.effects["barTall"][0] - self.effectsPrev["barTall"][0]
            self.barWidth += diff*60
            coords = self.coords(self.bar)
            self.coords(self.bar, tk._flatten((coords[0]-diff*30, coords[1], coords[2]+diff*30, coords[3])))
        if self.effects["ballTall"][0] != self.effectsPrev["ballTall"][0]: #l'effet "ballTall" agrandit la taille de la balle
            diff = self.effects["ballTall"][0] - self.effectsPrev["ballTall"][0]
            self.ballRadius += diff*10
            coords = self.coords(self.ball)
            self.coords(self.ball, tk._flatten((coords[0]-diff*10, coords[1]-diff*10, coords[2]+diff*10, coords[3]+diff*10)))
        
        #efecto "shield" 
        if self.effects["shield"][0]:
            self.itemconfig(self.shield, fill=self.bricksColors["b"], state="normal")
        else:
            self.itemconfig(self.shield, state="hidden")

        self.effectsPrev = copy.deepcopy(self.effects)

    #Este metodo actualiza el timer del juego
    def updateTime(self):
        self.seconds += 1/60
        self.itemconfig(self.timeContainer, text="%02d:%02d:%02d" % (int(self.seconds)//60, int(self.seconds)%60, (self.seconds*100)%100))

    #Este metodo displiega algun texto
    def displayText(self, text, hide = True, callback = None):
        self.textDisplayed = True
        self.textContainer = self.create_rectangle(0, 0, self.screenWidth, self.screenHeight, fill="#ffffff", width=0, stipple="gray50")
        self.text = self.create_text(self.screenWidth/2, self.screenHeight/2, text=text, font=("Arial", 25), justify="center")
        if hide:
            self.after(3000, self.hideText)
        if callback != None:
            self.after(3000, callback)

    #Este metodo borra el texto
    def hideText(self):
        self.textDisplayed = False
        self.delete(self.textContainer)
        self.delete(self.text)

    #Metodo de colision
    def collision(self, el1, el2):
        collisionCounter = 0

        objectCoords = self.coords(el1)
        obstacleCoords = self.coords(el2)
        
        if objectCoords[2] < obstacleCoords[0] + 5:
            collisionCounter = 1
        if objectCoords[3] < obstacleCoords[1] + 5:
            collisionCounter = 2
        if objectCoords[0] > obstacleCoords[2] - 5:
            collisionCounter = 3
        if objectCoords[1] > obstacleCoords[3] - 5:
            collisionCounter = 4
                
        return collisionCounter
	
#Uso del puerto seial para mover la paleta
    def puertoSerial(self):
        message = ""
        game.keyPressed[0] = 0
        game.keyPressed[1] = 0
        while ser.inWaiting()>0:
            message = ser.read(1)
        if message != "":
            print message
        if message== "6":
            game.keyPressed[0] = 1
        elif message== "4":
            game.keyPressed[1] = 1
        elif message == "D" and not(game.textDisplayed):
            game.ballThrown = True
        else:
            pass
        message = ""


def eventsPress(event):
    global game, hasEvent
    
    if event.keysym == "Left":
        game.keyPressed[0] = 1
    elif event.keysym == "Right":
        game.keyPressed[1] = 1
    elif event.keysym == "space" and not(game.textDisplayed):
        game.ballThrown = True


def eventsRelease(event):
    global game, hasEvent
    
    if event.keysym == "Left":
        game.keyPressed[0] = 0
    elif event.keysym == "Right":
        game.keyPressed[1] = 0


#Inicializacion de la pantalla
root = tk.Tk()
root.title("Brick Breaker")
root.resizable(0,0)
root.bind("<Key>", eventsPress)
root.bind("<KeyRelease>", eventsRelease)

#Empezar el juego
game = Game(root)
root.mainloop()
