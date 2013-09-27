#!/usr/bin/env python
"""
To use script, add this lines to your /etc/sudoers file:
youruser ALL=NOPASSWD: /usr/bin/pkill
youruser ALL=NOPASSWD: /sbin/brctl
youruser ALL=NOPASSWD: /sbin/ip
youruser ALL=NOPASSWD: /sbin/iptables
youruser ALL=NOPASSWD: /sbin/ifconfig
where 'youruser' is user who run this script


"""

from subprocess import Popen, PIPE, call
import os
from osstdb import dbhandler
from argparse import ArgumentParser
from osstdb.model import IPaddress
import osstworker.amqpserver as amqpserver

home = os.path.expanduser('~')
hostsfile = 'config/dnsmasq_dhcp_hostsfile.conf'
conffile = 'config/dnsmasq.conf'


def _del_file_line(fname, line_pattern):
    with open(fname, 'r') as fd:
        lines = fd.readlines()
        for ln in lines:
            if ln.rfind(line_pattern) != -1:
                lines.remove(ln)
                with open(fname, 'w') as wfd:
                    wfd.writelines(lines)
                break


def dnsmasq_hangup():
    cmd = "sudo pkill -HUP -o dnsmasq"
    (stdout, stderr) = Popen(cmd.split(), stdout=PIPE).communicate()
    print 'stdout %s\nstderr %s' % (stdout, stderr)


def bridge_settings():
    call([os.path.join(home, 'osst/network/bridge_settings.sh')])


def assign_ip(vmid, mac, ip=None):
    bridge_settings()
    if ip:  # check if address is availiable
        ip_obj = dbhandler.get_ipaddress(ip)
        if not ip_obj or ip_obj.assigned_vm_id:
            raise ValueError("IP address '%s' is not availiable" % ip)
    else:  # get free ip address
        ip_obj = dbhandler.get_free_ip()
        if ip_obj:
            ip = ip_obj.addr
        else:
            raise ValueError("No free IP addresses")
    dbhandler.assign_ip(vmid, mac, ip)
    with open(hostsfile, 'a') as fd:
        fd.write('%s,%s\n' % (mac, ip))
    dnsmasq_hangup()


def exempt_ip(addr):
    _del_file_line(hostsfile, addr + '\n')
    dbhandler.exempt_ip(addr)


def add_ip_range(addr_start, addr_end):
    "Add allocated IP range in database. For last two octets only"
    for addr in IPaddress.range(addr_start, addr_end):
        dbhandler.add_ip_addr(addr)
    with open(conffile, 'a') as fd:
        fd.write('\ndhcp-range=set:br0,%s,%s,static' % (addr_start, addr_end))
    dnsmasq_hangup()


def del_ip_range(addr_start, addr_end):
    addresses = IPaddress.range(addr_start, addr_end)
    with open(hostsfile, 'r') as fd:
        lines = fd.readlines()
        print lines
        for addr in addresses:
            dbhandler.delete_ip(addr)
            for ln in lines:
                if ln.rfind(addr + '\n') != -1:
                    lines.remove(ln)
                    print addr
                    break
        print lines
        with open(hostsfile, 'w') as wfd:
            wfd.writelines(lines)
        _del_file_line(conffile, addr_start + ',' + addr_end)


if __name__ == '__main__':
    parser = ArgumentParser(description='Starts network RPC server')
    parser.add_argument('-host', default='localhost')
    args = parser.parse_args()
    amqpserver.start(args.host, 'network', 'osstworker.network.network')
