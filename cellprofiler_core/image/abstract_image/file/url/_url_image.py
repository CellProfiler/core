import os
from .....utilities.pathname import url2pathname

from .....utilities.image import is_omero3d_path

from .._file_image import FileImage


class URLImage(FileImage):
    """Reference an image via a URL"""

    def __init__(
        self,
        name,
        url,
        rescale=True,
        series=None,
        index=None,
        channel=None,
        volume=False,
        spacing=None,
    ):
        if url.lower().startswith("file:"):
            path = url2pathname(url)
            pathname, filename = os.path.split(path)
        else:
            pathname = ""
            filename = url
        super(URLImage, self).__init__(
            name, pathname, filename, rescale, series, index, channel, volume, spacing
        )
        self.url = url

    def get_url(self):
        print("Retrieving urlImage URL")
        if is_omero3d_path(self.url):
            print("OMERO-3D URL: {}".format(self.url))
            url = self.url.split("omero-3d:")[1]
            if url is not None:
                return url
            return self.url
        if self.cache_file():
            return super(URLImage, self).get_url()
        return self.url
