builtin_readers = {
    "imageio_reader": "ImageIOReader",
    "bioformats_reader": "BioformatsReader",
    "gcs_reader": "GcsReader",
}
# All successfully loaded reader classes. Maps name:class
ALL_READERS = dict()
# Reader classes that failed to load. Maps name:exception str
BAD_READERS = dict()
# Active reader classes (ALL_READERS that aren't disabled by user). Maps name:class
AVAILABLE_READERS = dict()

