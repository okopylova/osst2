'''Client for osst VM manager API'''
import argparse
import urllib2
import json


def build_json(**kwargs):
    return json.dumps(kwargs)


def requester(host, port, section, action, json=None, method=None):
    '''Send requests for VM manager API functions and
    output result on screen'''

    url = 'http://%s:%d/api/v1/%s/%s' % (host, port, section, action)
    print url
    req = urllib2.Request(url, json)
    if method:  # if method is undefined, POST used by default
        req.get_method = lambda: method
    try:
        print urllib2.urlopen(req).read()
    except urllib2.HTTPError, e:
        print e.read()


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('-host', default='localhost')
    parser.add_argument('-port', type=int, default=8080)
    subparsers = parser.add_subparsers()
    compute = subparsers.add_parser('compute')
    compute.set_defaults(section='compute')
    subparsers_compute = compute.add_subparsers()
    for act in ['create', 'power_on', 'reboot', 'power_off', 'delete']:
        subparser = subparsers_compute.add_parser(act)
        subparser.add_argument('-vmname', required=True)
        subparser.set_defaults(action=act)

    network = subparsers.add_parser('network')
    network.set_defaults(section='network')
    subparsers_network = network.add_subparsers()
    subparser = subparsers_network.add_parser('add_ip_range')
    subparser.add_argument('-addr_start', required=True)
    subparser.add_argument('-addr_end', required=True)
    subparser.set_defaults(action='add_ip_range')

    subparser = subparsers.add_parser('list_all')
    subparser.set_defaults(action='list_all')
    args = parser.parse_args()
    http_methods = {'list_all': 'GET', 'create': 'PUT', 'delete': 'DELETE',
                    'add_ip_range': 'PUT'}
    json_data = None
    if hasattr(args, 'vmname'):
        json_data = build_json(vmname=args.vmname)
    else:
        json_data = build_json(addr_start=args.addr_start,
                               addr_end=args.addr_end)
    requester(args.host, args.port, args.section, args.action,
              json_data, http_methods.get(args.action))


if __name__ == '__main__':
    main()
