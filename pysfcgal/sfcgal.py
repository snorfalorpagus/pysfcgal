from _sfcgal import ffi, lib

# this must be called before anything else
lib.sfcgal_init()

def sfcgal_version():
    """Returns the version string of SFCGAL"""
    version = ffi.string(lib.sfcgal_version()).decode("utf-8")
    return version

def read_wkt(wkt):
    wkt = bytes(wkt, encoding="utf-8")
    return lib.sfcgal_io_read_wkt(wkt, len(wkt))

def write_wkt(geom):
    buf = ffi.new("char**")
    length = ffi.new("size_t*")
    lib.sfcgal_geometry_as_text(geom, buf, length)
    return ffi.string(buf[0], length[0]).decode("utf-8")

class Geometry:
    def distance(self, other):
        return lib.sfcgal_geometry_distance(self._geom, other._geom)

    def distance_3d(self, other):
        return lib.sfcgal_geometry_distance_3d(self._geom, other._geom)

    def area():
        def fget(self):
            return lib.sfcgal_geometry_area(self._geom)
        return locals()
    area = property(**area())

    def is_empty():
        def fget(self):
            return lib.sfcgal_geometry_is_empty(self._geom)
        return locals()
    is_empty = property(**is_empty())

    def intersects(self, other):
        return lib.sfcgal_geometry_intersects(self._geom, other._geom) == 1

    def intersection(self, other):
        geom = lib.sfcgal_geometry_intersection(self._geom, other._geom)
        return wrap_geom(geom)

    def wkt():
        def fget(self):
            return write_wkt(self._geom)
        return locals()
    wkt = property(**wkt())

class Point(Geometry):
    def __init__(self, x, y, z=None):
        # TODO: support coordinates as a list
        if z is None:
            self._geom = point_from_coordinates([x, y])
        else:
            self._geom = point_from_coordinates([x, y, z])

    def x():
        def fget(self):
            return lib.sfcgal_point_x(self._geom)
        return locals()
    x = property(**x())

    def y():
        def fget(self):
            return lib.sfcgal_point_y(self._geom)
        return locals()
    y = property(**y())

class LineString(Geometry):
    pass

class Polygon(Geometry):
    def __init__(self, exterior, interiors=None):
        if interiors is None:
            interiors = []
        self._geom = polygon_from_coordinates([
            exterior,
            *interiors,
        ])

class MultiPoint(Geometry):
    pass

class MultiLineString(Geometry):
    pass

class MultiPolygon(Geometry):
    pass

class GeometryCollection(Geometry):
    pass

def wrap_geom(geom):
    geom_type_id = lib.sfcgal_geometry_type_id(geom)
    cls = geom_type_to_cls[geom_type_id]
    geometry = object.__new__(cls)
    geometry._geom = geom
    return geometry

geom_type_to_cls = {
    lib.SFCGAL_TYPE_POINT: Point,
    lib.SFCGAL_TYPE_LINESTRING: LineString,
    lib.SFCGAL_TYPE_POLYGON: Polygon,
    lib.SFCGAL_TYPE_MULTIPOINT: MultiPoint,
    lib.SFCGAL_TYPE_MULTILINESTRING: MultiLineString,
    lib.SFCGAL_TYPE_MULTIPOLYGON: MultiPolygon,
    lib.SFCGAL_TYPE_GEOMETRYCOLLECTION: GeometryCollection,
}

def shape(geometry):
    """Creates a SFCGAL geometry from a GeoJSON-like geometry"""
    geom_type = geometry["type"].lower()
    try:
        factory = factories_type_from_coords[geom_type]
    except KeyError:
        raise ValueError("Unknown geometry type: {}".format(geometry["type"]))
    if geom_type == "geometrycollection":
        geometries = geometry["geometries"]
        return wrap_geom(factory(geometries))
    else:
        coordinates = geometry["coordinates"]
        return wrap_geom(factory(coordinates))

def point_from_coordinates(coordinates):
    if len(coordinates) == 2:
        point = lib.sfcgal_point_create_from_xy(*coordinates)
    else:
        point = lib.sfcgal_point_create_from_xyz(*coordinates)
    return point

def linestring_from_coordinates(coordinates):
    linestring = lib.sfcgal_linestring_create()
    for coordinate in coordinates:
        point = point_from_coordinates(coordinate)
        lib.sfcgal_linestring_add_point(linestring, point)
    return linestring

def polygon_from_coordinates(coordinates):
    exterior = linestring_from_coordinates(coordinates[0])
    polygon = lib.sfcgal_polygon_create_from_exterior_ring(exterior)
    for n in range(1, len(coordinates)):
        interior = linestring_from_coordinates(coordinates[n])
        lib.sfcgal_polygon_add_interior_ring(polygon, interior)
    return polygon

def multipoint_from_coordinates(coordinates):
    multipoint = lib.sfcgal_multi_point_create()
    for coords in coordinates:
        point = point_from_coordinates(coords)
        lib.sfcgal_geometry_collection_add_geometry(multipoint, point)
    return multipoint

def multilinestring_from_coordinates(coordinates):
    multilinestring = lib.sfcgal_multi_linestring_create()
    for coords in coordinates:
        linestring = linestring_from_coordinates(coords)
        lib.sfcgal_geometry_collection_add_geometry(multilinestring, linestring)
    return multilinestring

def multipolygon_from_coordinates(coordinates):
    multipolygon = lib.sfcgal_multi_polygon_create()
    for coords in coordinates:
        polygon = polygon_from_coordinates(coords)
        lib.sfcgal_geometry_collection_add_geometry(multipolygon, polygon)
    return multipolygon

def geometry_collection_from_coordinates(geometries):
    collection = lib.sfcgal_geometry_collection_create()
    for geometry in geometries:
        geom = shape(geometry)._geom
        lib.sfcgal_geometry_collection_add_geometry(collection, geom)
    return collection

factories_type_from_coords = {
    "point": point_from_coordinates,
    "linestring": linestring_from_coordinates,
    "polygon": polygon_from_coordinates,
    "multipoint": multipoint_from_coordinates,
    "multilinestring": multilinestring_from_coordinates,
    "multipolygon": multipolygon_from_coordinates,
    "geometrycollection": geometry_collection_from_coordinates,
}

geom_types = {
    "Point": lib.SFCGAL_TYPE_POINT,
    "LineString": lib.SFCGAL_TYPE_LINESTRING,
    "Polygon": lib.SFCGAL_TYPE_POLYGON,
    "MultiPoint": lib.SFCGAL_TYPE_MULTIPOINT,
    "MultiLineString": lib.SFCGAL_TYPE_MULTILINESTRING,
    "MultiPolygon": lib.SFCGAL_TYPE_MULTIPOLYGON,
    "GeometryCollection": lib.SFCGAL_TYPE_GEOMETRYCOLLECTION,
}
geom_types_r = dict((v,k) for k,v in geom_types.items())

def mapping(geometry):
    geom_type_id = lib.sfcgal_geometry_type_id(geometry._geom)
    try:
        geom_type = geom_types_r[geom_type_id]
    except KeyError:
        raise ValueError("Unknown geometry type: {}".format(geom_type_id))
    if geom_type == "GeometryCollection":
        ret = {
            "type": geom_type,
            "geometries": factories_type_to_coords[geom_type](geometry._geom)
        }
    else:
        ret = {
            "type": geom_type,
            "coordinates": factories_type_to_coords[geom_type](geometry._geom)
        }
    return ret

def point_to_coordinates(geometry):
    x = lib.sfcgal_point_x(geometry)
    y = lib.sfcgal_point_y(geometry)
    if lib.sfcgal_geometry_is_3d(geometry):
        z = lib.sfcgal_point_z(geometry)
        return [x, y, z]
    else:
        return [x,y]

def linestring_to_coordinates(geometry):
    num_points = lib.sfcgal_linestring_num_points(geometry)
    coords = []
    for n in range(0, num_points):
        point = lib.sfcgal_linestring_point_n(geometry, n)
        coords.append(point_to_coordinates(point))
    return coords

def polygon_to_coordinates(geometry):
    coords = []
    exterior = lib.sfcgal_polygon_exterior_ring(geometry)
    coords.append(linestring_to_coordinates(exterior))
    num_interior = lib.sfcgal_polygon_num_interior_rings(geometry)
    for n in range(0, num_interior):
        interior = lib.sfcgal_polygon_interior_ring_n(geometry, n)
        coords.append(linestring_to_coordinates(interior))
    return coords

def multipoint_to_coordinates(geometry):
    num_geoms = lib.sfcgal_geometry_collection_num_geometries(geometry)
    coords = []
    for n in range(0, num_geoms):
        point = lib.sfcgal_geometry_collection_geometry_n(geometry, n)
        coords.append(point_to_coordinates(point))
    return coords

def multilinestring_to_coordinates(geometry):
    num_geoms = lib.sfcgal_geometry_collection_num_geometries(geometry)
    coords = []
    for n in range(0, num_geoms):
        linestring = lib.sfcgal_geometry_collection_geometry_n(geometry, n)
        coords.append(linestring_to_coordinates(linestring))
    return coords

def multipolygon_to_coordinates(geometry):
    num_geoms = lib.sfcgal_geometry_collection_num_geometries(geometry)
    coords = []
    for n in range(0, num_geoms):
        polygon = lib.sfcgal_geometry_collection_geometry_n(geometry, n)
        coords.append(polygon_to_coordinates(polygon))
    return coords

def geometrycollection_to_coordinates(geometry):
    num_geoms = lib.sfcgal_geometry_collection_num_geometries(geometry)
    geoms = []
    for n in range(0, num_geoms):
        geom = lib.sfcgal_geometry_collection_geometry_n(geometry, n)
        geoms.append(mapping(wrap_geom(geom))) # TODO: inefficient
    return geoms

factories_type_to_coords = {
    "Point": point_to_coordinates,
    "LineString": linestring_to_coordinates,
    "Polygon": polygon_to_coordinates,
    "MultiPoint": multipoint_to_coordinates,
    "MultiLineString": multilinestring_to_coordinates,
    "MultiPolygon": multipolygon_to_coordinates,
    "GeometryCollection": geometrycollection_to_coordinates,
}
