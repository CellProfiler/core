import os
import pathlib
import urllib

from cellprofiler_core.constants.image import FILE_SCHEME, PASSTHROUGH_SCHEMES
from cellprofiler_core.utilities.image import is_file_url
from cellprofiler_core.readers import gcs_reader

def pathname2url(path):
    """Convert the unicode path to a file: url"""
    lower_path = path.lower()
    if any((lower_path.startswith(x) for x in PASSTHROUGH_SCHEMES)):
        return path
    path_object = pathlib.Path(path)
    if path_object.is_absolute():
        # Produces a valid URI regardless of platform.
        return path_object.as_uri()
    # Produces CellProfiler's interpretation of a relative path URI.
    return FILE_SCHEME + urllib.request.pathname2url(path)


def url2pathname(url):
    lower_url = url.lower()
    if any((lower_url.startswith(x) for x in PASSTHROUGH_SCHEMES)):
        if lower_url.startswith("gs"):
            parsed_url = urllib.parse.urlparse(lower_url)
            cwd = os.getcwd()
            local_filepath = "{}/{}".format(cwd, parsed_url.path)
            # If image already downloaded, return local file path.
            if os.path.exists(local_filepath):
                return local_filepath
            else:
                reader = gcs_reader.GcsReader(url)
                return reader.download_blob(url)
        else:
            return url
    if is_file_url(url):
        return urllib.request.url2pathname(url[len(FILE_SCHEME):])
