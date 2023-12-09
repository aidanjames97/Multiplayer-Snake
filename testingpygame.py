import pygame

# color constants
BLACK = (0, 0 ,0)
GREY = (210, 210, 210)

# size constants
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500
BLOCK_SIZE = 20

print("- started -")

# pygame initialization stuff
pygame.init() # initialize pygame
screen = pygame.display.set_mode((500, 500)) # set screen (w,h)
pygame.display.set_caption("Snake Game") # set caption (top of window)

while True:
    try:
        screen.fill(BLACK)
        pygame.display.update()
    except:
        break

print("close")
pygame.quit()