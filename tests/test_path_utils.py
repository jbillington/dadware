"""Tests for utils/path_utils.py"""

import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.path_utils import is_docker_path, is_sparse_file, should_exclude, should_skip_path


class TestIsDockerPath:
    def test_docker_directory(self):
        assert is_docker_path('/Users/me/Library/Containers/com.docker.docker') is True

    def test_docker_containers(self):
        assert is_docker_path('/var/lib/docker/containers/abc123') is True

    def test_docker_volumes(self):
        assert is_docker_path('/var/lib/docker/volumes/myapp') is True

    def test_docker_qcow2(self):
        assert is_docker_path('/Users/me/.docker/Docker.qcow2') is True

    def test_docker_raw(self):
        assert is_docker_path('/Users/me/Library/Containers/com.docker.docker/Data/vms/0/Docker.raw') is True

    def test_normal_path(self):
        assert is_docker_path('/Users/me/Documents/project') is False

    def test_docker_in_name_only(self):
        assert is_docker_path('/Users/me/Documents/my-docker-notes.txt') is False


class TestShouldExclude:
    def test_system_directories(self):
        assert should_exclude('/System/Library/Fonts') is True
        assert should_exclude('/Library/Application Support') is True
        assert should_exclude('/usr/local/bin') is True
        assert should_exclude('/bin/sh') is True
        assert should_exclude('/sbin/mount') is True
        assert should_exclude('/private/var/log') is True

    def test_applications(self):
        assert should_exclude('/Applications') is True

    def test_dot_app(self):
        assert should_exclude('/Users/me/Something.app') is True
        assert should_exclude('/Users/me/.app/subfolder') is True

    def test_photoslibrary(self):
        assert should_exclude('/Users/me/Pictures/Photos Library.photoslibrary') is True

    def test_caches(self):
        assert should_exclude('/Users/me/Library/Caches/com.apple.Safari') is True

    def test_tmp(self):
        assert should_exclude('/tmp/somefile') is True
        assert should_exclude('/Users/me/tmp') is True

    def test_hidden_files(self):
        assert should_exclude('/Users/me/.hidden_folder') is True

    def test_library_mail(self):
        assert should_exclude('/Users/me/Library/Mail/V9') is True

    def test_library_messages(self):
        assert should_exclude('/Users/me/Library/Messages') is True

    def test_normal_user_folder(self):
        assert should_exclude('/Users/me/Documents') is False
        assert should_exclude('/Users/me/Downloads') is False
        assert should_exclude('/Users/me/Movies') is False


class TestShouldSkipPath:
    def test_mobile_documents(self):
        assert should_skip_path('/Users/me/Library/Mobile Documents/com~apple~CloudDocs') is True

    def test_cloud_storage(self):
        assert should_skip_path('/Users/me/Library/CloudStorage/Dropbox') is True

    def test_containers(self):
        assert should_skip_path('/Users/me/Library/Containers/com.apple.mail') is True

    def test_group_containers(self):
        assert should_skip_path('/Users/me/Library/Group Containers/group.com.apple') is True

    def test_normal_path(self):
        assert should_skip_path('/Users/me/Documents/project') is False
