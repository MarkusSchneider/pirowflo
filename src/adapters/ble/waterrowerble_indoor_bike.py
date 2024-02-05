#!/usr/bin/env python3

# ---------------------------------------------------------------------------
# Original code from the PunchThrough Repo espresso-ble
# https://github.com/PunchThrough/espresso-ble
# ---------------------------------------------------------------------------
#
import logging
import signal
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import struct

from .ble import (
    Advertisement,
    Characteristic,
    Service,
    Application,
    find_adapter,
    Descriptor,
    Agent,
)

MainLoop = None

try:
    from gi.repository import GLib

    MainLoop = GLib.MainLoop

except ImportError:
    import gobject as GObject

    MainLoop = GObject.MainLoop

DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"

GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
GATT_DESC_IFACE = "org.bluez.GattDescriptor1"

LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"

logger = logging.getLogger(__name__)

mainloop = None

class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"


class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotSupported"


class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotPermitted"


class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.InvalidValueLength"


class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.Failed"


def register_app_cb():
    logger.info("GATT application registered")


def register_app_error_cb(error):
    logger.critical("Failed to register application: " + str(error))
    mainloop.quit()

# Function is needed to trigger the reset of the waterrower. It puts the "reset_ble" into the queue (FIFO) in order
# for the WaterrowerInterface thread to get the signal to reset the waterrower.

def request_reset_ble():
    out_q_reset.put("reset_ble")

def Convert_Waterrower_raw():

    WaterrowerValuesRaw = ble_in_q_value.pop()

    for keys in WaterrowerValuesRaw:
        WaterrowerValuesRaw[keys] = int(WaterrowerValuesRaw[keys])

    return WaterrowerValuesRaw
    # #todo refactor this part with the correct struct.pack e.g. 2 bytes use "H" instand of bitshifiting ?
    # #print(WaterrowerValuesRaw)
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['stroke_rate'] & 0xff)))                       # 0
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_strokes'] & 0xff)))                     # 1 
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_strokes'] & 0xff00) >> 8))              # 2
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_distance_m'] & 0xff)))                  # 3
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_distance_m'] & 0xff00) >> 8))           # 4
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_distance_m'] & 0xff0000) >> 16))        # 5
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['instantaneous pace'] & 0xff)))                # 6
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['instantaneous pace'] & 0xff00) >> 8))         # 7
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['watts'] & 0xff)))                             # 8
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['watts'] & 0xff00) >> 8))                      # 9
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_kcal'] & 0xff)))                        #10
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_kcal'] & 0xff00) >> 8))                 #11
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_kcal_hour'] & 0xff)))                   #12
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_kcal_hour'] & 0xff00) >> 8))            #13
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['total_kcal_min'] & 0xff)))                    #14
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['heart_rate'] & 0xff)))                        #15
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['elapsedtime'] & 0xff)))                       #16
    # WRBytearray.append(struct.pack("B", (WaterrowerValuesRaw['elapsedtime'] & 0xff00) >> 8))                #17
    # return WRBytearray


class DeviceInformation(Service):
    DEVICE_INFORMATION_UUID = '180A'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.DEVICE_INFORMATION_UUID, True)
        self.add_characteristic(ManufacturerNameString(bus, 0, self))
        self.add_characteristic(ModelNumberString(bus, 1, self))
        self.add_characteristic(SerialNumberSring(bus,2,self))
        self.add_characteristic(HardwareRevisionString(bus,3,self))
        self.add_characteristic(FirmwareRevisionString(bus,4,self))
        self.add_characteristic(SoftwareRevisionString(bus, 5, self))

class ManufacturerNameString(Characteristic):
    MANUFACTURER_NAME_STRING_UUID = '2a29'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.MANUFACTURER_NAME_STRING_UUID,
            ['read'],
            service)
        self.notifying = False
        self.ManuName = bytes('Waterrower', 'utf-8')
        self.value = dbus.Array(self.ManuName)  # ble com module waterrower software revision


    def ReadValue(self, options):
        print('ManufacturerNameString: ' + repr(self.value))
        return self.value

class ModelNumberString(Characteristic):
    MANUFACTURER_NAME_STRING_UUID = '2a24'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.MANUFACTURER_NAME_STRING_UUID,
            ['read'],
            service)
        self.notifying = False
        self.ManuName = bytes('4', 'utf-8')
        self.value = dbus.Array(self.ManuName)  # ble com module waterrower software revision


    def ReadValue(self, options):
        print('ModelNumberString: ' + repr(self.value))
        return self.value

class SerialNumberSring(Characteristic):
    MANUFACTURER_NAME_STRING_UUID = '2a25'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.MANUFACTURER_NAME_STRING_UUID,
            ['read'],
            service)
        self.notifying = False
        self.ManuName = bytes('0000', 'utf-8')
        self.value = dbus.Array(self.ManuName)  # ble com module waterrower software revision


    def ReadValue(self, options):
        print('SerialNumberSring: ' + repr(self.value))
        return self.value

class HardwareRevisionString(Characteristic):
    MANUFACTURER_NAME_STRING_UUID = '2a27'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.MANUFACTURER_NAME_STRING_UUID,
            ['read'],
            service)
        self.notifying = False
        self.ManuName = bytes('2.2BLE', 'utf-8')
        self.value = dbus.Array(self.ManuName)  # ble com module waterrower software revision


    def ReadValue(self, options):
        print('HardwareRevisionString: ' + repr(self.value))
        return self.value

class FirmwareRevisionString(Characteristic):
    MANUFACTURER_NAME_STRING_UUID = '2a26'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.MANUFACTURER_NAME_STRING_UUID,
            ['read'],
            service)
        self.notifying = False
        self.ManuName = bytes('0.30', 'utf-8')
        self.value = dbus.Array(self.ManuName)  # ble com module waterrower software revision


    def ReadValue(self, options):
        print('FirmwareRevisionString: ' + repr(self.value))
        return self.value

class SoftwareRevisionString(Characteristic):
    SOFTWARE_REVISION_STRING_UUID = '2a28'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.SOFTWARE_REVISION_STRING_UUID,
            ['read'],
            service)
        self.notifying = False
        #self.value = [dbus.Byte(0), dbus.Byte(0), dbus.Byte(0), dbus.Byte(0)]  # ble com module waterrower software revision
        self.value = [dbus.Byte(0), dbus.Byte(0), dbus.Byte(0)]  # ble com module waterrower software revision

        self.value[0] = 0x34
        self.value[1] = 0x2E
        self.value[2] = 0x33
        #self.value[3] = 0x30

    def ReadValue(self, options):
        print('SoftwareRevisionString: ' + repr(self.value))
        return self.value

class FitnessMachineService(Service):
    FITNESS_MACHINE_UUID = '1826'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.FITNESS_MACHINE_UUID, True)
        self.add_characteristic(FitnessMachineFeature(bus,0,self))
        self.add_characteristic(IndoorBikeData(bus, 1, self))
        self.add_characteristic(FitnessMachineControlPoint(bus, 2, self))

class FitnessMachineFeature(Characteristic):

    FITNESS_MACHINE_FEATURE_UUID = '2ACC'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.FITNESS_MACHINE_FEATURE_UUID,
            ['read'],
            service)
        self.notifying = False

        # Bit  Definition
        # 0     Average Speed Supported
        # 1     Cadence Supported
        # 2     Total Distance Supported
        # 3     Inclination Supported
        # 4     Elevation Gain Supported
        # 5     Pace Supported
        # 6     Step Count Supported
        # 7     Resistance Level Supported
        # 8     Stride Count Supported
        # 9     Expended Energy Supported
        # 10    Heart Rate Measurement Supported
        # 11    Metabolic Equivalent Supported
        # 12    Elapsed Time Supported
        # 13    Remaining Time Supported
        # 14    Power Measurement Supported
        # 15    Force on Belt and Power Output Supported
        # 16    User Data Retention Supported
        # 17-31 Reserved for Future Use
        
        # Fitness Machine Features (32bit), Target Setting Features (32bit)
        self.value = [dbus.Byte(0),dbus.Byte(0),dbus.Byte(0),dbus.Byte(0),dbus.Byte(0),dbus.Byte(0),dbus.Byte(0),dbus.Byte(0)]

        self.value[0] = 0b00001010
        self.value[1] = 0b00100000
        self.value[2] = 0b00000000
        self.value[3] = 0b00000000
        self.value[4] = 0b00000000
        self.value[5] = 0b00000000
        self.value[6] = 0b00000000
        self.value[7] = 0b00000000

    def ReadValue(self, options):
        print('FITNESS MACHINE Feature: ' + repr(self.value))
        return self.value

class IndoorBikeData(Characteristic):
    INDOOR_BIKE_DATA_UUID = '2AD2'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.INDOOR_BIKE_DATA_UUID,
            ['notify'],
            service)
        self.notifying = False
        self.iter = 0

    def Waterrower_cb(self):
        if ble_in_q_value:
            values = Convert_Waterrower_raw()
            power = values["watts"].to_bytes(2, 'little')
            cadence = (values["stroke_rate"] * 2).to_bytes(2, 'little')

            # Bit  Definition
            # 0     More Data
            # 1     Average Speed
            # 2     Instantaneous Cadence
            # 3     Average Cadence
            # 4     Total Distance 
            # 5     Resistance Leve
            # 6     Instantaneous Power
            # 7     Average Power
            # 8     Expended Energy
            # 9     Heart Rate
            # 10    Metabolic Equivalent
            # 11    Elapsed Time
            # 12    Remaining Time
            # 13    Elapsed Time Supported
            # 14    Remaining Time Supported     
            
            value = [
                dbus.Byte(0b11000101), dbus.Byte(0x00),                     # 16-bit Flags
                dbus.Byte(cadence[0]), dbus.Byte(cadence[1]),
                dbus.Byte(power[0]), dbus.Byte(power[1]),
                dbus.Byte(power[0]), dbus.Byte(power[1]),
            ]

            self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': value }, [])
            return self.notifying
        else:
            logger.warning("no data from s4 interface")
            pass

    def _update_Waterrower_cb_value(self):
        print('Update Waterrower Data')

        if not self.notifying:
            return

        GLib.timeout_add(200, self.Waterrower_cb)

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        self._update_Waterrower_cb_value()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False
        self._update_Waterrower_cb_value()

class FitnessMachineControlPoint(Characteristic):
    FITNESS_MACHINE_CONTROL_POINT_UUID = '2ad9'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.FITNESS_MACHINE_CONTROL_POINT_UUID,
            ['indicate', 'write'],
            service)
        self.out_q = None

    def fmcp_cb(self, byte):
        print('fmcp_cb activate')
        print(byte)
        if byte == 0:
            value = [dbus.Byte(128), dbus.Byte(0), dbus.Byte(1)]
        elif byte == 1:
            value = [dbus.Byte(128), dbus.Byte(1), dbus.Byte(1)]
            request_reset_ble()
        #print(value)
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

    def WriteValue(self, value, options):
        self.value = value
        print(value)
        byte = self.value[0]
        print('Fitness machine control point: ' + repr(self.value))
        if byte == 0:
            print('Request control')
            self.fmcp_cb(byte)
        elif byte == 1:
            print('Reset')
            self.fmcp_cb(byte)

class FitnessMachineAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_manufacturer_data(
            0xFFFF, [0x77, 0x72],
        )
        self.add_service_uuid(DeviceInformation.DEVICE_INFORMATION_UUID)
        self.add_service_uuid(FitnessMachineService.FITNESS_MACHINE_UUID)
        # Fitness Machine Available Bit 1, Indoor Bike Supported Bit 5
        self.add_service_data(FitnessMachineService.FITNESS_MACHINE_UUID, [0b00000001, 0b00100000, 0b00000000] )

        #self.add_local_name("S4 Comms PI")
        self.add_local_name("WaterRower")
        self.include_tx_power = True


def register_ad_cb():
    logger.info("Advertisement registered")

def register_ad_error_cb(error):
    logger.critical("Failed to register advertisement: " + str(error))
    mainloop.quit()

def sigint_handler(sig, frame):
    if sig == signal.SIGINT:
        mainloop.quit()
    else:
        raise ValueError("Undefined handler for '{}' ".format(sig))

AGENT_PATH = "/com/inonoob/agent"

def main(out_q,ble_in_q): #out_q
    global mainloop
    global out_q_reset
    global ble_in_q_value
    out_q_reset = out_q
    ble_in_q_value = ble_in_q

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    # get the system bus
    bus = dbus.SystemBus()
    # get the ble controller
    adapter = find_adapter(bus)

    if not adapter:
        logger.critical("GattManager1 interface not found")
        return

    adapter_obj = bus.get_object(BLUEZ_SERVICE_NAME, adapter)

    adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")

    # powered property on the controller to on
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    # Get manager objs
    service_manager = dbus.Interface(adapter_obj, GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(adapter_obj, LE_ADVERTISING_MANAGER_IFACE)

    advertisement = FitnessMachineAdvertisement(bus, 0)
    obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")

    agent = Agent(bus, AGENT_PATH)

    app = Application(bus)
    app.add_service(DeviceInformation(bus, 1))
    app.add_service(FitnessMachineService(bus, 2))

    mainloop = MainLoop()

    agent_manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput") # register the bluetooth agent with no input and output which should avoid asking for pairing 

    ad_manager.RegisterAdvertisement(
        advertisement.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )

    logger.info("Registering GATT application...")

    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=[register_app_error_cb],
    )

    agent_manager.RequestDefaultAgent(AGENT_PATH)

    mainloop.run()
    # ad_manager.UnregisterAdvertisement(advertisement)
    # dbus.service.Object.remove_from_connection(advertisement)

#
# if __name__ == "__main__":
#     signal.signal(signal.SIGINT, sigint_handler)

