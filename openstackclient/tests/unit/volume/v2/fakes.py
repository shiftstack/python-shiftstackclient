#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

import copy
import random
from unittest import mock
import uuid

from cinderclient import api_versions
from openstack.block_storage.v3 import backup as _backup
from openstack.block_storage.v3 import volume
from openstack.image.v2 import _proxy as image_v2_proxy
from osc_lib.cli import format_columns

from openstackclient.tests.unit import fakes
from openstackclient.tests.unit.identity.v3 import fakes as identity_fakes
from openstackclient.tests.unit import utils


QUOTA = {
    "gigabytes": 1000,
    "volumes": 11,
    "snapshots": 10,
    "backups": 10,
    "backup_gigabytes": 1000,
    "per_volume_gigabytes": -1,
    "gigabytes_volume_type_backend": -1,
    "volumes_volume_type_backend": -1,
    "snapshots_volume_type_backend": -1,
}


class FakeVolumeClient:
    def __init__(self, **kwargs):
        self.auth_token = kwargs['token']
        self.management_url = kwargs['endpoint']
        self.api_version = api_versions.APIVersion('2.0')

        self.availability_zones = mock.Mock()
        self.availability_zones.resource_class = fakes.FakeResource(None, {})
        self.backups = mock.Mock()
        self.backups.resource_class = fakes.FakeResource(None, {})
        self.capabilities = mock.Mock()
        self.capabilities.resource_class = fakes.FakeResource(None, {})
        self.cgsnapshots = mock.Mock()
        self.cgsnapshots.resource_class = fakes.FakeResource(None, {})
        self.consistencygroups = mock.Mock()
        self.consistencygroups.resource_class = fakes.FakeResource(None, {})
        self.limits = mock.Mock()
        self.limits.resource_class = fakes.FakeResource(None, {})
        self.pools = mock.Mock()
        self.pools.resource_class = fakes.FakeResource(None, {})
        self.qos_specs = mock.Mock()
        self.qos_specs.resource_class = fakes.FakeResource(None, {})
        self.quota_classes = mock.Mock()
        self.quota_classes.resource_class = fakes.FakeResource(None, {})
        self.quotas = mock.Mock()
        self.quotas.resource_class = fakes.FakeResource(None, {})
        self.restores = mock.Mock()
        self.restores.resource_class = fakes.FakeResource(None, {})
        self.services = mock.Mock()
        self.services.resource_class = fakes.FakeResource(None, {})
        self.transfers = mock.Mock()
        self.transfers.resource_class = fakes.FakeResource(None, {})
        self.volume_encryption_types = mock.Mock()
        self.volume_encryption_types.resource_class = fakes.FakeResource(
            None, {}
        )
        self.volume_snapshots = mock.Mock()
        self.volume_snapshots.resource_class = fakes.FakeResource(None, {})
        self.volume_type_access = mock.Mock()
        self.volume_type_access.resource_class = fakes.FakeResource(None, {})
        self.volume_types = mock.Mock()
        self.volume_types.resource_class = fakes.FakeResource(None, {})
        self.volumes = mock.Mock()
        self.volumes.resource_class = fakes.FakeResource(None, {})


class TestVolume(utils.TestCommand):
    def setUp(self):
        super().setUp()

        self.app.client_manager.volume = FakeVolumeClient(
            endpoint=fakes.AUTH_URL, token=fakes.AUTH_TOKEN
        )

        self.app.client_manager.identity = identity_fakes.FakeIdentityv3Client(
            endpoint=fakes.AUTH_URL, token=fakes.AUTH_TOKEN
        )

        # avoid circular imports by defining this manually rather than using
        # openstackclient.tests.unit.image.v2.fakes.FakeClientMixin
        self.app.client_manager.image = mock.Mock(spec=image_v2_proxy.Proxy)
        self.image_client = self.app.client_manager.image


def create_one_transfer(attrs=None):
    """Create a fake transfer.

    :param dict attrs:
        A dictionary with all attributes of Transfer Request
    :return:
        A FakeResource object with volume_id, name, id.
    """
    # Set default attribute
    transfer_info = {
        'volume_id': 'volume-id-' + uuid.uuid4().hex,
        'name': 'fake_transfer_name',
        'id': 'id-' + uuid.uuid4().hex,
        'links': 'links-' + uuid.uuid4().hex,
    }

    # Overwrite default attributes if there are some attributes set
    attrs = attrs or {}

    transfer_info.update(attrs)

    transfer = fakes.FakeResource(None, transfer_info, loaded=True)

    return transfer


def create_transfers(attrs=None, count=2):
    """Create multiple fake transfers.

    :param dict attrs:
        A dictionary with all attributes of transfer
    :param Integer count:
        The number of transfers to be faked
    :return:
        A list of FakeResource objects
    """
    transfers = []
    for n in range(0, count):
        transfers.append(create_one_transfer(attrs))

    return transfers


def get_transfers(transfers=None, count=2):
    """Get an iterable MagicMock object with a list of faked transfers.

    If transfers list is provided, then initialize the Mock object with the
    list. Otherwise create one.

    :param List transfers:
        A list of FakeResource objects faking transfers
    :param Integer count:
        The number of transfers to be faked
    :return
        An iterable Mock object with side_effect set to a list of faked
        transfers
    """
    if transfers is None:
        transfers = create_transfers(count)

    return mock.Mock(side_effect=transfers)


def create_one_type_access(attrs=None):
    """Create a fake volume type access for project.

    :param dict attrs:
        A dictionary with all attributes
    :return:
        A FakeResource object, with  Volume_type_ID and Project_ID.
    """
    if attrs is None:
        attrs = {}

    # Set default attributes.
    type_access_attrs = {
        'volume_type_id': 'volume-type-id-' + uuid.uuid4().hex,
        'project_id': 'project-id-' + uuid.uuid4().hex,
    }

    # Overwrite default attributes.
    type_access_attrs.update(attrs)

    type_access = fakes.FakeResource(None, type_access_attrs, loaded=True)

    return type_access


def create_one_service(attrs=None):
    """Create a fake service.

    :param dict attrs:
        A dictionary with all attributes of service
    :return:
        A FakeResource object with host, status, etc.
    """
    # Set default attribute
    service_info = {
        'host': 'host_test',
        'binary': 'cinder_test',
        'status': 'enabled',
        'disabled_reason': 'LongHoliday-GoldenWeek',
        'zone': 'fake_zone',
        'updated_at': 'fake_date',
        'state': 'fake_state',
    }

    # Overwrite default attributes if there are some attributes set
    attrs = attrs or {}

    service_info.update(attrs)

    service = fakes.FakeResource(None, service_info, loaded=True)

    return service


def create_services(attrs=None, count=2):
    """Create multiple fake services.

    :param dict attrs:
        A dictionary with all attributes of service
    :param Integer count:
        The number of services to be faked
    :return:
        A list of FakeResource objects
    """
    services = []
    for n in range(0, count):
        services.append(create_one_service(attrs))

    return services


def create_one_capability(attrs=None):
    """Create a fake volume backend capability.

    :param dict attrs:
        A dictionary with all attributes of the Capabilities.
    :return:
        A FakeResource object with capability name and attrs.
    """
    # Set default attribute
    capability_info = {
        "namespace": "OS::Storage::Capabilities::fake",
        "vendor_name": "OpenStack",
        "volume_backend_name": "lvmdriver-1",
        "pool_name": "pool",
        "driver_version": "2.0.0",
        "storage_protocol": "iSCSI",
        "display_name": "Capabilities of Cinder LVM driver",
        "description": "Blah, blah.",
        "visibility": "public",
        "replication_targets": [],
        "properties": {
            "compression": {
                "title": "Compression",
                "description": "Enables compression.",
                "type": "boolean",
            },
            "qos": {
                "title": "QoS",
                "description": "Enables QoS.",
                "type": "boolean",
            },
            "replication": {
                "title": "Replication",
                "description": "Enables replication.",
                "type": "boolean",
            },
            "thin_provisioning": {
                "title": "Thin Provisioning",
                "description": "Sets thin provisioning.",
                "type": "boolean",
            },
        },
    }

    # Overwrite default attributes if there are some attributes set
    capability_info.update(attrs or {})

    capability = fakes.FakeResource(None, capability_info, loaded=True)

    return capability


def create_one_pool(attrs=None):
    """Create a fake pool.

    :param dict attrs:
        A dictionary with all attributes of the pool
    :return:
        A FakeResource object with pool name and attrs.
    """
    # Set default attribute
    pool_info = {
        'name': 'host@lvmdriver-1#lvmdriver-1',
        'storage_protocol': 'iSCSI',
        'thick_provisioning_support': False,
        'thin_provisioning_support': True,
        'total_volumes': 99,
        'total_capacity_gb': 1000.00,
        'allocated_capacity_gb': 100,
        'max_over_subscription_ratio': 200.0,
    }

    # Overwrite default attributes if there are some attributes set
    pool_info.update(attrs or {})

    pool = fakes.FakeResource(None, pool_info, loaded=True)

    return pool


def create_one_volume(attrs=None):
    """Create a fake volume.

    :param dict attrs:
        A dictionary with all attributes of volume
    :return:
        A FakeResource object with id, name, status, etc.
    """
    attrs = attrs or {}

    # Set default attribute
    volume_info = {
        'id': 'volume-id' + uuid.uuid4().hex,
        'name': 'volume-name' + uuid.uuid4().hex,
        'description': 'description' + uuid.uuid4().hex,
        'status': random.choice(['available', 'in_use']),
        'size': random.randint(1, 20),
        'volume_type': random.choice(['fake_lvmdriver-1', 'fake_lvmdriver-2']),
        'bootable': random.randint(0, 1),
        'metadata': {
            'key' + uuid.uuid4().hex: 'val' + uuid.uuid4().hex,
            'key' + uuid.uuid4().hex: 'val' + uuid.uuid4().hex,
            'key' + uuid.uuid4().hex: 'val' + uuid.uuid4().hex,
        },
        'snapshot_id': random.randint(1, 5),
        'availability_zone': 'zone' + uuid.uuid4().hex,
        'attachments': [
            {
                'device': '/dev/' + uuid.uuid4().hex,
                'server_id': uuid.uuid4().hex,
            },
        ],
    }

    # Overwrite default attributes if there are some attributes set
    volume_info.update(attrs)

    volume = fakes.FakeResource(None, volume_info, loaded=True)
    return volume


def create_volumes(attrs=None, count=2):
    """Create multiple fake volumes.

    :param dict attrs:
        A dictionary with all attributes of volume
    :param Integer count:
        The number of volumes to be faked
    :return:
        A list of FakeResource objects
    """
    volumes = []
    for n in range(0, count):
        volumes.append(create_one_volume(attrs))

    return volumes


def create_one_sdk_volume(attrs=None):
    """Create a fake volume.

    :param dict attrs:
        A dictionary with all attributes of volume
    :return:
        A FakeResource object with id, name, status, etc.
    """
    attrs = attrs or {}

    # Set default attribute
    volume_info = {
        'id': 'volume-id' + uuid.uuid4().hex,
        'name': 'volume-name' + uuid.uuid4().hex,
        'description': 'description' + uuid.uuid4().hex,
        'status': random.choice(['available', 'in_use']),
        'size': random.randint(1, 20),
        'volume_type': random.choice(['fake_lvmdriver-1', 'fake_lvmdriver-2']),
        'bootable': random.choice(['true', 'false']),
        'metadata': {
            'key' + uuid.uuid4().hex: 'val' + uuid.uuid4().hex,
            'key' + uuid.uuid4().hex: 'val' + uuid.uuid4().hex,
            'key' + uuid.uuid4().hex: 'val' + uuid.uuid4().hex,
        },
        'snapshot_id': random.randint(1, 5),
        'availability_zone': 'zone' + uuid.uuid4().hex,
        'attachments': [
            {
                'device': '/dev/' + uuid.uuid4().hex,
                'server_id': uuid.uuid4().hex,
            },
        ],
    }

    # Overwrite default attributes if there are some attributes set
    volume_info.update(attrs)
    return volume.Volume(**volume_info)


def create_sdk_volumes(attrs=None, count=2):
    """Create multiple fake volumes.

    :param dict attrs:
        A dictionary with all attributes of volume
    :param Integer count:
        The number of volumes to be faked
    :return:
        A list of FakeResource objects
    """
    volumes = []
    for n in range(0, count):
        volumes.append(create_one_sdk_volume(attrs))

    return volumes


def get_volumes(volumes=None, count=2):
    """Get an iterable MagicMock object with a list of faked volumes.

    If volumes list is provided, then initialize the Mock object with the
    list. Otherwise create one.

    :param List volumes:
        A list of FakeResource objects faking volumes
    :param Integer count:
        The number of volumes to be faked
    :return
        An iterable Mock object with side_effect set to a list of faked
        volumes
    """
    if volumes is None:
        volumes = create_volumes(count)

    return mock.Mock(side_effect=volumes)


def get_volume_columns(volume=None):
    """Get the volume columns from a faked volume object.

    :param volume:
        A FakeResource objects faking volume
    :return
        A tuple which may include the following keys:
        ('id', 'name', 'description', 'status', 'size', 'volume_type',
         'metadata', 'snapshot', 'availability_zone', 'attachments')
    """
    if volume is not None:
        return tuple(k for k in sorted(volume.keys()))
    return tuple([])


def get_volume_data(volume=None):
    """Get the volume data from a faked volume object.

    :param volume:
        A FakeResource objects faking volume
    :return
        A tuple which may include the following values:
        ('ce26708d', 'fake_volume', 'fake description', 'available',
         20, 'fake_lvmdriver-1', "Alpha='a', Beta='b', Gamma='g'",
         1, 'nova', [{'device': '/dev/ice', 'server_id': '1233'}])
    """
    data_list = []
    if volume is not None:
        for x in sorted(volume.keys()):
            if x == 'tags':
                # The 'tags' should be format_list
                data_list.append(format_columns.ListColumn(volume.info.get(x)))
            else:
                data_list.append(volume.info.get(x))
    return tuple(data_list)


def create_one_backup(attrs=None):
    """Create a fake backup.

    :param dict attrs:
        A dictionary with all attributes
    :return:
        A FakeResource object with id, name, volume_id, etc.
    """
    attrs = attrs or {}

    # Set default attributes.
    backup_info = {
        "created_at": 'time-' + uuid.uuid4().hex,
        "data_timestamp": 'time-' + uuid.uuid4().hex,
        "id": 'backup-id-' + uuid.uuid4().hex,
        "encryption_key_id": None,
        "fail_reason": "Service not found for creating backup.",
        "has_dependent_backups": False,
        "is_incremental": False,
        "metadata": {},
        "project_id": uuid.uuid4().hex,
        "updated_at": 'time-' + uuid.uuid4().hex,
        "user_id": uuid.uuid4().hex,
        "name": 'backup-name-' + uuid.uuid4().hex,
        "volume_id": 'volume-id-' + uuid.uuid4().hex,
        "snapshot_id": 'snapshot-id' + uuid.uuid4().hex,
        "description": 'description-' + uuid.uuid4().hex,
        "object_count": None,
        "container": 'container-' + uuid.uuid4().hex,
        "size": random.randint(1, 20),
        "is_incremental": False,
        "status": "error",
        "availability_zone": 'zone' + uuid.uuid4().hex,
    }

    # Overwrite default attributes.
    backup_info.update(attrs)

    backup = _backup.Backup(**backup_info)
    return backup


def create_backups(attrs=None, count=2):
    """Create multiple fake backups.

    :param dict attrs:
        A dictionary with all attributes
    :param int count:
        The number of backups to fake
    :return:
        A list of FakeResource objects faking the backups
    """
    backups = []
    for i in range(0, count):
        backup = create_one_backup(attrs)
        backups.append(backup)

    return backups


def get_backups(backups=None, count=2):
    """Get an iterable MagicMock object with a list of faked backups.

    If backups list is provided, then initialize the Mock object with the
    list. Otherwise create one.

    :param List backups:
        A list of FakeResource objects faking backups
    :param Integer count:
        The number of backups to be faked
    :return
        An iterable Mock object with side_effect set to a list of faked
        backups
    """
    if backups is None:
        backups = create_backups(count)

    return mock.Mock(side_effect=backups)


def create_backup_record():
    """Gets a fake backup record for a given backup.

    :return: An "exported" backup record.
    """

    return {
        'backup_service': 'cinder.backup.drivers.swift.SwiftBackupDriver',
        'backup_url': 'eyJzdGF0dXMiOiAiYXZh',
    }


def import_backup_record():
    """Creates a fake backup record import response from a backup.

    :return: The fake backup object that was encoded.
    """
    return {
        'backup': {
            'id': 'backup.id',
            'name': 'backup.name',
            'links': [
                {'href': 'link1', 'rel': 'self'},
                {'href': 'link2', 'rel': 'bookmark'},
            ],
        },
    }


def create_one_consistency_group(attrs=None):
    """Create a fake consistency group.

    :param dict attrs:
        A dictionary with all attributes
    :return:
        A FakeResource object with id, name, description, etc.
    """
    attrs = attrs or {}

    # Set default attributes.
    consistency_group_info = {
        "id": 'backup-id-' + uuid.uuid4().hex,
        "name": 'backup-name-' + uuid.uuid4().hex,
        "description": 'description-' + uuid.uuid4().hex,
        "status": "error",
        "availability_zone": 'zone' + uuid.uuid4().hex,
        "created_at": 'time-' + uuid.uuid4().hex,
        "volume_types": ['volume-type1'],
    }

    # Overwrite default attributes.
    consistency_group_info.update(attrs)

    consistency_group = fakes.FakeResource(
        info=copy.deepcopy(consistency_group_info), loaded=True
    )
    return consistency_group


def create_consistency_groups(attrs=None, count=2):
    """Create multiple fake consistency groups.

    :param dict attrs:
        A dictionary with all attributes
    :param int count:
        The number of consistency groups to fake
    :return:
        A list of FakeResource objects faking the consistency groups
    """
    consistency_groups = []
    for i in range(0, count):
        consistency_group = create_one_consistency_group(attrs)
        consistency_groups.append(consistency_group)

    return consistency_groups


def get_consistency_groups(consistency_groups=None, count=2):
    """Note:

    Get an iterable MagicMock object with a list of faked
    consistency_groups.

    If consistency_groups list is provided, then initialize
    the Mock object with the list. Otherwise create one.

    :param List consistency_groups:
        A list of FakeResource objects faking consistency_groups
    :param Integer count:
        The number of consistency_groups to be faked
    :return
        An iterable Mock object with side_effect set to a list of faked
        consistency_groups
    """
    if consistency_groups is None:
        consistency_groups = create_consistency_groups(count)

    return mock.Mock(side_effect=consistency_groups)


def create_one_consistency_group_snapshot(attrs=None):
    """Create a fake consistency group snapshot.

    :param dict attrs:
        A dictionary with all attributes
    :return:
        A FakeResource object with id, name, description, etc.
    """
    attrs = attrs or {}

    # Set default attributes.
    consistency_group_snapshot_info = {
        "id": 'id-' + uuid.uuid4().hex,
        "name": 'backup-name-' + uuid.uuid4().hex,
        "description": 'description-' + uuid.uuid4().hex,
        "status": "error",
        "consistencygroup_id": 'consistency-group-id' + uuid.uuid4().hex,
        "created_at": 'time-' + uuid.uuid4().hex,
    }

    # Overwrite default attributes.
    consistency_group_snapshot_info.update(attrs)

    consistency_group_snapshot = fakes.FakeResource(
        info=copy.deepcopy(consistency_group_snapshot_info), loaded=True
    )
    return consistency_group_snapshot


def create_consistency_group_snapshots(attrs=None, count=2):
    """Create multiple fake consistency group snapshots.

    :param dict attrs:
        A dictionary with all attributes
    :param int count:
        The number of consistency group snapshots to fake
    :return:
        A list of FakeResource objects faking the
        consistency group snapshots
    """
    consistency_group_snapshots = []
    for i in range(0, count):
        consistency_group_snapshot = create_one_consistency_group_snapshot(
            attrs,
        )
        consistency_group_snapshots.append(consistency_group_snapshot)

    return consistency_group_snapshots


def get_consistency_group_snapshots(snapshots=None, count=2):
    """Get an iterable MagicMock object with a list of faked cgsnapshots.

    If consistenct group snapshots list is provided, then initialize
    the Mock object with the list. Otherwise create one.

    :param List snapshots:
        A list of FakeResource objects faking consistency group snapshots
    :param Integer count:
        The number of consistency group snapshots to be faked
    :return
        An iterable Mock object with side_effect set to a list of faked
        consistency groups
    """
    if snapshots is None:
        snapshots = create_consistency_group_snapshots(count)

    return mock.Mock(side_effect=snapshots)


def create_one_qos(attrs=None):
    """Create a fake Qos specification.

    :param dict attrs:
        A dictionary with all attributes
    :return:
        A FakeResource object with id, name, consumer, etc.
    """
    attrs = attrs or {}

    # Set default attributes.
    qos_info = {
        "id": 'qos-id-' + uuid.uuid4().hex,
        "name": 'qos-name-' + uuid.uuid4().hex,
        "consumer": 'front-end',
        "specs": {"foo": "bar", "iops": "9001"},
    }

    # Overwrite default attributes.
    qos_info.update(attrs)

    qos = fakes.FakeResource(info=copy.deepcopy(qos_info), loaded=True)
    return qos


def create_one_qos_association(attrs=None):
    """Create a fake Qos specification association.

    :param dict attrs:
        A dictionary with all attributes
    :return:
        A FakeResource object with id, name, association_type, etc.
    """
    attrs = attrs or {}

    # Set default attributes.
    qos_association_info = {
        "id": 'type-id-' + uuid.uuid4().hex,
        "name": 'type-name-' + uuid.uuid4().hex,
        "association_type": 'volume_type',
    }

    # Overwrite default attributes.
    qos_association_info.update(attrs)

    qos_association = fakes.FakeResource(
        info=copy.deepcopy(qos_association_info), loaded=True
    )
    return qos_association


def create_qoses(attrs=None, count=2):
    """Create multiple fake Qos specifications.

    :param dict attrs:
        A dictionary with all attributes
    :param int count:
        The number of Qos specifications to fake
    :return:
        A list of FakeResource objects faking the Qos specifications
    """
    qoses = []
    for i in range(0, count):
        qos = create_one_qos(attrs)
        qoses.append(qos)

    return qoses


def get_qoses(qoses=None, count=2):
    """Get an iterable MagicMock object with a list of faked qoses.

    If qoses list is provided, then initialize the Mock object with the
    list. Otherwise create one.

    :param List qoses:
        A list of FakeResource objects faking qoses
    :param Integer count:
        The number of qoses to be faked
    :return
        An iterable Mock object with side_effect set to a list of faked
        qoses
    """
    if qoses is None:
        qoses = create_qoses(count)

    return mock.Mock(side_effect=qoses)


def create_one_snapshot(attrs=None):
    """Create a fake snapshot.

    :param dict attrs:
        A dictionary with all attributes
    :return:
        A FakeResource object with id, name, description, etc.
    """
    attrs = attrs or {}

    # Set default attributes.
    snapshot_info = {
        "id": 'snapshot-id-' + uuid.uuid4().hex,
        "name": 'snapshot-name-' + uuid.uuid4().hex,
        "description": 'snapshot-description-' + uuid.uuid4().hex,
        "size": 10,
        "status": "available",
        "metadata": {"foo": "bar"},
        "created_at": "2015-06-03T18:49:19.000000",
        "volume_id": 'vloume-id-' + uuid.uuid4().hex,
    }

    # Overwrite default attributes.
    snapshot_info.update(attrs)

    snapshot = fakes.FakeResource(
        info=copy.deepcopy(snapshot_info), loaded=True
    )
    return snapshot


def create_snapshots(attrs=None, count=2):
    """Create multiple fake snapshots.

    :param dict attrs:
        A dictionary with all attributes
    :param int count:
        The number of snapshots to fake
    :return:
        A list of FakeResource objects faking the snapshots
    """
    snapshots = []
    for i in range(0, count):
        snapshot = create_one_snapshot(attrs)
        snapshots.append(snapshot)

    return snapshots


def get_snapshots(snapshots=None, count=2):
    """Get an iterable MagicMock object with a list of faked snapshots.

    If snapshots list is provided, then initialize the Mock object with the
    list. Otherwise create one.

    :param List snapshots:
        A list of FakeResource objects faking snapshots
    :param Integer count:
        The number of snapshots to be faked
    :return
        An iterable Mock object with side_effect set to a list of faked
        snapshots
    """
    if snapshots is None:
        snapshots = create_snapshots(count)

    return mock.Mock(side_effect=snapshots)


def create_one_volume_type(attrs=None, methods=None):
    """Create a fake volume type.

    :param dict attrs:
        A dictionary with all attributes
    :param dict methods:
        A dictionary with all methods
    :return:
        A FakeResource object with id, name, description, etc.
    """
    attrs = attrs or {}
    methods = methods or {}

    # Set default attributes.
    volume_type_info = {
        "id": 'type-id-' + uuid.uuid4().hex,
        "name": 'type-name-' + uuid.uuid4().hex,
        "description": 'type-description-' + uuid.uuid4().hex,
        "extra_specs": {"foo": "bar"},
        "is_public": True,
    }

    # Overwrite default attributes.
    volume_type_info.update(attrs)

    volume_type = fakes.FakeResource(
        info=copy.deepcopy(volume_type_info), methods=methods, loaded=True
    )
    return volume_type


def create_volume_types(attrs=None, count=2):
    """Create multiple fake volume_types.

    :param dict attrs:
        A dictionary with all attributes
    :param int count:
        The number of types to fake
    :return:
        A list of FakeResource objects faking the types
    """
    volume_types = []
    for i in range(0, count):
        volume_type = create_one_volume_type(attrs)
        volume_types.append(volume_type)

    return volume_types


def get_volume_types(volume_types=None, count=2):
    """Get an iterable MagicMock object with a list of faked volume types.

    If volume_types list is provided, then initialize the Mock object with
    the list. Otherwise create one.

    :param List volume_types:
        A list of FakeResource objects faking volume types
    :param Integer count:
        The number of volume types to be faked
    :return
        An iterable Mock object with side_effect set to a list of faked
        volume types
    """
    if volume_types is None:
        volume_types = create_volume_types(count)

    return mock.Mock(side_effect=volume_types)


def create_one_encryption_volume_type(attrs=None):
    """Create a fake encryption volume type.

    :param dict attrs:
        A dictionary with all attributes
    :return:
        A FakeResource object with volume_type_id etc.
    """
    attrs = attrs or {}

    # Set default attributes.
    encryption_info = {
        "volume_type_id": 'type-id-' + uuid.uuid4().hex,
        'provider': 'LuksEncryptor',
        'cipher': None,
        'key_size': None,
        'control_location': 'front-end',
    }

    # Overwrite default attributes.
    encryption_info.update(attrs)

    encryption_type = fakes.FakeResource(
        info=copy.deepcopy(encryption_info), loaded=True
    )
    return encryption_type


def create_one_vol_quota(attrs=None):
    """Create one quota"""
    attrs = attrs or {}

    quota_attrs = {
        'id': 'project-id-' + uuid.uuid4().hex,
        'backups': 100,
        'backup_gigabytes': 100,
        'gigabytes': 10,
        'per_volume_gigabytes': 10,
        'snapshots': 0,
        'volumes': 10,
    }

    quota_attrs.update(attrs)

    quota = fakes.FakeResource(info=copy.deepcopy(quota_attrs), loaded=True)
    quota.project_id = quota_attrs['id']

    return quota


def create_one_default_vol_quota(attrs=None):
    """Create one quota"""
    attrs = attrs or {}

    quota_attrs = {
        'id': 'project-id-' + uuid.uuid4().hex,
        'backups': 100,
        'backup_gigabytes': 100,
        'gigabytes': 100,
        'per_volume_gigabytes': 100,
        'snapshots': 100,
        'volumes': 100,
    }

    quota_attrs.update(attrs)

    quota = fakes.FakeResource(info=copy.deepcopy(quota_attrs), loaded=True)
    quota.project_id = quota_attrs['id']

    return quota


def create_one_detailed_quota(attrs=None):
    """Create one quota"""
    attrs = attrs or {}

    quota_attrs = {
        'volumes': {'limit': 3, 'in_use': 1, 'reserved': 0},
        'per_volume_gigabytes': {'limit': -1, 'in_use': 0, 'reserved': 0},
        'snapshots': {'limit': 10, 'in_use': 0, 'reserved': 0},
        'gigabytes': {'limit': 1000, 'in_use': 5, 'reserved': 0},
        'backups': {'limit': 10, 'in_use': 0, 'reserved': 0},
        'backup_gigabytes': {'limit': 1000, 'in_use': 0, 'reserved': 0},
        'volumes_lvmdriver-1': {'limit': -1, 'in_use': 1, 'reserved': 0},
        'gigabytes_lvmdriver-1': {'limit': -1, 'in_use': 5, 'reserved': 0},
        'snapshots_lvmdriver-1': {'limit': -1, 'in_use': 0, 'reserved': 0},
        'volumes___DEFAULT__': {'limit': -1, 'in_use': 0, 'reserved': 0},
        'gigabytes___DEFAULT__': {'limit': -1, 'in_use': 0, 'reserved': 0},
        'snapshots___DEFAULT__': {'limit': -1, 'in_use': 0, 'reserved': 0},
        'groups': {'limit': 10, 'in_use': 0, 'reserved': 0},
        'id': uuid.uuid4().hex,
    }
    quota_attrs.update(attrs)

    quota = fakes.FakeResource(info=copy.deepcopy(quota_attrs), loaded=True)

    return quota


class FakeLimits(object):
    """Fake limits"""

    def __init__(self, absolute_attrs=None):
        self.absolute_limits_attrs = {
            'totalSnapshotsUsed': 1,
            'maxTotalBackups': 10,
            'maxTotalVolumeGigabytes': 1000,
            'maxTotalSnapshots': 10,
            'maxTotalBackupGigabytes': 1000,
            'totalBackupGigabytesUsed': 0,
            'maxTotalVolumes': 10,
            'totalVolumesUsed': 4,
            'totalBackupsUsed': 0,
            'totalGigabytesUsed': 35,
        }
        absolute_attrs = absolute_attrs or {}
        self.absolute_limits_attrs.update(absolute_attrs)

        self.rate_limits_attrs = [
            {
                "uri": "*",
                "limit": [
                    {
                        "value": 10,
                        "verb": "POST",
                        "remaining": 2,
                        "unit": "MINUTE",
                        "next-available": "2011-12-15T22:42:45Z",
                    },
                    {
                        "value": 10,
                        "verb": "PUT",
                        "remaining": 2,
                        "unit": "MINUTE",
                        "next-available": "2011-12-15T22:42:45Z",
                    },
                    {
                        "value": 100,
                        "verb": "DELETE",
                        "remaining": 100,
                        "unit": "MINUTE",
                        "next-available": "2011-12-15T22:42:45Z",
                    },
                ],
            }
        ]

    @property
    def absolute(self):
        for name, value in self.absolute_limits_attrs.items():
            yield FakeAbsoluteLimit(name, value)

    def absolute_limits(self):
        reference_data = []
        for name, value in self.absolute_limits_attrs.items():
            reference_data.append((name, value))
        return reference_data

    @property
    def rate(self):
        for group in self.rate_limits_attrs:
            uri = group['uri']
            for rate in group['limit']:
                yield FakeRateLimit(
                    rate['verb'],
                    uri,
                    rate['value'],
                    rate['remaining'],
                    rate['unit'],
                    rate['next-available'],
                )

    def rate_limits(self):
        reference_data = []
        for group in self.rate_limits_attrs:
            uri = group['uri']
            for rate in group['limit']:
                reference_data.append(
                    (
                        rate['verb'],
                        uri,
                        rate['value'],
                        rate['remaining'],
                        rate['unit'],
                        rate['next-available'],
                    )
                )
        return reference_data


class FakeAbsoluteLimit(object):
    """Data model that represents an absolute limit."""

    def __init__(self, name, value):
        self.name = name
        self.value = value


class FakeRateLimit(object):
    """Data model that represents a flattened view of a single rate limit."""

    def __init__(self, verb, uri, value, remain, unit, next_available):
        self.verb = verb
        self.uri = uri
        self.value = value
        self.remain = remain
        self.unit = unit
        self.next_available = next_available
