import pygame


WINDOW_WIDTH = 250
WINDOW_HEIGHT = 250
TILE_SIZE = 20


class Square:

    def __init__(self, x, y, colour):
        self.x = x
        self.y = y
        self.colour = colour


    def draw(self, window):
        sx = self.x * TILE_SIZE + WINDOW_WIDTH / 2 - TILE_SIZE / 2
        sy = self.y * TILE_SIZE + WINDOW_HEIGHT / 2 - TILE_SIZE / 2
        pygame.draw.rect(window, self.colour, (sx, sy, TILE_SIZE, TILE_SIZE))


class World:
    TileSize = 20

    def __init__(self, renderer):
        self.renderer = renderer
        self.world_data = {}


    def update_square(self, x, y, colour):
        if (x, y) in self.world_data:
            self.world_data[(x, y)].colour = colour
        else:
            self.world_data[(x, y)] = Square(x, y, colour)


    def update_squares(self):
        for x, y in self.renderer.requested:
            self.update_square(x, y, pygame.Color(255, 0, 0))
        for x, y in self.renderer.rendered_chunks:
            self.update_square(x, y, pygame.Color(0, 255, 0))


    def draw(self, window):
        for square in self.world_data.values():
            square.draw(window)


class Minimap:
    def __init__(self, renderer):
        pygame.init()

        self.renderer = renderer
        self.window = pygame.display.set_mode((250, 250))
        self.world = World(renderer)
        self.world.update_square(0, 0, pygame.Color(255, 0, 0))


    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                close()
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
