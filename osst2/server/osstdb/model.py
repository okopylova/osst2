from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Instance(Base):
    __tablename__ = 'instances'

    STATUS_POWER_OFF = 0
    STATUS_POWER_ON = 1

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    power_status = Column(Integer,
                          default=STATUS_POWER_OFF)
    vm_state = Column(Integer,
                      default=STATUS_POWER_OFF)

    def __init__(self, name, power_status=None):
        self.name = name
        self.power_status = power_status

    def __repr__(self):
        return "<Instance(name='%r', power_status='%r')>" % (self.name,
                                                             self.power_status)


class IPaddress(Base):
    __tablename__ = 'ipaddr'

    id = Column(Integer, primary_key=True, unique=True)
    addr = Column(String(15), unique=True)  # 15 is length of IPv4 adress representation
    assigned_vm_id = Column(Integer, ForeignKey('instances.id'), nullable=True)
    mac = Column(String(17))  # length of mac address string representation


    @staticmethod
    def validate_addr(addr):
        '''Validate IPv4 address'''
        octets = addr.split('.')
        return len(octets) == 4 and \
            all(map(lambda o: o.isdigit() and 0 <= int(o) < 256, octets))

    @staticmethod
    def range(addr_start, addr_end):
        if not IPaddress.validate_addr(addr_start) and \
                IPaddress.validate_addr(addr_start):
            raise ValueError('Invalid IPv4 address format')
        oct_start = map(int, addr_start.split('.'))
        oct_end = map(int, addr_end.split('.'))
        for oct3 in xrange(oct_start[2], oct_end[2] + 1):
            for oct4 in xrange(oct_start[3], oct_end[3] + 1):
                addr = '%d.%d.%d.%d' % (oct_start[0], oct_start[1], oct3, oct4)
                yield addr

    def __init__(self, addr, assigned_vm_id=None, mac=None):
        if IPaddress.validate_addr(addr):
            self.addr = addr
        else:
            raise ValueError('Invalid IPv4 address format')
        self.assigned_vm_id = assigned_vm_id
        self.mac = mac

    def __repr__(self):
        return ("<IPaddress(addr='%r', assigned_vm_id='%r', mac='%r')>" %
                (self.addr, self.assigned_vm_id, self.mac))
