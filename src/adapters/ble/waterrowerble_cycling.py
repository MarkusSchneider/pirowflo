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

class CyclingPowerService(Service):
    CYCLING_POWER_UUID = '1818'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.CYCLING_POWER_UUID, True)
        self.add_characteristic(CyclingPowerFeature(bus,0,self))
        self.add_characteristic(CyclingPowerData(bus, 1, self))
        self.add_characteristic(FitnessMachineControlPoint(bus, 2, self))


class CyclingPowerFeature(Characteristic):

    CYCLING_POWER_FEATURE_UUID = '2a65'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CYCLING_POWER_FEATURE_UUID,
            ['read'],
            service)
        self.notifying = False

        # Configure the Cycle Power Feature characteristic
        # See: https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.cycling_power_feature.xml
        # Properties = Read
        # Min Len    = 1
        # Max Len    = 32
        #    B0:3    = UINT8 - Cycling Power Feature (MANDATORY)
        #      b0    = Pedal power balance supported; 0 = false, 1 = true
        #      b1    = Accumulated torque supported; 0 = false, 1 = true
        #      b2    = Wheel revolution data supported; 0 = false, 1 = true
        #      b3    = Crank revolution data supported; 0 = false, 1 = true
        #      b4    = Extreme magnatudes supported; 0 = false, 1 = true
        #      b5    = Extreme angles supported; 0 = false, 1 = true
        #      b6    = Top/bottom dead angle supported; 0 = false, 1 = true
        #      b7    = Accumulated energy supported; 0 = false, 1 = true
        #      b8    = Offset compensation indicator supported; 0 = false, 1 = true
        #      b9    = Offset compensation supported; 0 = false, 1 = true
        #      b10   = Cycling power measurement characteristic content masking supported; 0 = false, 1 = true
        #      b11   = Multiple sensor locations supported; 0 = false, 1 = true
        #      b12   = Crank length adj. supported; 0 = false, 1 = true
        #      b13   = Chain length adj. supported; 0 = false, 1 = true
        #      b14   = Chain weight adj. supported; 0 = false, 1 = true
        #      b15   = Span length adj. supported; 0 = false, 1 = true
        #      b16   = Sensor measurement context; 0 = force, 1 = torque
        #      b17   = Instantaineous measurement direction supported; 0 = false, 1 = true
        #      b18   = Factory calibrated date supported; 0 = false, 1 = true
        #      b19   = Enhanced offset compensation supported; 0 = false, 1 = true
        #   b20:21   = Distribtue system support; 0 = legacy, 1 = not supported, 2 = supported, 3 = RFU
        #   b22:32   = Reserved
        self.value = [dbus.Byte(0),dbus.Byte(0),dbus.Byte(0),dbus.Byte(0)]

        self.value[0] = 0x00001011
        self.value[1] = 0x00
        self.value[2] = 0x00
        self.value[3] = 0x00

    def ReadValue(self, options):
        print('CYCLING POWER Feature: ' + repr(self.value))
        return self.value

class CyclingPowerData(Characteristic):
    CYCLING_POWER_MEASUREMENT_UUID = '2a63'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
            self, bus, index,
            self.CYCLING_POWER_MEASUREMENT_UUID,
            ['notify'],
            service)
        self.notifying = False
        self.iter = 0

    def Waterrower_cb(self):

            # Configure the Cycle Power Measurement characteristic
            # See: https://www.bluetooth.com/specifications/gatt/viewer?attributeXmlFile=org.bluetooth.characteristic.cycling_power_measurement.xml
            # Properties = Notify
            # Min Len    = 2
            # Max Len    = 34
            #    B0:1    = UINT16  - Flag (MANDATORY)
            #      b0    = Pedal power balance present; 0 = false, 1 = true
            #      b1    = Pedal power balance reference; 0 = unknown, 1 = left
            #      b2    = Accumulated torque present; 0 = false, 1 = true
            #      b3    = Accumulated torque source; 0 = wheel, 1 = crank
            #      b4    = Wheel revolution data present; 0 = false, 1 = true
            #      b5    = Crank revolution data present; 0 = false, 1 = true
            #      b6    = Extreme force magnatudes present; 0 = false, 1 = true
            #      b7    = Extreme torque magnatues present; 0 = false, 1 = true
            #      b8    = Extreme angles present; 0 = false, 1 = true
            #      b9    = Top dead angle present; 0 = false, 1 = true
            #      b10   = Bottom dead angle present; 0 = false, 1 = true
            #      b11   = Accumulated energy present; 0 = false, 1 = true
            #      b12   = Offset compensation indicator; 0 = false, 1 = true
            #      b13   = Reseved
            #      b14   = n/a
            #      b15   = n/a
            #    B2:3    = SINT16 - Instataineous power, Watts (decimal)
            #    B4      = UINT8  -  Pedal power balance, Percent (binary) 1/2
            #    B5:6    = UINT16 - Accumulated torque, Nm; res (binary) 1/32
            #    B7:10   = UINT32 - Cumulative wheel revolutions, (decimal)
            #    B11:12  = UINT16 - Last wheel event time, second (binary) 1/2048
            #    B13:14  = UINT16 - Cumulative crank revolutions, (decimal)
            #    B15:16  = UINT16 - Last crank event time, second (binary) 1/1024 
            #    B17:18  = SINT16 - Max force magnitude, Newton (decimal)
            #    B19:20  = SINT16 - Min force magnitude, Newton (decimal)
            #    B21:22  = SINT16 - Max torque magnitude, Nm (binary) 1/1024
            #    B23:24  = SINT16 - Min torque magnitude, Nm (binary) 1/1024
            #    B25:26  = UINT12 - Max angle, degree (decimal)
            #    B27:28  = UINT12 - Min angle, degree (decimal)
            #    B29:30  = UINT16 - Top dead spot angle, degree (decimal)
            #    B31:32  = UINT16 - Bottom dead spot angle, degree (decimal)
            #    B33:34  = UINT16 - Accumulated energy, kJ (decimal)
        
        if ble_in_q_value:
            values = Convert_Waterrower_raw()
            power = values["watts"].to_bytes(2, 'little')
            cadence = (values["total_strokes"] * 2).to_bytes(2, 'little')
            elapsedtime = (values["elapsedtime"] * 1024) & 0xFFFF
            time = elapsedtime.to_bytes(2, 'little')
            
            logger.info("total_strokes: " + str(values["total_strokes"]))
            logger.info("elapsedtime: " + str(values["elapsedtime"]))

            value = [
                dbus.Byte(0b00100001), dbus.Byte(0x00),                     # 16-bit Flags
                dbus.Byte(power[0]), dbus.Byte(power[1]),                   #    B2:3    = SINT16 - Instataineous power, Watts (decimal)
                #    B4      = UINT8  -  Pedal power balance, Percent (binary) 1/2
                #    B5:6    = UINT16 - Accumulated torque, Nm; res (binary) 1/32
                #    B7:10   = UINT32 - Cumulative wheel revolutions, (decimal)
                #    B11:12  = UINT16 - Last wheel event time, second (binary) 1/2048
                dbus.Byte(cadence[0]), dbus.Byte(cadence[1]),                #    B13:14  = UINT16 - Cumulative crank revolutions, (decimal)
                dbus.Byte(time[0]), dbus.Byte(time[1])                       #    B15:16  = UINT16 - Last crank event time, second (binary) 1/1024 
                #    B17:18  = SINT16 - Max force magnitude, Newton (decimal)
                #    B19:20  = SINT16 - Min force magnitude, Newton (decimal)
                #    B21:22  = SINT16 - Max torque magnitude, Nm (binary) 1/1024
                #    B23:24  = SINT16 - Min torque magnitude, Nm (binary) 1/1024
                #    B25:26  = UINT12 - Max angle, degree (decimal)
                #    B27:28  = UINT12 - Min angle, degree (decimal)
                #    B29:30  = UINT16 - Top dead spot angle, degree (decimal)
                #    B31:32  = UINT16 - Bottom dead spot angle, degree (decimal)
                #    B33:34  = UINT16 - Accumulated energy, kJ (decimal)
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


class CyclingAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, "peripheral")
        self.add_manufacturer_data(
            0xFFFF, [0x77, 0x72],
        )
        self.add_service_uuid(DeviceInformation.DEVICE_INFORMATION_UUID)
        self.add_service_uuid(CyclingPowerService.CYCLING_POWER_UUID)

        #self.add_local_name("S4 Comms PI")
        self.add_local_name("PiRowFlo")
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

    advertisement = CyclingAdvertisement(bus, 0)
    obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")

    agent = Agent(bus, AGENT_PATH)

    app = Application(bus)
    app.add_service(DeviceInformation(bus, 1))
    app.add_service(CyclingPowerService(bus, 2))

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

