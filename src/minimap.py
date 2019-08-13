import pygame, itertools


"""This is a second window that opens along side the main game window. It can be used for debug info, a minimap, or what have you. I've used it mostly for debugging."""


WINDOW_WIDTH = 500 # Width of window.
WINDOW_HEIGHT = 500 # Height of window.
TILE_SIZE = 20 # Size of chunk squares.


class Square:
    """A Square that can be drawn in the window. Has a position, fill colour, and border colour."""

    def __init__(self, x, y, colour=None, border_colour=None):
        self.x = x
        self.y = y
        self.colour = colour
        self.border_colour = border_colour
        self.width = 2


    def draw(self, window):
        sx = self.x * TILE_SIZE + WINDOW_WIDTH / 2 - TILE_SIZE / 2
        sy = self.y * TILE_SIZE + WINDOW_HEIGHT / 2 - TILE_SIZE / 2

        if self.border_colour is not None:
            pygame.draw.rect(window, self.border_colour, (sx, sy, TILE_SIZE, TILE_SIZE), 0)
        if self.colour is not None:
            pygame.draw.rect(window, self.colour, (sx+self.width, sy+self.width, TILE_SIZE-self.width, TILE_SIZE-self.width), 0)


class World:
    """A collection of tiles and how to update them."""

    def __init__(self, renderer, generator, world_client):
        self.renderer = renderer
        self.generator = generator
        self.world_client = world_client
        self.world_data = {}


    def update_squares(self):
        """Update all the squares based on the world data and what not."""
        for x, y in self.renderer.requested:
            self.update_square(x, y, colour=pygame.Color(100, 100, 100))
        for x, y in self.renderer.pending_chunks:
            self.update_square(x, y, colour=pygame.Color(255, 0, 0))
        for x, y in self.generator.recently_requested.keys():
            self.update_square(x, y, border_colour=pygame.Color(0, 0, 255))
        for x, y in self.renderer.rendered_chunks.keys():
            self.update_square(x, y, colour=pygame.Color(0, 255, 0), border_colour=pygame.Color(0, 255, 0))


    def draw(self, window):
        """Draw all the squares."""
        for square in self.world_data.values():
            square.draw(window)


class Minimap:
    """The actual Minimap window and it's data."""

    def __init__(self, renderer, generator, world_client):
        """
        Parameters:
            renderer is the WorldRenderer from the game.
            generator is the WorldGenerator from the game.
            world_client is a WorldDataClient.
        """
        pygame.init()

        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minimap")
        self.world = World(renderer, generator, world_client)


    def update(self):
        """Update the data drawn in the minimap."""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
        self.world.update_squares()
        self.draw()


    def draw(self):
        """Draw the minimap contents."""

        self.window.fill(pygame.Color(0, 0, 0))

        self.world.draw(self.window)

        pygame.display.flip()


    def close(self):
        """Close the window."""
        pygame.quit()
