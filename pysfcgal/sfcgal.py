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

def shape(geometry):
    """Creates a SFCGAL geometry from a GeoJSON-like geometry"""
    geom_type = geometry["type"].lower()
    try:
        factory = factories_type_from_coords[geom_type]
    except KeyError:
        raise ValueError("Unknown geometry type: {}".format(geometry["type"]))
    if geom_type == "geometrycollection":
        geometries = geometry["geometries"]
        return factory(geometries)
    else:
        coordinates = geometry["coordinates"]
        return factory(coordinates)

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
        geom = shape(geometry)
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
    geom_type_id = lib.sfcgal_geometry_type_id(geometry)
    try:
        geom_type = geom_types_r[geom_type_id]
    except KeyError:
        raise ValueError("Unknown geometry type: {}".format(geom_type_id))
    if geom_type == "GeometryCollection":
        ret = {
            "type": geom_type,
            "geometries": factories_type_to_coords[geom_type](geometry)
        }
    else:
        ret = {
            "type": geom_type,
            "coordinates": factories_type_to_coords[geom_type](geometry)
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
        geoms.append(mapping(geom))
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
