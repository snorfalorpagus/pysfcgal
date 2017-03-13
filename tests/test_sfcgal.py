import pytest

import pysfcgal.sfcgal as sfcgal
import geom_data

def test_version():
    print(sfcgal.sfcgal_version())

geometry_names, geometry_values = zip(*geom_data.data.items())
@pytest.mark.parametrize("geometry", geometry_values, ids=geometry_names)
def test_integrity(geometry):
    sfcgal_geom = sfcgal.shape(geometry)
    data = sfcgal.mapping(sfcgal_geom)
    # TODO: use a comparison that doesn't care about tuples vs lists
    assert(geometry == data)
