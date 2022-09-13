from flask import Flask, request
import sys, os, json, html, logging, logging.handlers

# 0.1 : initial version
# 0.2: added small delay before boot so that answer can be send


VERSION = '0.2'

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
log = logging.getLogger('RP')

log.setLevel('INFO')
log_handler = logging.handlers.RotatingFileHandler('./rfidproxy.log', maxBytes=1024 * 1024, backupCount=20)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

log.info(f"start RFID ")

@app.route("/api/wireless", methods=['POST'])
def set_wireless():
    try:
        if 'ssid' in request.args and 'key' in request.args:
            template = app.config['WPA_SUPPLICANT_TEMPLATE']
            template = template.replace('$$SSID$$', request.args['ssid'])
            template = template.replace('$$KEY$$', request.args['key'])
            with open(app.config['WPA_SUPPLICANT_CONFIG'], "w") as cfg:
                cfg.write(template)
            log.info(f"update wireless to ssid {request.args['ssid']}")
            if app.config['REBOOT']:
                os.system("(sleep 1; sudo reboot) &")
            else:
                log.info('update wireless, do not reboot')
                os.system("(sleep 1; echo reboot test) &")
            return json.dumps({"status": True, "data": 'wireless update ok, going to reboot'})
        else:
            log.error(f"update wireless failed, ssid or key not present")
            return json.dumps({"status": False, "data": '/api/wireless?ssid=XXX&key=XXX'})
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return json.dumps({"status": False, "data": html.escape(str(e))})


@app.route("/api/version", methods=['GET'])
def get_version():
    try:
        return json.dumps({"status": True, "data": f'@2022 MB V{VERSION}'})
    except Exception as e:
        log.error(f'{sys._getframe().f_code.co_name}: {e}')
        return json.dumps({"status": False, "data": html.escape(str(e))})


