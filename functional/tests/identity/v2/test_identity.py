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

from tempest_lib.common.utils import data_utils

from functional.common import test

BASIC_LIST_HEADERS = ['ID', 'Name']


class IdentityTests(test.TestCase):
    """Functional tests for Identity commands. """

    USER_FIELDS = ['email', 'enabled', 'id', 'name', 'project_id',
                   'username', 'domain_id', 'default_project_id']
    PROJECT_FIELDS = ['enabled', 'id', 'name', 'description', 'domain_id']
    TOKEN_FIELDS = ['expires', 'id', 'project_id', 'user_id']
    ROLE_FIELDS = ['id', 'name', 'links']

    EC2_CREDENTIALS_FIELDS = ['access', 'project_id', 'secret',
                              'trust_id', 'user_id']
    EC2_CREDENTIALS_LIST_HEADERS = ['Access', 'Secret',
                                    'Project ID', 'User ID']
    CATALOG_LIST_HEADERS = ['Name', 'Type', 'Endpoints']

    @classmethod
    def setUpClass(cls):
        if hasattr(super(IdentityTests, cls), 'setUpClass'):
            super(IdentityTests, cls).setUpClass()

        # create dummy project
        cls.project_name = data_utils.rand_name('TestProject')
        cls.project_description = data_utils.rand_name('description')
        cls.openstack(
            'project create '
            '--description %(description)s '
            '--enable '
            '%(name)s' % {'description': cls.project_description,
                          'name': cls.project_name})

    @classmethod
    def tearDownClass(cls):
        cls.openstack('project delete %s' % cls.project_name)

        if hasattr(super(IdentityTests, cls), 'tearDownClass'):
            super(IdentityTests, cls).tearDownClass()

    def _create_dummy_project(self, add_clean_up=True):
        project_name = data_utils.rand_name('TestProject')
        project_description = data_utils.rand_name('description')
        raw_output = self.openstack(
            'project create '
            '--description %(description)s '
            '--enable %(name)s' % {'description': project_description,
                                   'name': project_name})
        items = self.parse_show(raw_output)
        self.assert_show_fields(items, self.PROJECT_FIELDS)
        project = self.parse_show_as_object(raw_output)
        if add_clean_up:
            self.addCleanup(
                self.openstack,
                'project delete %s' % project['id'])
        return project_name

    def _create_dummy_user(self, add_clean_up=True):
        username = data_utils.rand_name('TestUser')
        password = data_utils.rand_name('password')
        email = data_utils.rand_name() + '@example.com'
        raw_output = self.openstack(
            'user create '
            '--project %(project)s '
            '--password %(password)s '
            '--email %(email)s '
            '--enable '
            '%(name)s' % {'project': self.project_name,
                          'email': email,
                          'password': password,
                          'name': username})
        items = self.parse_show(raw_output)
        self.assert_show_fields(items, self.USER_FIELDS)
        if add_clean_up:
            self.addCleanup(
                self.openstack,
                'user delete %s' % self.parse_show_as_object(raw_output)['id'])
        return username

    def _create_dummy_role(self, add_clean_up=True):
        role_name = data_utils.rand_name('TestRole')
        raw_output = self.openstack('role create %s' % role_name)
        items = self.parse_show(raw_output)
        self.assert_show_fields(items, self.ROLE_FIELDS)
        role = self.parse_show_as_object(raw_output)
        self.assertEqual(role_name, role['name'])
        if add_clean_up:
            self.addCleanup(
                self.openstack,
                'role delete %s' % role['id'])
        return role_name

    def _create_dummy_ec2_credentials(self, add_clean_up=True):
        raw_output = self.openstack('ec2 credentials create')
        items = self.parse_show(raw_output)
        self.assert_show_fields(items, self.EC2_CREDENTIALS_FIELDS)
        ec2_credentials = self.parse_show_as_object(raw_output)
        access_key = ec2_credentials['access']
        if add_clean_up:
            self.addCleanup(
                self.openstack,
                'ec2 credentials delete %s' % access_key)
        return access_key

    def _create_dummy_token(self, add_clean_up=True):
        raw_output = self.openstack('token issue')
        items = self.parse_show(raw_output)
        self.assert_show_fields(items, self.TOKEN_FIELDS)
        token = self.parse_show_as_object(raw_output)
        if add_clean_up:
            self.addCleanup(self.openstack,
                            'token revoke %s' % token['id'])
        return token['id']
