import re

builtin_readers = {
    "imageio_reader": "ImageIOReader",
    "ngff_reader": "NGFFReader",
    "bioformats_reader": "BioformatsReader",
}
all_readers = dict()
bad_readers = []

ZARR_FILETYPE = re.compile(r"(?<=\.zarr)", flags=re.IGNORECASE)

