import logging.handlers, json, sys, requests, datetime, os, time
from instance import config
import gpiozero

log = logging.getLogger('NWC')

log.setLevel('INFO')
log_handler = logging.handlers.RotatingFileHandler('./log/networkcheck.log', maxBytes=1024 * 1024, backupCount=20)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

log.info(f"start NETWORK CHECK")

CLOCK_PERIOD = 0.5  # seconds


def ping():
    return os.system(f"ping -c 1 -w 1 {config.NWC_PING_HOST} > /dev/null") == 0


STATE_TRYING = 'trying'
STATE_CONNECTED = 'connected'
count_connected_ping_periods = config.NWC_CONNECTED_PING_PERIODS
count_trying_ping_periods = config.NWC_TRYING_PING_PERIODS

state = STATE_TRYING
try:
    status_led = gpiozero.LED(config.NWC_LED_PIN)
    while True:
        if state == STATE_TRYING:
            count_trying_ping_periods -= 1
            if count_trying_ping_periods <= 0:
                count_trying_ping_periods = config.NWC_TRYING_PING_PERIODS
                if ping():
                    # ping is ok, change state
                    state = STATE_CONNECTED
                    status_led(True)
                    log.info('network connection is UP')
                else:
                    # ping is not ok, blink led
                    status_led.toggle()
        if state == STATE_CONNECTED:
            count_connected_ping_periods -= 1
            if count_connected_ping_periods <= 0:
                count_connected_ping_periods = config.NWC_CONNECTED_PING_PERIODS
                if ping():
                    # ping is ok
                    status_led(True)
                else:
                    # ping is not ok, change state
                    state = STATE_TRYING
                    log.info('network connection is DOWN')
        time.sleep(CLOCK_PERIOD)
except Exception as e:
    log.error(f'{sys._getframe().f_code.co_name}: {e}')
