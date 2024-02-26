import collections
import os
import re
import sys
import tempfile
import urllib.parse
from urllib.request import urlopen

import numpy
import zarr
import boto3
import shutil

from cellprofiler_core.utilities.pathname import url2pathname

import logging
logger = logging.getLogger(__name__)


def get_zarr_metadata(url):
    xmlfile = 'METADATA.ome.xml'
    parser = urllib.parse.urlparse(url)
    if parser.scheme == 'file':
        url = url2pathname(url)
    elif parser.scheme == 's3':
        client = boto3.client('s3')
        bucket_name, key = re.compile('s3://([\w\d\-\.]+)/(.*)').search(
            url).groups()
        key += "/OME/METADATA.ome.xml"
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key.replace("+", " ")}
        )
        src = urlopen(url)
        return src.read().decode()
    metadata_path = os.path.join(url, "OME", xmlfile)
    if os.path.exists(metadata_path):
        with open(metadata_path) as data:
            return data.read()
    elif os.path.exists(os.path.join(url, xmlfile)):
        with open(os.path.join(url, xmlfile)) as data:
            return data.read()
    else:
        logger.warning("Input zarr lacks an OME-XML file. "
                       "CellProfiler will try to construct metadata, but this feature is experimental")
        return make_ome_xml(url)


def make_ome_xml(url):
    # Prototype zarr parser to construct a fake OME XML.
    root = zarr.open(url, mode='r')
    queue = collections.deque()
    queue.append(root)
    xmlstr = """<?xml version="1.0" encoding="UTF-8"?><OME xmlns="http://www.openmicroscopy.org/Schemas/OME/2016-06" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.openmicroscopy.org/Schemas/OME/2016-06 http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd"><Instrument ID="Instrument:0"><Objective ID="Objective:0:0" NominalMagnification="20.0"/></Instrument>"""
    while queue:
        subject = queue.popleft()
        for loc, group in subject.groups():
            queue.append(group)
        for loc, array in subject.arrays():
            t, c, z, y, x = array.shape
            dtype = array.dtype.name
            if dtype == "int64":
                # OME-XML can't handle int64, consider as a float instead.
                dtype = "float"
            xmlstr += \
                f"""<Image ID="Image:{subject.basename}" Name="{array.name}"><AcquisitionDate>Unknown</AcquisitionDate><Description>CellProfiler OME Metadata </Description><InstrumentRef ID="Instrument:0"/><ObjectiveSettings ID="Objective:0:0"/><Pixels BigEndian="false" DimensionOrder="XYZCT" ID="Pixels:{array.basename}" Interleaved="false" SignificantBits="8" SizeC="{c}" SizeT="{t}" SizeX="{x}" SizeY="{y}" SizeZ="{z}" Type="{dtype}">"""
            for i in range(c):
                xmlstr += f"""<Channel ID="Channel:{i}:0" SamplesPerPixel="1"><LightPath/></Channel>"""
            xmlstr += """</Pixels></Image> """
            # We only want the first resolution
            break
    return xmlstr + "</OME>"


def get_zarr_reader(key, path=None, url=None):
    logger.debug("Getting image reader for: %s, %s, %s" % (key, path, url))
    from bioformats.formatreader import __image_reader_key_cache, __image_reader_cache, release_image_reader
    if key in __image_reader_key_cache:
        old_path, old_url = __image_reader_key_cache[key]
        old_count, rdr = __image_reader_cache[old_path, old_url]
        if old_path == path and old_url == url:
            return rdr
        release_image_reader(key)
    if (path, url) in __image_reader_cache:
        old_count, rdr = __image_reader_cache[path, url]
    else:
        rdr = ZarrReader(path, url)
        old_count = 0
    __image_reader_cache[path, url] = (old_count + 1, rdr)
    __image_reader_key_cache[key] = (path, url)

    return rdr


class ZarrReader(object):
    def __init__(self, path=None, url=None, perform_init=True):

        self.stream = None
        file_scheme = "file:"

        self.using_temp_file = False

        if url is not None:
            url = str(url)
            if url.lower().startswith(file_scheme):
                url = url2pathname(url)
                path = url
            elif path is None:
                path = url

        self.path = path
        if path is None:
            if not url.lower().startswith('s3:'):
                self.path = self.download(url)
        else:
            if sys.platform.startswith("win"):
                self.path = self.path.replace("/", os.path.sep)
            filename = os.path.split(path)[1]
        store = zarr.storage.FSStore(self.path)
        if path.startswith('s3'):
            logger.info("Zarr is stored on S3, will try to read directly.")
            if '.zmetadata' in store:
                # Zarr has consolidated metadata.
                self.reader = zarr.convenience.open_consolidated(store, mode='r')
            else:
                logging.warning(f"Image is on S3 but lacks consolidated metadata. "
                                f"This may degrade reading performance. URL: {path}")
                self.reader = zarr.open(store, mode='r')
        elif not os.path.isdir(self.path):
            raise IOError("The file, \"%s\", does not exist." % path)
        else:
            self.reader = zarr.open(store, mode='r')
        self.well_map = self.map_wells()
        self.series_list = self.map_series()

    def read(self, c=None, z=None, t=None, series=None, index=None, rescale=True, wants_max_intensity=True, channel_names=None, XYWH=None):
        """Read a single plane from the image reader file.
        :param c: read from this channel. `None` = read color image if multichannel
            or interleaved RGB.
        :param z: z-stack index
        :param t: time index
        :param series: series for ``.flex`` and similar multi-stack formats
        :param index: if `None`, fall back to ``zct``, otherwise load the indexed frame
        :param rescale: `True` to rescale the intensity scale to 0 and 1; `False` to
                  return the raw values native to the file.
        :param wants_max_intensity: if `False`, only return the image; if `True`,
                  return a tuple of image and max intensity
        :param channel_names: provide the channel names for the OME metadata
        :param XYWH: a (x, y, w, h) tuple"""
        # Index should always be None, we need ctz to properly index zarrs.
        logger.debug(f"Reading {c=}, {z=}, {t=}, {series=}, {index=}, {XYWH=}")
        c2 = None if c is None else c + 1
        z2 = None if z is None else z + 1
        t2 = None if t is None else t + 1
        if XYWH is not None:
            x, y, w, h = XYWH
            x = round(x)
            y = round(y)
            x2 = x + w
            y2 = y + h
        else:
            y, y2, x, x2 = None, None, None, None
        if self.well_map:
            series_col, series_row, series_field = self.series_list[series]
            base_path = self.well_map[(series_col, series_row)]
            seriesreader = self.reader[base_path]
            field = seriesreader.attrs['well']['images'][series_field]['path']
            # Hard-coding resolution 0 for now
            seriesreader = seriesreader[field][0]
        else:
            seriesreader = self.reader[self.series_list[series]][0]
        # Zarr arrays are indexed as TCZYX
        if len(seriesreader.shape) == 5:
            image = seriesreader[t:t2, c:c2, z:z2, y:y2, x:x2]
        else:
            image = seriesreader[c:c2, z:z2, y:y2, x:x2]
        # Remove redundant axes
        image = numpy.squeeze(image)
        # C needs to be the last axis, but z should be first. Thank you CellProfiler.
        if len(image.shape) > 2 and z is not None:
            image = numpy.moveaxis(image, 0, -1)
        elif len(image.shape) > 3:
            image = numpy.moveaxis(image, 0, -1)
        scale = numpy.iinfo(image.dtype).max
        if rescale:
            image = image.astype(float) / scale
        if wants_max_intensity:
            if image.dtype in [numpy.int8, numpy.uint8]:
                scale = 255
            elif image.dtype in [numpy.int16, numpy.uint16]:
                scale = 65535
            elif image.dtype == numpy.int32:
                scale = 2 ** 32 - 1
            elif image.dtype == numpy.uint32:
                scale = 2 ** 32
            else:
                scale = 1
            return image, scale
        return image

    def map_wells(self):
        # For HCS zarrs, we construct a dictionary mapping well positions to array directories.
        attrs = self.reader.attrs
        if 'plate' not in attrs or 'wells' not in attrs['plate']:
            return False
        well_data = attrs['plate']['wells']
        mapper = {}
        if 'column_index' in well_data[0]:
            # Standard format
            for row in well_data:
                mapper[(str(row['column_index']), str(row['row_index']))] = row['path']
        else:
            for row in well_data:
                path = row['path']
                col, row = path.split('/', 1)
                mapper[(str(col), str(row))] = path
        return mapper

    def map_series(self):
        # If in HCS mode we produce a list of (Row, Column, FieldNum) tuples to use with the well map.
        # If in non-HCS mode we just make a list of paths to each series.
        series_list = []
        if self.well_map:
            metadata = get_zarr_metadata(self.path)
            from lxml import etree
            import io
            context = etree.iterparse(io.BytesIO(metadata.encode()), tag="{*}ImageRef")
            for action, node in context:
                wellsample = node.getparent()
                well = wellsample.getparent()
                series_list.append((well.get('Column'), well.get('Row'), well.getchildren().index(wellsample)))
                node.clear()
            if not series_list:
                # No series were found, try constructing from the image tags.
                context = etree.iterparse(io.BytesIO(metadata.encode()), tag="{*}Image")
                for action, node in context:
                    imagepath = node.attrib["Name"]
                    parts = imagepath.split('/')
                    series_list.append((parts[1], parts[2], int(parts[3])))
                    node.clear()
        else:
            # No well metadata, just fetch series in order.
            queue = collections.deque()
            queue.append(self.reader)
            while queue:
                subject = queue.popleft()
                for loc, group in subject.groups():
                    queue.append(group)
                for loc, array in subject.arrays():
                    series_list.append(array.name)
                    # We only want the first resolution
                    break
        return series_list

    def download(self, url):
        # Cloned from bioformats' reader. Should temporarily download URLs.
        # No idea if this will work since zarr is a directory-based format.
        scheme = urllib.parse.urlparse(url)[0]
        ext = url[url.rfind("."):]
        urlpath = urllib.parse.urlparse(url)[2]
        filename = os.path.basename(self.path)

        self.using_temp_file = True

        src = urlopen(url)
        dest_fd, self.path = tempfile.mkstemp(suffix=ext)
        try:
            with os.fdopen(dest_fd, 'wb') as dest:
                shutil.copyfileobj(src, dest)
        except:
            os.remove(self.path)
        finally:
            src.close()

        return filename

    def close(self):
        # Zarr readers don't need to be explicitly closed.
        pass
