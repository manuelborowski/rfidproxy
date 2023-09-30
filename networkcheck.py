import logging.handlers, json, sys, requests, datetime, os, time

log = logging.getLogger('NWC')

log.setLevel('INFO')
log_handler = logging.handlers.RotatingFileHandler('./log/networkcheck.log', maxBytes=1024 * 1024, backupCount=20)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

log.info(f"start NETWORK CHECK")

CLOCK_PERIOD = 1  # 1 second
CONNECTED_PING_PERIODS = 5 # when connected, ping every 5 * 1 = 5 secs
TRYING_PING_PERIODS = 1 # when trying to connect, ping every 1 * 1 = 1 secs
PING_HOST = "8.8.8.8"

def ping():
    return os.system(f"ping -c 1 -w 1 {PING_HOST} > /dev/null") == 0

def set_led(state):
    global led_state
    global status_led
    led_state = state
    log.info(f'led state, {led_state}')
    if config['USE_GPIOZERO']:
        if led_state:
            status_led.on()
        else:
            status_led.off()


STATE_TRYING = 'trying'
STATE_CONNECTED = 'connected'
led_state = False
count_connected_ping_periods = CONNECTED_PING_PERIODS
count_trying_ping_periods = TRYING_PING_PERIODS

state = STATE_TRYING
# config
# status_led = None

try:
    with open('./networkcheck.json') as cfg:
        global config
        config = json.loads(cfg.read())
        if config['USE_GPIOZERO']:
            global status_led
            from gpiozero import LED
            status_led = LED(config["LED_PIN"])
        while True:
            if state == STATE_TRYING:
                count_trying_ping_periods -= 1
                if count_trying_ping_periods <= 0:
                    count_trying_ping_periods = TRYING_PING_PERIODS
                    if ping():
                        # ping is ok, change state
                        state = STATE_CONNECTED
                        set_led(True)
                        log.info('network connection is UP')
                    else:
                        # ping is not ok, blink led
                        set_led(not led_state)
            if state == STATE_CONNECTED:
                count_connected_ping_periods -= 1
                if count_connected_ping_periods <= 0:
                    count_connected_ping_periods = CONNECTED_PING_PERIODS
                    if ping():
                        # ping is ok
                        set_led(True)
                    else:
                        # ping is not ok, change state
                        state = STATE_TRYING
                        log.info('network connection is DOWN')
            time.sleep(CLOCK_PERIOD)
except Exception as e:
    log.error(f'{sys._getframe().f_code.co_name}: {e}')
