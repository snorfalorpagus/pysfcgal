import pytest

import pysfcgal.sfcgal as sfcgal
from pysfcgal.sfcgal import (Point, LineString, Polygon, MultiPoint,
    MultiLineString, MultiPolygon, GeometryCollection)
import geom_data

def test_version():
    print(sfcgal.sfcgal_version())

geometry_names, geometry_values = zip(*geom_data.data.items())

@pytest.mark.parametrize("geometry", geometry_values, ids=geometry_names)
def test_integrity(geometry):
    geom = sfcgal.shape(geometry)
    # data = sfcgal.mapping(geom)
    # TODO: use a comparison that doesn't care about tuples vs lists
    # assert(geometry == data)

@pytest.mark.parametrize("geometry", geometry_values, ids=geometry_names)
def test_wkt_write(geometry):
    geom = sfcgal.shape(geometry)
    wkt = geom.wkt
    assert(wkt)
    data = sfcgal.mapping(sfcgal.read_wkt(wkt))
    assert(geometry == data)

def test_point_in_polygon():
    """Tests the intersection between a point and a polygon"""
    point = Point(2, 3)
    polygon1 = Polygon([[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]])
    polygon2 = Polygon([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
    assert(polygon1.intersects(point))
    assert(point.intersects(polygon1))
    assert(not polygon2.intersects(point))
    assert(not point.intersects(polygon2))
    result = point.intersection(polygon1)
    assert(isinstance(result, Point))
    assert(not result.is_empty)
    assert(result.x == point.x)
    assert(result.y == point.y)
    result = point.intersection(polygon2)
    assert(isinstance(result, GeometryCollection))
    assert(result.is_empty)

def test_intersection_polygon_polygon():
    """Tests the intersection between two polygons"""
    polygon1 = Polygon([[0, 0], [5, 0], [5, 5], [0, 5], [0, 0]])
    polygon2 = Polygon([[-1, -1], [1, -1], [1, 1], [-1, 1], [-1, -1]])
    assert(polygon1.intersects(polygon2))
    assert(polygon2.intersects(polygon1))
    polygon3 = polygon1.intersection(polygon2)
    assert(polygon3.area == 1.0)
    # TODO: check coordinates

def test_point():
    point1 = Point(4,5,6)
    assert(point1.x == 4.0)
    assert(point1.y == 5.0)
    assert(point1.z == 6.0)
    assert(point1.has_z)

    point2 = Point(4,5)
    assert(point2.x == 4.0)
    assert(point2.y == 5.0)
    with pytest.raises(sfcgal.DimensionError):
        z = point2.z
    assert(not point2.has_z)

def test_line_string():
    line = LineString([(0,0), (0, 1), (1, 1.5), (1, 2)])
    assert(len(line) == 4)
    
    # test access to coordinates
    coords = line.coords
    assert(len(coords) == 4)
    assert(coords[0] == [0.0,0.0])
    assert(coords[-1] == [1.0,2.0])
    assert(coords[0:2] == [[0.0,0.0], [0.0, 1.0]])

def test_geometry_collection():
    geom = sfcgal.shape(geom_data.data["gc1"])
    # length
    assert(len(geom) == 3)
    # iteration
    for g in geom.geoms:
        print(geom)
    # indexing
    g = geom.geoms[1]
    assert(isinstance(g, LineString))
    g = geom.geoms[-1]
    assert(isinstance(g, Polygon))
    gs = geom.geoms[0:2]
    assert(len(gs) == 2)
    # conversion to lists
    gs = list(geom.geoms)
    assert([g.__class__ for g in gs] == [Point, LineString, Polygon])
