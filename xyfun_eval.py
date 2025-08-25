# xfyun_eval.py

import websocket
import hashlib
import base64
import hmac
import json
from urllib.parse import urlencode
import time
import ssl
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

appid = "0e99a9fb"
api_secret = "NWUxMzYxNTkyMjlkMjViNGZjZGU5ZTM3"
api_key = "73750d2c681a00cc9d39d6a5729c9bfa"
host_url = "ws://ise-api.xfyun.cn/v2/open-ise"


def run_ise_eval(audio_file_path: str, content: str = "nice to meet you.") -> str:
    """
    use a iFLYTEK to help do the speech recognition score

        audio_file_path:  mp3
        content: 
    """
    result_xml = ""

    def product_url():
        now_time = datetime.now()
        now_date = format_date_time(mktime(now_time.timetuple()))
        origin_base = f"host: ise-api.xfyun.cn\ndate: {now_date}\nGET /v2/open-ise HTTP/1.1"
        signature_sha = hmac.new(api_secret.encode('utf-8'), origin_base.encode('utf-8'), hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode('utf-8')
        authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
        params = {
            "authorization": authorization,
            "date": now_date,
            "host": "ise-api.xfyun.cn"
        }
        return host_url + "?" + urlencode(params)

    def on_message(ws, message):
        nonlocal result_xml
        status = json.loads(message)["data"]["status"]
        if status == 2:
            xml = base64.b64decode(json.loads(message)["data"]["data"])
            result_xml = xml.decode("utf-8")
            ws.close()

    def on_error(ws, error):
        print("WebSocket Error:", error)

    def on_close(ws, close_status_code, close_msg):
        print("WebSocket connection closed.")

    def on_open(ws):
        print("WebSocket opened, sending data...")
        # send the text and initialize
        send_dict = {
            "common": {"app_id": appid},
            "business": {
                "category": "read_sentence",
                "rstcd": "utf8",
                "sub": "ise",
                "group": "pupil",
                "ent": "en_vip",
                "tte": "utf-8",
                "cmd": "ssb",
                "auf": "audio/L16;rate=16000",
                "aue": "lame",
                "text": '\uFEFF' + content
            },
            "data": {"status": 0, "data": ""}
        }
        ws.send(json.dumps(send_dict))

        # send the audio
        with open(audio_file_path, "rb") as f:
            while True:
                chunk = f.read(1280)
                if not chunk:
                    end_packet = {
                        "business": {"cmd": "auw", "aus": 4, "aue": "lame"},
                        "data": {"status": 2, "data": ""}
                    }
                    ws.send(json.dumps(end_packet))
                    break
                audio_packet = {
                    "business": {"cmd": "auw", "aus": 1, "aue": "lame"},
                    "data": {
                        "status": 1,
                        "data": base64.b64encode(chunk).decode("utf-8"),
                        "data_type": 1,
                        "encoding": "raw"
                    }
                }
                ws.send(json.dumps(audio_packet))
                time.sleep(0.04)

    # launch websocket connection
    ws_url = product_url()
    ws_app = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws_app.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
    print(" Return XML original message：\n", result_xml)

    return result_xml
