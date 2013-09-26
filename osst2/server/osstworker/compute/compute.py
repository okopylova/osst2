"""Manage VMs with CirrOS OS, based on existing VM disk image"""

import os
import shutil
import libvirt
from argparse import ArgumentParser
import xml.etree.ElementTree as ET
from os.path import expanduser, join
import osstdb.dbhandler as dbhandler
from osstdb.model import Instance
from osstworker.network.network import assign_ip, exempt_ip
import osstworker.rpcserver as rpcserver


driver = 'qemu:///system'
home = expanduser('~')
base_disk_path = join(home, 'vm_disks')
base_vm_img = '../data/base_vm_disk.img'
vm_conf_templ_path = 'config/vm_conf_templ.xml'

_conn = libvirt.open(driver)
_vm_conf_template = open(vm_conf_templ_path).read()


def list_all():
    """Returns list of all defined VM names"""

    return (_conn.listDefinedDomains() +
            [_conn.lookupByID(id).name() for id in _conn.listDomainsID()])


def create(vmname, addr=None):
    """Create VM with specified name

    Keyword arguments:
    vmname -- name of the created VM

    Raise libvirt.libvirtError if VM with this name already exists"""

    imgpath = os.path.join(base_disk_path, vmname + '.img')
    shutil.copyfile(base_vm_img, imgpath)
    config = _vm_conf_template.format(**locals())
    vm = _conn.defineXML(config)
    xml = ET.fromstring(vm.XMLDesc(0))
    mac = xml.find('devices').find('interface').find('mac').attrib['address']
    vm_info = dbhandler.add_vm(vmname)
    assign_ip(vm_info.id, mac, addr)
    return 'VM %s created' % vmname


def delete(vmname, deldisk=True):
    """Delete VM with specified name

    Keyword arguments:
    vmname -- name of the created VM
    deldisk -- specifies whether to perform deletion of VM disk image
    (default: True)

    Raise libvirt.libvirtError if VM with this name doesn't exist"""

    dom = _conn.lookupByName(vmname)
    if dom.isActive():
        dom.destroy()
        dbhandler.update_status_vm(vmname, Instance.STATUS_POWER_OFF)
    dom.undefine()
    full_info = dbhandler.get_full_vm_info(vmname)
    if full_info.IPaddress:
        exempt_ip(full_info.IPaddress.addr)
    dbhandler.delete_vm(vmname)
    if deldisk:
        os.remove(os.path.join(base_disk_path, dom.name() + '.img'))
    return 'VM %s deleted' % vmname


def power_on(vmname):
    """Start VM with specified name
    Raise libvirt.libvirtError if VM with this name doesn't exist
    or it is already running"""

    _conn.lookupByName(vmname).create()
    dbhandler.update_status_vm(vmname, Instance.STATUS_POWER_ON)
    return 'VM %s powered on' % vmname


def power_off(vmname):
    """Stop VM with specified name
    Throws libvirt.libvirtError if VM with this name doesn't exist
    or it is not running"""

    _conn.lookupByName(vmname).destroy()  # cirros don't know shutdown command
    dbhandler.update_status_vm(vmname, Instance.STATUS_POWER_OFF)
    return 'VM %s powered off' % vmname


def reboot(vmname):
    """Reboot VM with specified name
    Throws libvirt.libvirtError if VM with this name doesn't exist
    or it is not running"""

    dom = _conn.lookupByName(vmname)
    # cirros also don't know reboot command
    dom.destroy()
    dbhandler.update_status_vm(vmname, Instance.STATUS_POWER_OFF)
    dom.create()
    dbhandler.update_status_vm(vmname, Instance.STATUS_POWER_ON)
    return 'VM %s rebooted' % vmname


if __name__ == '__main__':
    parser = ArgumentParser(description='Starts network RPC server')
    parser.add_argument('-host', default='localhost')
    args = parser.parse_args()
    rpcserver.start_rpc_server(args.host, 'compute',
                               'osstworker.compute.compute')
