import json
import re

import cellprofiler_core
from cellprofiler_core.constants.pipeline import IMAGE_PLANE_DESCRIPTOR_VERSION, H_PLANE_COUNT


def dump(pipeline, fp, save_image_plane_details):
    """Serializes pipeline into JSON"""
    modules = []

    for module in pipeline.modules(False):
        settings = []
        for setting in module.settings():
            settings.append(setting.to_dict())

        modules += [
            {
                "attributes": module.to_dict(),
                "settings": settings
            }
        ]

    content = {
        "has_image_plane_details": save_image_plane_details,
        "date_revision": int(re.sub(r"\.|rc\d", "", cellprofiler_core.__version__)),
        "module_count": len(pipeline.modules(False)),
        "modules": modules,
        "version": "v6"}

    if len(pipeline.file_list) == 0:
        save_image_plane_details = False

    if save_image_plane_details:
        urls = [url for url in pipeline.file_list]
        file_list = {
            "version": '"%s":"%d","%s":"%d"' % (
                "Version", IMAGE_PLANE_DESCRIPTOR_VERSION, H_PLANE_COUNT, len(pipeline.file_list)),
            "urls": urls
        }
        content["file_list"] = file_list

    json.dump(content, fp, indent=4)