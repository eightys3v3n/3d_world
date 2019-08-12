import pygame, itertools


WINDOW_WIDTH = 500
WINDOW_HEIGHT = 500
TILE_SIZE = 20


class Square:

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
    TileSize = 20

    def __init__(self, renderer, generator, world_client):
        self.renderer = renderer
        self.generator = generator
        self.world_client = world_client
        self.world_data = {}


    def update_square(self, x, y, colour=None, border_colour=None):
        if (x, y) in self.world_data:
            if colour is not None:
                self.world_data[(x, y)].colour = colour
            if border_colour is not None:
                self.world_data[(x, y)].border_colour = border_colour
        else:
            if colour is None:
                colour = pygame.Color(255, 255, 255)
            if border_colour is None:
                border_colour = pygame.Color(255, 255, 255)
            self.world_data[(x, y)] = Square(x, y, colour, border_colour)


    def update_squares(self):
        for x, y in self.renderer.requested:
            self.update_square(x, y, colour=pygame.Color(100, 100, 100))
        for x, y in self.renderer.pending_chunks:
            self.update_square(x, y, colour=pygame.Color(255, 0, 0))
        for x, y in self.generator.recently_requested.keys():
            self.update_square(x, y, border_colour=pygame.Color(0, 0, 255))
        for x, y in self.renderer.rendered_chunks.keys():
            self.update_square(x, y, colour=pygame.Color(0, 255, 0), border_colour=pygame.Color(0, 255, 0))
 


    def draw(self, window):
        for square in self.world_data.values():
            square.draw(window)


class Minimap:

    def __init__(self, renderer, generator, world_client):
        pygame.init()

        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minimap")
        self.world = World(renderer, generator, world_client)


    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
        self.world.update_squares()
        self.draw()


    def draw(self):
        self.window.fill(pygame.Color(0, 0, 0))

        self.world.draw(self.window)

        pygame.display.flip()


    def close(self):
        pygame.quit()



if __name__ == '__main__':
    minimap = Minimap()
    minimap.loop()
