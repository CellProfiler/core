import logging
import os
import tempfile

import h5py
import numpy
import pytest

import cellprofiler_core.measurement
import cellprofiler_core.pipeline
import cellprofiler_core.utilities.core.workspace
import cellprofiler_core.utilities.hdf5_dict
import cellprofiler_core.workspace
import cellprofiler_core.motion
import cellprofiler_core.setting.text


@pytest.fixture
def motion() -> cellprofiler_core.motion.Motion:
    u = numpy.array([])
    v = numpy.array([])

    return cellprofiler_core.motion.Motion(u, v)


@pytest.fixture
def workspace() -> cellprofiler_core.workspace.Workspace:
    pipeline = cellprofiler_core.pipeline.Pipeline()

    measurements = cellprofiler_core.measurement.Measurements()

    return cellprofiler_core.workspace.Workspace(
        pipeline, None, measurements, None, measurements, None
    )


class TestWorkspace:
    def setup_method(self):
        self.workspace_files = []

    def teardown_method(self):
        for path in self.workspace_files:
            try:
                os.remove(path)
            except OSError:
                logging.warning("Failed to close file %s" % path, exc_info=1)

    def make_workspace_file(self):
        """Make a very basic workspace file"""
        pipeline = cellprofiler_core.pipeline.Pipeline()
        pipeline.init_modules()
        m = cellprofiler_core.measurement.Measurements()
        workspace = cellprofiler_core.workspace.Workspace(
            pipeline, None, m, None, m, None
        )
        fd, path = tempfile.mkstemp(".cpproj")
        file_list = workspace.get_file_list()
        file_list.add_files_to_filelist(
            [os.path.join(os.path.dirname(__file__), "resources/01_POS002_D.TIF")]
        )
        workspace.save(path)
        self.workspace_files.append(path)
        os.close(fd)
        return path

    def test_is_workspace_file(self):
        path = self.make_workspace_file()
        assert cellprofiler_core.utilities.core.workspace.is_workspace_file(path)

    def test_is_not_workspace_file(self):
        assert not cellprofiler_core.utilities.core.workspace.is_workspace_file(
            __file__
        )
        for group in (
            cellprofiler_core.utilities.hdf5_dict.TOP_LEVEL_GROUP_NAME,
            cellprofiler_core.utilities.hdf5_dict.FILE_LIST_GROUP,
        ):
            path = self.make_workspace_file()
            h5file = h5py.File(path, "r+")
            del h5file[group]
            h5file.close()
            assert not cellprofiler_core.utilities.core.workspace.is_workspace_file(
                path
            )

    def test_file_handle_closed(self):
        # regression test of issue #1326
        path = self.make_workspace_file()
        assert cellprofiler_core.utilities.core.workspace.is_workspace_file(path)
        os.remove(path)
        self.workspace_files.remove(path)
        assert not os.path.isfile(path)

    def test_motions(self, workspace, motion):
        workspace.motions["foo"] = motion

        assert workspace.motions == {"foo": motion}
