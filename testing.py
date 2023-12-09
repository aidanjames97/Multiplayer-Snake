import numpy as np
import socket
from _thread import *
import pickle
from snake import SnakeGame
import uuid
import time
import rsa
import random
import threading

# server = "10.11.250.207"
server = "127.0.0.1"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

counter = 0 
rows = 20 

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(2)
# s.settimeout(0.5)
print("Waiting for a connection, Server Started")

game = SnakeGame(rows)
game_state = "" 
last_move_timestamp = time.time()
interval = 0.2
moves_queue = set()

public_Key, private_Key = rsa.newkeys(1024) # init keys
clients = {} #  for all clients

# needed for multiple players
rgb_colors = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
}
rgb_colors_list = list(rgb_colors.values())

# for broadcasting to all connectied clients
def broadcast_Msg(message, sender, unique_id):
    for connect, enc in clients:
        try:
            if connect != sender: 
                sm = "$in$"
                connect.send(sm.encode())
                eMessage = enc(f'User {unique_id} says: {message}'.encode())
                connect.send(eMessage)
                
        except Exception as e:
            print(f"Error broadcasting {e}")

# handles thread (each client gets own thread)
def game_thread(exit_game_thread) : 
    global game, moves_queue, game_state 
    while not exit_game_thread.is_set():
        last_move_timestamp = time.time()
        game.move(moves_queue)
        moves_queue = set()
        game_state = game.get_state()
        while time.time() - last_move_timestamp < interval : 
            time.sleep(0.1) 

def client_thread(conn, addr, exit_flag):
    print(f"(NEW) - Connected to:{addr}")
    global game_state, moves_queue, public_Key, private_Key

    unique_id = str(uuid.uuid4())
    color = random.choice(rgb_colors_list)
    game.add_player(unique_id, color)

    def enc(msg):
            return rsa.encrypt(msg.encode('ascii'), public_partner)

    def dec(msg):
        try:
            return rsa.decrypt(msg, private_Key).decode('ascii')
        except:
            print(" ** Decrypt Fail **")
            return False

    clients[unique_id] = (conn, enc, dec)

    exit_game_thread = threading.Event()
    # so we dont have multiple clients running game (speed increase)
    if len(clients) == 1:    
        start_new_thread(game_thread, (exit_game_thread, ))

    while not exit_flag.is_set():
        try:
            inMsg = conn.recv(1024)
            if inMsg == "":
                continue

            data = dec(inMsg)

            if not data or data == "c:quit":
                break

            move = None      
            if data == "c:reset":
                # Handle client reset game
                game.reset_player(unique_id)
            elif data in ["c:up", "c:down", "c:left", "c:right"]:
                # Handle client movement
                move = data[2:] # removing "c:"
                moves_queue.add((unique_id, move))

            conn.send(game_state.encode())

            if data.startswith("m:"):
                # user message, parse and call broadcast msg
                msg = data.split("m:", 1)[1].strip()
                print(f"MESS: {msg} (calling broadcast)")
                broadcast_Msg(msg, conn, unique_id)

        except Exception as e:
            print(f"Client Thread Error: {e}")
            break

    # break will end up here
    print(f"[DISCONNECT]: {unique_id} disconnecting...")
    exit_flag.set()
    game.remove_player(unique_id)
    del clients[unique_id]
    conn.close()
    print(f"Connected clients: {len(clients)}")

    # stops thread from running snake game so when we load again it is not double speed
    # due to multiple threads calculating simultaneously
    if len(clients) == 0:
        exit_game_thread.set()

def main():
    print("\n -- Main Started -- \n")
    global counter, game, public_Key, public_partner

    exit_flag = threading.Event() # for exiting threads safely

    player = False # for closing server before anyone has joined
    while True:
        try:
            conn, addr = s.accept()
            player = True
            public_partner = rsa.PublicKey.load_pkcs1(conn.recv(1024))
            conn.send(public_Key.save_pkcs1("PEM"))
            start_new_thread(client_thread, (conn, addr, exit_flag))
        except Exception as e:
            exit_flag.set()
            print(f"Main Error: {e}")
            try:
                conn.close()
            except:
                pass
            break

    # Remove client from the list and close the connection
    ("closing server ...")
    if(player):
        conn.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        s.close()
        print("Server closed")