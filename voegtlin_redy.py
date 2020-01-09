#!/usr/bin/env python

from pymodbus.client.sync import ModbusSerialClient as ModbusClient
#from pymodbus.payload import BinaryPayloadDecoder
import logging, itertools, argparse, struct

class RedY():

    def __init__(self, unit, modbus_client):
        self.unit = unit
        self.mc = modbus_client

    @classmethod
    def nwords(self, kind):
        if kind in ('uint16', 'uint16_bm'):
            return 1
        elif kind in ('uint32', 'uint32_bm', 'float32'):
            return 2
        elif kind in ('str_8', ):
            return 4
        else:
            raise NotImplementedError()

    @classmethod
    def decode(self, kind, words):
        if kind == 'uint16':
            return words[0]
        elif kind == 'uint32':
            return (words[0] << 16) + words[1]
        elif kind == 'float32':
            a = words # alias for shorter lines
            # with BinaryPayloadDecoder
            #data = [a[0] & 0xff, a[0] >> 8, a[1] & 0xff, a[1] >> 8]
            #decoder = BinaryPayloadDecoder(bytes(data))
            #value = decoder.decode_32bit_float()
            # with struct.unpack
            data = [a[0] >> 8, a[0] & 0xff, a[1] >> 8, a[1] & 0xff]
            value = struct.unpack('>f', bytes(data))[0]
            #
            return value
        elif kind == 'uint16_bm':
            status = words[0]
            return [(status >> i) & 1 for i in range(16)]
        elif kind == 'uint32_bm':
            status = (words[0] << 16) + words[1]
            return [(status >> i) & 1 for i in range(32)]
        elif kind == 'str_8':
            bstr = bytes(itertools.chain(*([w >> 8, w & 0xff] for w in words)))
            return bstr.split(b'\0',1)[0].decode('ascii')
        else:
            raise NotImplementedError()

    def read_all(self):
        for addr, rw, kind, name, descr in red_y_registers:
            if r not in rw:
                # skip non readable (write-only) registers
                continue
            try:
                nwords = RedY.nwords(kind)
            except NotImplementedError:
                print(f"{kind} not implemented yet")
                print('----')
                continue
            rr = self.mc.read_holding_registers(addr, nwords, unit=self.unit)
            print(f"0x{addr:04X} ({kind}) - {name} ({descr})")
            print(rr.registers)
            try:
                print(repr(RedY.decode(kind, rr.registers)))
            except NotImplementedError:
                pass
            print('----')

red_y_registers = [
(0x0000, 'r',  'float32',   'Gas flow',                   'Measured value'),
(0x0002, 'r',  'float32',   'Temperature',                'Measured value'),
(0x0004, 'rw', 'float32',   'Totaliser',                  'Total gas flown'),
(0x0006, 'rw', 'float32',   'Setpoint gas flow',          'Control setpoint of gas flow'),
(0x0008, 'r',  'float32',   'Measured value analog input','Measured value of analog input port'),
(0x000a, 'rw', 'float32',   'Valve control signal',       'Actual value of the valve control signal'),
(0x000c, 'r',  'uint16_bm', 'Alarm',                      'Alarm status'),
(0x000d, 'r',  'uint16_bm', 'Hardware error',             'Indicator for possible malfunction'),
(0x000e, 'rw', 'uint16_bm', 'Control function',           'Selection of the controller mode'),
(0x0013, 'rw', 'uint16',    'Instrument address',         'Sets the Modbus instrument address'),
(0x0014, 'r',  'float32',   'Measuring range',            'Calibrated measuring range of the instrument'),
(0x0016, 'r',  'str_8',     'Unit of measured value',     'Engineering unit of measured value'),
(0x001a, 'r',  'str_8',     'Name of fluid',              'Name of the measured gas'),
(0x001e, 'r',  'uint32',    'Serial number hardware',     'Serial number of the electronic module'),
(0x0020, 'r',  'uint16',    'Version number hardware',    'Development stage of the electronic module'),
(0x0021, 'r',  'uint16',    'Version number software',    'Development stage of the software'),
(0x0022, 'rw', 'uint16',    'E2PROM actualisation',       'Stores the settings in the non-volatile memory'),
(0x0023, 'r',  'str_8',     'Instrument name',            'Name of the instrument'),
(0x0028, 'rw', 'float32',   'Analog output manual',       'Manual setting of the analog output'),
(0x002d, 'rw', 'uint16',    'Scanning speed S',           'PWM scanning speed non linear/linear range'),
(0x002e, 'rw', 'float32',   'Gain factor KP',             'Control parameter gain'),
(0x0030, 'rw', 'float32',   'Time constant TN',           'Control parameter integral time'),
(0x0032, 'rw', 'uint16',    'Feed forward F',             'Control parameter feed forward'),
(0x0033, 'rw', 'uint16',    'Non linearity N',            'Control parameter valve offset compensation'),
(0x0034, 'w',  'uint16',    'Soft reset',                 'Resets all  parameters to the power-on status'),
(0x0035, 'rw', 'uint16_bm', 'Set of control parameters',  'Selection of predefined control parameters'),
(0x4040, 'rw', 'uint16',    'Power-up alarm',             'Activation of the power-up alarm function'),
(0x4041, 'rw', 'float32',   'Power-up alarm setpoint',    'Setpoint of power-up alarm'),
(0x4043, 'rw', 'uint16',    'Totaliser function',         'Function of the totaliser'),
# r or rw???:
(0x4046, 'r',  'float32',   'Totaliser scaling factor',   'Scaling factor of the totaliser'),
# r or rw???:
(0x4048, 'rw', 'str_8',     'Totaliser unit',             'Engineering unit of the total'),
# r or rw???:
(0x404c, 'rw', 'float32',   'Zero point suppression',     'Zero point suppression'),
(0x404f, 'w',  'uint16',    'Reset hardware error',       'Reset of the status hardware error'),
(0x4050, 'rw', 'uint16',    'Automatic storage E2PROM',   'Storage mode of the non-volatile memory'),
(0x4052, 'rw', 'float32',   'Backflow detection',         'Indicates a negative flow'),
(0x4084, 'r',  'uint16',    'Signal type analog output',  'Signal type of the analog measured value output'),
(0x4085, 'r' , 'uint16',    'Signal type setpoint',       'Signal type of the analog setpoint input'),
(0x4087, 'rw', 'uint16',    'Delay hardware error',       'Delay time for the plausibility check at a hardware error'),
# not available with older firmware versions:
#(0x4128, 'r',  'uint32_bm', 'Implemented functions',      'Implemented functions (options) according to the type of instrument'),
# not available with older firmware versions:
#(0x4139, 'r',  'uint16',    'Calibration data set',       'Selection of the calibration data set')
]

def main():
    parser = argparse.ArgumentParser(description='Talk to a voegtlin red-y flow controller')
    parser.add_argument('port', help='The serial interface your Modbus device is connected to.')
    parser.add_argument('--unit', default=247, type=int, help='The slave address of the Modbus device')
    args = parser.parse_args()

    logging.basicConfig()
    log = logging.getLogger()
    #log.setLevel(logging.DEBUG)

    client = ModbusClient(method='rtu', port=args.port, stopbits=2, baudrate=9600)
    try:
        client.connect()

        redy = RedY(unit=args.unit, modbus_client=client)
        redy.read_all()

    finally:
        client.close()

if __name__ == "__main__":
    main()
