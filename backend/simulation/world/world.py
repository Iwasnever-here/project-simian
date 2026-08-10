from backend.simulation.world.tile import Tile


class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = []

        # create tiles
        for x in range(self.width):
            for y in range(self.height):
                self.tiles.append(Tile(x, y, "grass"))




    def get_tile(self, x, y):
        # return the tile at the given coordinates
        for tile in self.tiles:
            if tile.x == x and tile.y == y:
                return tile
        return None


    def to_dict(self):
        # TODO:
        # convert the World into a dictionary
        # that FastAPI can return as JSON
        tile_dicts = []
        for tile in self.tiles:
            tile_dicts.append({
                "x": tile.x,
                "y": tile.y,
                "terrain": tile.terrain
            })

        return {
            "width": self.width,
            "height": self.height,
            "tiles": tile_dicts
        }