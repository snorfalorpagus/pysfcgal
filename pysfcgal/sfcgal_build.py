import os
from cffi import FFI

ffibuilder = FFI()

ffibuilder.set_source("pysfcgal._sfcgal", r"""
#include <stdlib.h>
#include <SFCGAL/capi/sfcgal_c.h>
""", libraries=["SFCGAL"])

with open(os.path.join(os.path.dirname(__file__), "sfcgal_def.c"), "r") as f:
    sfcgal_def = f.read()
ffibuilder.cdef(sfcgal_def)

if __name__ == "__main__":
    help(ffibuilder.compile)
    ffibuilder.compile(verbose=True)

