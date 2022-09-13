import logging.handlers, keyboard, json, sys, requests, datetime

log = logging.getLogger('RPH')

log.setLevel('INFO')
log_handler = logging.handlers.RotatingFileHandler('./rfidhandler.log', maxBytes=1024 * 1024, backupCount=20)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

log.info(f"start RFID HANDLER")

def process_code(code):
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


def send_scan_info(url, rfid):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    res = session.post(f'{url}/api/scanevent?rfid={rfid}&timestamp={now}')
    if res.status_code == 200:
        data = res.json()
        print(data)
    else:
        print('could not send')


test_keyboard = True
try:
    #read configuration file
    with open('server.json') as cfg:
        config = json.loads(cfg.read())
        url = config['url']
        session = requests.Session()
        valid_key = True
        input_string = ''
        while True:
            if test_keyboard:
                input_code = input('enter code: ')
                _, _, output_code = process_code(input_code)
                print(f'scanned code, {output_code}')
                send_scan_info(url, output_code)
            else:
                key = keyboard.read_key()
                if valid_key:
                    if key == 'enter':
                        valid_key = True
                        _, _, output_code = process_code(input_string)
                        input_string = ''
                        log.info(f'scanned code, {output_code}')
                        send_scan_info(url, output_code)
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
