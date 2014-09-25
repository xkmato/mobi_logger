#!/usr/bin/env python

import socket
import time
from sh import tail
import sys


CARBON_SERVER = '0.0.0.0'
CARBON_PORT = 2003
DELAY = 5


class Logger(object):
    def __init__(self, line):
        self.timestamp = line.split(',')[0]
        data = line.split('!')[1]
        data_logger, actual_data = tuple(data.split(','))
        self.data_logger = data_logger.split()
        self.actual_data = actual_data.split()
        self.full_cur = int(self.data_logger[2], 16)

    def get_timestamp(self):
        t = time.strptime(self.timestamp.split('+')[0], '%Y-%m-%d %H:%M:%S')
        return time.mktime(t)

    def get_state_of_charge(self):
        menu_state = self.data_logger[13]
        soc = self.actual_data[1]
        print "Log Value Soc====", soc
        if int(menu_state, 16) & 7 == 0:
            return float(soc)/30*100
        return float(soc)/35*100

    def get_battery_voltage(self):
        volt = float(self.actual_data[3])
        return volt*0.032+9

    def get_end_charge(self):
        charge = float(self.actual_data[4])
        return charge*0.032+9

    def _cx_type(self):
        if self.full_cur > 50: cx_type = 10
        elif 23 < self.full_cur < 30: cx_type = 20
        elif self.full_cur < 22: cx_type = 40
        return cx_type

    def get_load_current(self):
        load_current = float(self.actual_data[6])
        return load_current/self.full_cur*self._cx_type()

    def get_temperature(self):
        return int(self.actual_data[12]) + 25

    def get_pv_current(self):
        return float(self.actual_data[14])/self.full_cur*self._cx_type()


def send_msg(message):
    print 'sending message:\n%s' % message
    sock = socket.socket()
    sock.connect((CARBON_SERVER, CARBON_PORT))
    sock.sendall(message)
    sock.close()


if __name__ == '__main__':
    logfile = sys.argv[1]
    print logfile
    x = 1
    for line in tail("-fn 1000", logfile, _iter=True):
        if line.strip():
            log = Logger(line)
            lines = [
                'mobi.serail_008.SOC %s %d' % (log.get_state_of_charge(), log.get_timestamp()),
                'mobi.serail_008.BatteryVoltage %s %d' % (log.get_battery_voltage(), log.get_timestamp()),
                'mobi.serail_008.EndChargeVoltage %s %d' % (log.get_end_charge(), log.get_timestamp()),
                'mobi.serail_008.LoadCurrent %s %d' % (log.get_load_current(), log.get_timestamp()),
                'mobi.serail_008.Temperature %s %d' % (log.get_temperature(), log.get_timestamp()),
                'mobi.serail_008.PVCurrent %s %d' % (log.get_pv_current(), log.get_timestamp()),
            ]
            message = '\n'.join(lines) + '\n'
            send_msg(message)
            time.sleep(DELAY)
        print 'Loop', x, 'done'
        x+=1