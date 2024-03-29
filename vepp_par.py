import http.client
import time
import datetime
import csv
import json


class Req(object):
    """docstring for """

    def __init__(self, host, port, path):
        self.host = host
        self.port = port
        self.path = path

    def get_freq(self, response):

        js = json.loads(response)
        return js

    def get_chunk_compress(self, uuid, fields, level):
        headers = {'Content-type': 'application/json'}
        data = {"fields": fields, "level": level}
        data_js = json.dumps(data)
        conn = http.client.HTTPConnection(self.host, self.port)
        conn.request("POST", self.path + "/chunk_compress/" + str(uuid), data_js, headers)
        response = conn.getresponse().read().decode('utf-8')
        return response

    def CursorCompress(self, t1, t2, channels, level, fields=None):
        try:
            data = {"t1": t1, "t2": t2, "channels": channels, "fields": fields, "level": level}

            data_js = json.dumps(data)
            headers = {'Content-type': 'application/json'}
            conn = http.client.HTTPConnection(self.host, self.port)
            conn.request("POST", self.path + "/cursor_compress", data_js, headers)
            response = conn.getresponse()
            js = json.loads(response.read().decode('utf-8'))
            data = response.read()
            count = 0
            current_uuid = js["first"]["uuid"]
            length = js["len_dict"]
            while (count < length):
                r = self.get_chunk_compress(current_uuid, fields, level)
                current_chunk = self.get_freq(r)
                yield current_chunk
                current_uuid = current_chunk.get("next", None)
                if current_uuid is None:
                    break

                count += 1
            return js
        except KeyError:
            logging.error("1")


if __name__ == '__main__':
    req = Req("172.16.1.117", 80, "/api/v1")
    array = []
    csv_writers = {}
    channels = ['VEPP/Currents/FZ']

    for ch in channels:
        name = str(ch).replace('/', '_') + '.csv'
        csvfile = open(name, 'w')
        writer = csv.DictWriter(csvfile, fieldnames=['time', 'value'])
        csv_writers[ch] = (csvfile, writer)


    def close_files():
        while csv_writers:
            name, (csvfile, writer) = csv_writers.popitem()
            csvfile.close()


    try:
        for chunk in req.CursorCompress("2018-06-01 14:00:00.00000", "2018-06-01 14:47:00.00000", channels, "raw"):
            for ch in channels:
                csvfile, writer = csv_writers[ch]
                try:
                    for i in chunk[ch]:
                        writer.writerow({
                            "time": str(datetime.datetime.strptime(i["time"], '%Y-%m-%d %H:%M:%S.%f')),
                            "value": str(i["value"])
                        })
                except(KeyError):
                    pass

    except Exception as e:

        print(e)
        raise

    finally:
        close_files()

