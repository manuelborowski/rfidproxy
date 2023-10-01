import logging.handlers, keyboard, json, sys, requests, datetime, gpiozero, binascii, serial, datetime
from instance.config import RFID_SOURCE, RFID_BEEP_PIN, RFID_REGISTER_OK_PIN, RFID_REGISTER_NOK_PIN

log = logging.getLogger('RPH')

log.setLevel('INFO')
log_handler = logging.handlers.RotatingFileHandler('./log/rfidhandler.log', maxBytes=1024 * 1024, backupCount=20)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

log.info(f"start RFID HANDLER")


def read_server_config_file():
    with open('server.json') as cfg:
        config = json.loads(cfg.read())
    return config


def send_scan_info(url, key, location, rfid):
    now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    # res = session.post(f'{url}/api/scanevent?rfid={rfid}&timestamp={now}')
    res = requests.post(f"{url}/api/registration/add", headers={'x-api-key': key},
                        json={"location_key": location, "badge_code": rfid, "timestamp": now})
    if res.status_code == 200:
        data = res.json()
        print(data)
    else:
        print('could not send')


class Rfid7941W():
    read_uid = bytearray(b'\xab\xba\x00\x10\x00\x10')

    resp_len = 2405

    def test_timer_blink(self, timer):
        self.register_nok_pin.toggle()

    def start(self):
        print("start main")
        self.beep_pin = gpiozero.LED(RFID_BEEP_PIN)
        self.register_ok_pin = gpiozero.LED(RFID_REGISTER_OK_PIN)
        self.register_nok_pin = gpiozero.LED(RFID_REGISTER_NOK_PIN)
        # rfid_serial = machine.UART(0, baudrate=115200, bits=8, parity=None, stop=1, timeout=100)
        rfid_serial = serial.Serial("/dev/ttyS0", 115200, timeout=0.1)
        ctr = 0
        prev_code = ""
        self.register_ok_pin.off()
        self.register_nok_pin.off()

        # machine.Timer(mode=machine.Timer.PERIODIC, period=500, callback=self.test_timer_blink)

        while True:
            config = read_server_config_file()
            rfid_serial.write(self.read_uid)
            rcv_raw = rfid_serial.read(self.resp_len)
            if rcv_raw:
                rcv = binascii.hexlify(rcv_raw).decode("UTF-8")
                if rcv[6:8] == "81":  # valid uid received
                    code = rcv[10:18]
                    if code != prev_code or ctr > 10:
                        self.register_ok_pin.off()
                        self.register_nok_pin.off()
                        # beep()
                        # p6 = machine.PWM(beep_pin, freq=1000, duty_u16=30000)
                        timestamp = datetime.datetime.now().isoformat()
                        ret = requests.post(f"{config['api_url']}/api/registration/add", headers={'x-api-key': config['api_key']},
                                            json={"location_key": config["location"], "badge_code": code, "timestamp": timestamp})
                        # p6.deinit()
                        if ret.status_code == 200:
                            res = ret.json()
                            print(res)
                            if res["status"]:
                                self.register_ok_pin.on()
                            else:
                                self.register_nok_pin.on()
                        print(code)
                        ctr = 0
                    prev_code = code
                    ctr += 1


class RfidKeyboard():
    def process_code(self, code):
        def process_int_code(code):
            if int(code) < 100000:
                #Assumed a student code because it is less then 100.000
                return False, code
            h = '{:0>8}'.format(hex(int(code)).split('x')[-1].upper())
            code = h[6:8] + h[4:6] + h[2:4] + h[0:2]
            return True, code

        def decode_caps_lock(code):
            out = u''
            dd = {u'&': '1', u'É': '2', u'"': '3', u'\'': '4', u'(': '5', u'§': '6', u'È': '7', u'!': '8', u'Ç': '9',
                  u'À': '0', u'A' : 'A', u'B' : 'B', u'C' : 'C', u'D' : 'D', u'E' : 'E', u'F' : 'F'}
            for i in code:
                out += dd[i.upper()]
            return out

        is_rfid_code = True
        is_valid_code = True
        code = code.upper()

        if len(code) == 8:
            #Assumed a HEX code of 8 characters
            if 'Q' in code:
                # This is a HEX code, with the Q iso A
                code = code.replace('Q', 'A')
            try:
                #Code is ok
                int(code, 16)
            except:
                try:
                    # decode because of strange characters (CAPS LOCK)
                    code = decode_caps_lock(code)
                    int(code, 16)
                except:
                    #It shoulde be a HEX code but it is not valid
                    is_valid_code = False
        else:
            #Assumed an INT code
            try:
                #code is ok
                int(code)
                is_rfid_code, code = process_int_code(code)
            except:
                try:
                    # decode because of strange characters (CAPS LOCK)
                    code = decode_caps_lock(code)
                    #code is ok
                    int(code)
                    is_rfid_code, code = process_int_code(code)
                except:
                    #It should be an INT code but it is not valid
                    is_valid_code = False

        return is_valid_code, is_rfid_code, code

    test_keyboard = False
    def start(self):
        try:
            with open('server.json') as cfg:
                config = json.loads(cfg.read())
                url = config['url']
                api_key = config["key"]
                location = config["location"]
                session = requests.Session()
                valid_key = True
                input_string = ''
                while True:
                    if self.test_keyboard:
                        input_code = input('enter code: ')
                        _, _, output_code = self.process_code(input_code)
                        print(f'scanned code, {output_code}')
                        send_scan_info(url, api_key, location, output_code)
                    else:
                        key = keyboard.read_key()
                        if valid_key:
                            if key == 'enter':
                                valid_key = True
                                _, _, output_code = self.process_code(input_string)
                                input_string = ''
                                log.info(f'scanned code, {output_code}')
                                send_scan_info(url, api_key, location, output_code)
                            else:
                                input_string += key
                        valid_key = not valid_key

                    # input_code = input('enter code: ')
                    # _, _, output_code = process_code(input_code)
                    # print(f'output code: {output_code}')
                    # log.info(f'output code: {output_code}')
                    # input('Press enter to close')
        except Exception as e:
            log.error(f'{sys._getframe().f_code.co_name}: {e}')


if RFID_SOURCE == "7941W":
    rfid = Rfid7941W()
    rfid.start()
