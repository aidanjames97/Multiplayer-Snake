import socket
import rsa
from _thread import *
import re
import pygame

# color constants
BLACK = (0, 0 ,0)
GREY = (210, 210, 210)

# size constants
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500
BLOCK_SIZE = 20

# server details
server_ip = '127.0.0.1' 
server_port = 5555

# init keys
public_Key, private_Key = rsa.newkeys(1024)
# create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Connect to the server
client_socket.connect((server_ip, server_port))

# for drawing snake and snacks (as to not import snake class)
class cube():
    rows = 20
    w = 500
    def __init__(self, start, color, dirnx=1, dirny=0,):
        self.pos = start
        self.dirnx = dirnx
        self.dirny = dirny # "L", "R", "U", "D"
        thruple = re.findall(r'\((\d+), (\d+), (\d+)\)', color)
        self.color = (int(thruple[0][0]), int(thruple[0][1]), int(thruple[0][2]))

    def move(self, dirnx, dirny):
        self.dirnx = dirnx
        self.dirny = dirny
        self.pos  = (self.pos[0] + self.dirnx, self.pos[1] + self.dirny)
            

    def draw(self, surface, eyes=False):
        dis = self.w // self.rows
        i = int(self.pos[0])
        j = int(self.pos[1])
        
        pygame.draw.rect(surface, self.color, (i*dis+1,j*dis+1,dis-2,dis-2))
        if eyes:
            centre = dis//2
            radius = 3
            circleMiddle = (i*dis+centre-radius,j*dis+8)
            circleMiddle2 = (i*dis + dis -radius*2, j*dis+8)
            pygame.draw.circle(surface, (0,0,0), circleMiddle, radius)
            pygame.draw.circle(surface, (0,0,0), circleMiddle2, radius)

# for messaging (sending)
def msg_thread(enc, client_socket):
    while True:
        try:
            msg = "m:"
            msg += input()
            emsg = enc(msg)
            client_socket.send(emsg)
        except:
            break

def main():
    print("\n - Main Start -")
    try:
        # exchange keys w/ server
        client_socket.send(public_Key.save_pkcs1("PEM"))
        public_partner = rsa.PublicKey.load_pkcs1(client_socket.recv(1024))

        def enc(msg):
            if msg == "":
                return False
            else:
                return rsa.encrypt(msg.encode('ascii'), public_partner)

        def dec(msg):
            return rsa.decrypt(msg, private_Key).decode('ascii')

        start_new_thread(msg_thread, (enc, client_socket))

        # pygame initialization stuff
        pygame.init() # initialize pygame
        screen = pygame.display.set_mode((500, 500)) # set screen (w,h)
        pygame.display.set_caption("Snake Game") # set caption (top of window)

        # input types so player can see them
        print("\nInputs:")
        print("1. up: changes the direction of the snake to up/north")
        print("2. down: changes the direction of the snake to down/south")
        print("3. left: changes the direction of the snake to left/west")
        print("4. right: changes the direction of the snake to right/east")
        print("5. spacebar: reset the length of the snake and start from a random location")
        print("6. esc: quits the application")
        print("7. g: a default command. Requests the current game state\n")
        
        # draw snacks 
        def draw_snack(pos):
            c = cube((pos[0], pos[1]), '(0, 250, 0)')
            c.draw(screen)
        
        # draw snake
        def draw_snake(pos, eyes):
            s = cube((pos[0], pos[1]), pos[2])
            s.draw(screen, eyes)
            
        # draw game grid
        def draw_grid():
            size = 500 // 20
            x = 0
            y = 0
            for c in range(20):
                x = x + size
                y = y + size
                pygame.draw.line(screen, (255,255,255), (x,0),(x,500))
                pygame.draw.line(screen, (255,255,255), (0,y),(500,y))

            gameState = inp.split("|")
            arr = gameState[0].split("**")

            snakeLocation = [] # final array
            # paring game info into a 2d array of tuples
            i = 0
            for a in arr:
                snakes = a.split(":")   
                ss = snakes[0].split("*")
                eye = True
                for s in ss:
                    tupleMatch = re.findall(r'\((\d+), (\d+)\)', s)

                    for x, y in tupleMatch:
                        tuples = (x, y, snakes[1], eye)
                        eye = False

                    row = []
                    for t in tuples:
                        row.append(t)
                    
                    snakeLocation.append(row)
                    i += 1

                snackTuples = gameState[1].split('**')
                snacksLocation = [[int(num) for num in tuple_str.strip('()').split(', ')] for tuple_str in snackTuples]

        quitGame = False
        while not quitGame:
            eventSent = False
            # requesting new game state if server is not going to send it already
            if not eventSent:
                msg = "c:getd"
                getMsg = enc(msg)
                if getMsg:
                    client_socket.send(getMsg)

            inp = client_socket.recv(1024).decode()
            if inp.startswith("$in$"):
                data = dec(client_socket.recv(1024)) 
                print(data)         
                inp = client_socket.recv(1024).decode()

            if(inp != "E1"):
                gameState = inp.split("|")
                arr = gameState[0].split("**")

                snakeLocation = [] # final array
                # paring game info into a 2d array of tuples
                i = 0
                for a in arr:
                    snakes = a.split(":")
                    ss = snakes[0].split("*")
                    eye = True
                    for s in ss:
                        tupleMatch = re.findall(r'\((\d+), (\d+)\)', s)

                        for x, y in tupleMatch:
                            tuples = (x, y, snakes[1], eye)
                            eye = False

                        row = []
                        for t in tuples:
                            row.append(t)
                        
                        snakeLocation.append(row)
                        i += 1
                
                snackTuples = gameState[1].split('**')
                snacksLocation = [[int(num) for num in tuple_str.strip('()').split(', ')] for tuple_str in snackTuples]
            else:
                break

            # drawing game we have parsed from server
            screen.fill(BLACK) # fill screen background / wipe screen of past drawings

            # drawing snake w/ eyes at head
            for sn in snakeLocation:
                draw_snake((sn[0], sn[1], sn[2]), sn[3])
            
            # drawing snacks
            for cb in snacksLocation:
                draw_snack((cb[0], cb[1]))

            draw_grid() # drawing grid onto screen

            # updating display
            pygame.display.update()

        # close the socket and quit game
        pygame.quit()
        client_socket.close()

    except Exception as e:
        print(e)
        print(f"Server forced to close closing client ...")


if __name__ == "__main__":
    main()