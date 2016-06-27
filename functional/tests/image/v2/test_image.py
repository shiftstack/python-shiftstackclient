#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import uuid

import testtools

from functional.common import test


class ImageTests(test.TestCase):
    """Functional tests for image. """

    NAME = uuid.uuid4().hex
    OTHER_NAME = uuid.uuid4().hex
    HEADERS = ['Name']
    FIELDS = ['name']

    @classmethod
    def setUpClass(cls):
        os.environ['OS_IMAGE_API_VERSION'] = '2'
        opts = cls.get_show_opts(cls.FIELDS)
        raw_output = cls.openstack('image create ' + cls.NAME + opts)
        expected = cls.NAME + '\n'
        cls.assertOutput(expected, raw_output)

    @classmethod
    def tearDownClass(cls):
        # Rename test
        raw_output = cls.openstack('image set --name ' + cls.OTHER_NAME + ' '
                                   + cls.NAME)
        cls.assertOutput('', raw_output)
        # Delete test
        raw_output = cls.openstack('image delete ' + cls.OTHER_NAME)
        cls.assertOutput('', raw_output)

    def test_image_list(self):
        opts = self.get_list_opts(self.HEADERS)
        raw_output = self.openstack('image list' + opts)
        self.assertIn(self.NAME, raw_output)

    def test_image_show(self):
        opts = self.get_show_opts(self.FIELDS)
        raw_output = self.openstack('image show ' + self.NAME + opts)
        self.assertEqual(self.NAME + "\n", raw_output)

    def test_image_set(self):
        opts = self.get_show_opts([
            "disk_format", "visibility", "min_disk", "min_ram", "name"])
        self.openstack('image set --min-disk 4 --min-ram 5 ' +
                       '--public ' + self.NAME)
        raw_output = self.openstack('image show ' + self.NAME + opts)
        self.assertEqual("raw\n4\n5\n" + self.NAME + '\npublic\n', raw_output)

    def test_image_metadata(self):
        opts = self.get_show_opts(["name", "properties"])
        self.openstack('image set --property a=b --property c=d ' + self.NAME)
        raw_output = self.openstack('image show ' + self.NAME + opts)
        self.assertEqual(self.NAME + "\na='b', c='d'\n", raw_output)

    @testtools.skip("skip until bug 1596573 is resolved")
    def test_image_unset(self):
        opts = self.get_show_opts(["name", "tags", "properties"])
        self.openstack('image set --tag 01 ' + self.NAME)
        self.openstack('image unset --tag 01 ' + self.NAME)
        # test_image_metadata has set image properties "a" and "c"
        self.openstack('image unset --property a --property c ' + self.NAME)
        raw_output = self.openstack('image show ' + self.NAME + opts)
        self.assertEqual(self.NAME + "\n\n", raw_output)
