__author__ = 'Ohad'

cachePath = 'MapCache'


import flask
import os
from random import choice


def get_g_map_url(x, y, z):
    base = 'https://khms{0}.google.com/kh/v=162&src=app&expIds=201527&rlbl=1&x={1}&y={2}&z={3}&s={4}'
    servers = [0, 1]
    magic = ['', 'G', 'Ga', 'Gal', 'Gali', 'Galil', 'Galile', 'Galileo']
    return base.format(choice(servers), x, y, z, choice(magic))


def get_tile_path(tile_type, x, y, z):
    """ Returns the path to the cached tile """
    return os.path.join(cachePath, tile_type, z, x, y + '.jpg')


def is_tile_in_cache(tile_type, x, y, z):
    """
    Checks if the specified tile is in the cache
    :param tile_type:   The type of tile e.g. 'sat'
    :param x:           The X-Axis coordinate of the tile
    :param y:           The Y-Axis coordinate of the tile
    :param z:           The zoom level of the tile
    :return:            Whether the tile was found in the cache
    """
    return os.path.exists(get_tile_path(tile_type, x, y, z))


def store_tile_to_cache(tile_type, x, y, z, data):
    """
    Stores the given tile to cache
    :param tile_type:   The type of tile e.g. 'sat'
    :param x:           The X-Axis coordinate of the tile
    :param y:           The Y-Axis coordinate of the tile
    :param z:           The zoom level of the tile
    :param data:        Binary data for the tile
    """
    file_path = get_tile_path(tile_type, x, y, z)
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, 'wb') as local_file:
        local_file.write(data)


def load_tile(tile_type, x, y, z):
    if is_tile_in_cache(tile_type, x, y, z):
        return
    url = get_g_map_url(x, y, z)
    print ('Tile ' + x + ', ' + y + ', ' + z + ' not found in cache, fetching from: ' + url)
    import urllib2
    try:
        response = urllib2.urlopen(url)
        if response.code == 200:
            store_tile_to_cache(tile_type, x, y, z, response.read())
    except Exception, e:
        print e


def get_tile(tile_type, x, y, z):
    load_tile(tile_type, x, y, z)
    try:
        return flask.send_file(get_tile_path(tile_type, x, y, z), mimetype='image/jpg')
    except Exception, e:
        return "File not Found" + str(e)