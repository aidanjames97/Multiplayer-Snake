import numpy as np
import socket
from _thread import *
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

public_Key, private_Key = rsa.newkeys(1024) # init keys

game = SnakeGame(rows)
game_state = "" 
last_move_timestamp = time.time()
interval = 0.2
moves_queue = set()

clients = {} # for all clients

# needed for multiple players
rgb_colors = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
}
rgb_colors_list = list(rgb_colors.values())

# CHANGE
def broadcast_Msg(message, unique_id):
    print(f"Broadcasting: {message}")
    for client_unique_id, (conn, enc) in clients.items():
        try:
            if client_unique_id != unique_id: 
                conn.send(enc(f'User {unique_id} says: {message}'))
                
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
    global game_state, game, moves_queue, public_Key, private_Key

    try:
        # setup encryption
        server_der = public_Key.save_pkcs1(format="DER")
        conn.send(server_der)

        client_der = conn.recv(1024)
        client_public_key = rsa.PublicKey.load_pkcs1(client_der, format="DER")

        unique_id = str(uuid.uuid4())
        color = random.choice(rgb_colors_list)
        game.add_player(unique_id, color)

        def enc(msg):
                return rsa.encrypt(msg.encode('ascii'), client_public_key)

        def dec(msg):
            try:
                return rsa.decrypt(msg, private_Key).decode('ascii')
            except:
                print(" ** Decrypt Fail **")
                return False

        clients[unique_id] = (conn, enc)

        exit_game_thread = threading.Event()
        # so we dont have multiple clients running game (speed increase)
        if len(clients) == 1:    
            start_new_thread(game_thread, (exit_game_thread, ))

        while not exit_flag.is_set():
            data = dec(conn.recv(1024))
            
            if not data or data == "c:quit":
                break

            move = None
            if data.startswith("c:"): 
                if data == "c:reset":
                    # Handle client reset game
                    game.reset_player(unique_id)
                elif data in ["c:up", "c:down", "c:left", "c:right"]:
                    # Handle client movement
                    move = data[2:] # removing "c:"
                    moves_queue.add((unique_id, move))

                # send game start (after message if needed)
                conn.send(game_state.encode())

            else:
                if data.startswith("m:"):
                    # user message, parse and call broadcast msg
                    msg = data.split("m:", 1)[1].strip()
                    start_new_thread(broadcast_Msg, (msg, unique_id))

    except Exception as e:
        # Handle unexpected client disconnect
        print(f"[Ex] - Client_thread: {e}")

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

# main server function
def main() : 
    print("\n - Main Start -\n")
    global counter, game, public_partner, public_Key

    while True:
        try:
            conn, addr = s.accept()
            exit_flag = threading.Event() # for exiting threads safely

            start_new_thread(client_thread, (conn, addr, exit_flag))
        except Exception as e:
            exit_flag.set() # to close threads
            print(f"Exception in main: {e}")
            break

# call main when script ran
if __name__ == "__main__" : 
    try:
        main()
    except KeyboardInterrupt:
        s.close()
        print("\nServer closed")