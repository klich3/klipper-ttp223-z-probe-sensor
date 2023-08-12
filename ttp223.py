"""
█▀ █▄█ █▀▀ █░█ █▀▀ █░█
▄█ ░█░ █▄▄ █▀█ ██▄ ▀▄▀

Author: <Anton Sychev> (anton at sychev dot xyz) 
ttp223.py (c) 2023 
Created:  2023-08-13 01:32:39 
Desc: Z sensor TTP223 inductive low cost sensor, its connect to BLTouch port
      Based on BLTouch plugin by KevinOConnor
Docs: documentation
"""

import logging
from . import probe

SIGNAL_PERIOD = 0.020
MIN_CMD_TIME = 5 * SIGNAL_PERIOD

TEST_TIME = 5 * 60.
RETRY_RESET_TIME = 1.
ENDSTOP_REST_TIME = .001
ENDSTOP_SAMPLE_TIME = .000015
ENDSTOP_SAMPLE_COUNT = 4


class TTP223:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:connect",
                                            self.handle_connect)
        self.printer.register_event_handler('klippy:mcu_identify',
                                            self.handle_mcu_identify)
        self.position_endstop = config.getfloat('z_offset', minval=0.)
        self.stow_on_each_sample = config.getboolean('stow_on_each_sample',
                                                     True)
        self.probe_touch_mode = config.getboolean('probe_with_touch_mode',
                                                  False)
        # Create a pwm object to handle the control pin
        ppins = self.printer.lookup_object('pins')

        # Command timing
        self.next_cmd_time = self.action_end_time = 0.
        self.finish_home_complete = self.wait_trigger_complete = None

        # Create an "endstop" object to handle the sensor pin
        pin = config.get('sensor_pin')
        pin_params = ppins.lookup_pin(pin, can_invert=True, can_pullup=True)
        mcu = pin_params['chip']
        self.mcu_endstop = mcu.setup_pin('endstop', pin_params)

        self.pin_up_not_triggered = config.getboolean(
            'pin_up_reports_not_triggered', True)
        self.pin_up_touch_triggered = config.getboolean(
            'pin_up_touch_mode_reports_triggered', True)

        # Calculate pin move time
        self.pin_move_time = config.getfloat('pin_move_time', 0.680, above=0.)

        # Wrappers
        self.get_mcu = self.mcu_endstop.get_mcu
        self.add_stepper = self.mcu_endstop.add_stepper
        self.get_steppers = self.mcu_endstop.get_steppers
        self.home_wait = self.mcu_endstop.home_wait
        self.query_endstop = self.mcu_endstop.query_endstop

        self.gcode = self.printer.lookup_object('gcode')

        # multi probes state
        self.multi = 'OFF'

    def handle_mcu_identify(self):
        kin = self.printer.lookup_object('toolhead').get_kinematics()
        for stepper in kin.get_steppers():
            if stepper.is_active_axis('z'):
                self.add_stepper(stepper)

    def handle_connect(self):
        self.next_cmd_time += 0.200

    def sync_print_time(self):
        toolhead = self.printer.lookup_object('toolhead')
        print_time = toolhead.get_last_move_time()
        if self.next_cmd_time > print_time:
            toolhead.dwell(self.next_cmd_time - print_time)
        else:
            self.next_cmd_time = print_time

    def verify_state(self, triggered):
        # Perform endstop check to verify bltouch reports desired state
        self.mcu_endstop.home_start(self.action_end_time, ENDSTOP_SAMPLE_TIME,
                                    ENDSTOP_SAMPLE_COUNT, ENDSTOP_REST_TIME,
                                    triggered=triggered)
        trigger_time = self.mcu_endstop.home_wait(self.action_end_time + 0.100)
        return trigger_time > 0.

    def verify_raise_probe(self):
        if not self.pin_up_not_triggered:
            # No way to verify raise attempt
            return
        for retry in range(3):
            success = self.verify_state(False)
            if success:
                # The "probe raised" test completed successfully
                break
            if retry >= 2:
                raise self.printer.command_error(
                    "TTP223 failed to raise probe")
            msg = "Failed to verify TTP223 probe is raised; retrying."
            self.gcode.respond_info(msg)
            # self.send_cmd('reset', duration=RETRY_RESET_TIME)

    def multi_probe_begin(self):
        if self.stow_on_each_sample:
            return
        self.multi = 'FIRST'

    def multi_probe_end(self):
        if self.stow_on_each_sample:
            return
        self.sync_print_time()
        self.raise_probe()
        self.verify_raise_probe()
        self.sync_print_time()
        self.multi = 'OFF'

    def probe_prepare(self, hmove):
        if self.multi == 'OFF' or self.multi == 'FIRST':
            if self.multi == 'FIRST':
                self.multi = 'ON'
        self.sync_print_time()

    def home_start(self, print_time, sample_time, sample_count, rest_time,
                   triggered=True):
        rest_time = min(rest_time, ENDSTOP_REST_TIME)
        self.finish_home_complete = self.mcu_endstop.home_start(
            print_time, sample_time, sample_count, rest_time, triggered)
        # Schedule wait_for_trigger callback
        r = self.printer.get_reactor()
        self.wait_trigger_complete = r.register_callback(self.wait_for_trigger)
        return self.finish_home_complete

    def wait_for_trigger(self, eventtime):
        self.finish_home_complete.wait()
        if self.multi == 'OFF':
            self.raise_probe()

    def probe_finish(self, hmove):
        self.wait_trigger_complete.wait()
        if self.multi == 'OFF':
            self.verify_raise_probe()
        self.sync_print_time()
        if hmove.check_no_movement() is not None:
            raise self.printer.command_error("TTP223 failed to deploy")

    def get_position_endstop(self):
        return self.position_endstop


def load_config(config):
    blt = TTP223(config)
    config.get_printer().add_object('probe', probe.PrinterProbe(config, blt))
    return blt
