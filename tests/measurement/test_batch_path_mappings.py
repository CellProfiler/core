import json
import nturl2path
import urllib.parse

import pytest
from cellprofiler_core.constants.measurement import (
    K_CASE_SENSITIVE,
    K_LOCAL_SEPARATOR,
    K_PATH_MAPPINGS,
    K_URL2PATHNAME_PACKAGE_NAME,
    M_PATH_MAPPINGS,
)
from cellprofiler_core.measurement import Measurements, _measurements


@pytest.fixture
def measurements():
    result = Measurements()
    yield result
    result.close()


@pytest.fixture(params=["posix", "windows"])
def target(request, monkeypatch):
    if request.param == "windows":
        encode = nturl2path.pathname2url
        decode = nturl2path.url2pathname
        root = r"Z:\cluster\images"
        expected = r"Z:\cluster\images\subfolder\image é#%.tif"
    else:
        encode = urllib.parse.quote
        decode = urllib.parse.unquote
        root = "/home/ubuntu/bucket/projects/project/batch/images"
        expected = root + "/subfolder/image é#%.tif"
    monkeypatch.setattr(_measurements.urllib.request, "pathname2url", encode)
    return root, expected, decode


@pytest.mark.parametrize(
    "url,local_root,case_sensitive,separator,package",
    [
        (
            "file:///D:/Batch_1_CellGrowth/images/subfolder/image%20%C3%A9%23%25.tif",
            r"D:\Batch_1_CellGrowth\images",
            False,
            "\\",
            "nturl2path",
        ),
        (
            "file:/D:/BATCH_1_CELLGROWTH/images/subfolder/image%20%C3%A9%23%25.tif",
            "d:/Batch_1_CellGrowth/images",
            False,
            "\\",
            "nturl2path",
        ),
        (
            "file://server/share/images/subfolder/image%20%C3%A9%23%25.tif",
            r"\\server\share\images",
            False,
            "\\",
            "nturl2path",
        ),
        (
            "file:///C:/Program%20Files/CellProfiler/images/subfolder/image%20%C3%A9%23%25.tif",
            r"C:\Program Files\CellProfiler\images",
            False,
            "\\",
            "nturl2path",
        ),
        (
            "file:///Users/local/images/subfolder/image%20%C3%A9%23%25.tif",
            "/Users/local/images",
            True,
            "/",
            "urllib.request",
        ),
        (
            "file:/Users/local/images/subfolder/image%20%C3%A9%23%25.tif",
            "/Users/local/images",
            True,
            "/",
            "urllib.request",
        ),
    ],
    ids=[
        "windows-drive",
        "windows-forward-slashes",
        "windows-unc",
        "windows-space-in-root",
        "posix-uri",
        "posix-short-uri",
    ],
)
@pytest.mark.parametrize("trailing_separator", [False, True])
def test_alter_url_post_create_batch(
    measurements,
    target,
    url,
    local_root,
    case_sensitive,
    separator,
    package,
    trailing_separator,
):
    remote_root, expected, decode = target
    if trailing_separator:
        local_root += separator
        remote_root += "/"
    measurements.add_experiment_measurement(
        M_PATH_MAPPINGS,
        json.dumps(
            {
                K_CASE_SENSITIVE: case_sensitive,
                K_LOCAL_SEPARATOR: separator,
                K_URL2PATHNAME_PACKAGE_NAME: package,
                K_PATH_MAPPINGS: [("unrelated", "unused"), (local_root, remote_root)],
            }
        ),
    )
    result = measurements.alter_url_post_create_batch(url)
    assert result.startswith("file:")
    assert decode(result[5:]) == expected


@pytest.mark.parametrize(
    "url",
    ["https://example.org/image.tif", "s3://bucket/image.tif", "file:///D:/image.tif"],
)
def test_alter_url_without_mappings(measurements, url):
    assert measurements.alter_url_post_create_batch(url) == url


def test_unmatched_url_is_unchanged(measurements):
    measurements.write_path_mappings([(r"C:\images", "/cluster/images")])
    url = "file:///D:/images/image.tif"
    assert measurements.alter_url_post_create_batch(url) == url


@pytest.mark.parametrize(
    "url", ["https://example.org/image.tif", "s3://bucket/image.tif"]
)
def test_non_file_url_with_mappings(measurements, url):
    measurements.write_path_mappings([("", "/cluster/images")])
    assert measurements.alter_url_post_create_batch(url) == url


def test_posix_mapping_is_case_sensitive(measurements):
    measurements.add_experiment_measurement(
        M_PATH_MAPPINGS,
        json.dumps(
            {
                K_CASE_SENSITIVE: True,
                K_LOCAL_SEPARATOR: "/",
                K_URL2PATHNAME_PACKAGE_NAME: "urllib.request",
                K_PATH_MAPPINGS: [("/Users/local/images", "/cluster/images")],
            }
        ),
    )
    url = "file:///Users/LOCAL/images/image.tif"
    assert measurements.alter_url_post_create_batch(url) == url
