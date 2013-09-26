from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from osstdb.model import Instance, IPaddress

dbconfig = {'engine': 'postgresql',
            'user': 'postgres',
            'passw': 'zaq123',
            'host': 'localhost',
            'port': '5432',
            'dbname': 'osst',
            }

url = '{engine}://{user}:{passw}@{host}:{port}/{dbname}'.format(**dbconfig)
engine = create_engine(url)
session = sessionmaker(bind=engine)()


def get_instance(vmname):
    return session.query(Instance).filter_by(name=vmname).first()


def get_full_vm_info(vmname):
    return session.query(Instance, IPaddress).outerjoin(IPaddress) \
        .filter(Instance.name == vmname).first()


def add_vm(vmname):
    """Insert information about VM state into table "instances"
    """
    vm = Instance(vmname)
    session.add(vm)
    session.flush()
    session.commit()
    return vm


def status_all_vm():
    return session.query(Instance).all()


def delete_vm(vmname):
    vm = get_instance(vmname)
    session.delete(vm)
    session.commit()


def update_status_vm(vmname, status):
    session.query(Instance).filter_by(name=vmname). \
        update({'power_status': status})
    session.commit()


def add_ip_addr(addr, assigned_vm_id=None):
    session.add(IPaddress(addr, assigned_vm_id))
    session.commit()


def delete_ip(addr):
    ip = session.query(IPaddress).filter_by(addr=addr).first()
    if ip:
        session.delete(ip)
        session.commit()


def get_ipaddress(addr):
    return session.query(IPaddress).filter_by(addr=addr).first()


def get_free_ip():
    return session.query(IPaddress).filter_by(assigned_vm_id=None).first()


def exempt_ip(addr):
    session.query(IPaddress).filter_by(addr=addr). \
        update({'assigned_vm_id': None})
    session.commit()


def assign_ip(vmid, mac, addr):
    session.query(IPaddress).filter_by(addr=addr). \
        update({'assigned_vm_id': vmid, 'mac': mac})
    session.commit()
