#!/usr/bin/env python

import pyawair.auth
import pyawair.devices
import pyawair.data
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, REGISTRY
import os

class AwairCollector(object):
    def collect(self):
        auth = pyawair.auth.AwairAuth(os.environ['AWAIR_TOKEN'])

        rate_limited = GaugeMetricFamily(
            'awair_rate_limited',
            'Boolean that is 1 if 429 API rate limit received',
            labels=[''])

        try:
            print("Getting device list")
            devices = pyawair.devices.get_all_devices(auth)

            device_labels = [
                'name', 'device_type', 'device_uuid', 'device_id',
            ]

            score = GaugeMetricFamily('awair_score', 'Awair air quality score (0-100)',
                labels=device_labels)

            for device in devices:
                print(" - Getting data for " + device['name'])
                data = pyawair.data.get_current_air_data(
                    auth,
                    device_type=device['deviceType'],
                    device_id=device['deviceId'],
                    )[0]

                print('   - score: ' + str(data['score']))
                label_values = [device['name'], device['deviceType'], device['deviceUUID'], str(device['deviceId'])]
                score.add_metric(label_values, data['score'])
                yield score

                for sensor in data['sensors']:
                    print('   - ' + sensor['comp'] + ': ' + str(data['score']))
                    g = GaugeMetricFamily(
                        'awair_sensor_' + sensor['comp'],
                        'Awair sensor data for component ' + sensor['comp'],
                        labels=device_labels)
                    g.add_metric(label_values, sensor['value'])
                    yield g
        except ConnectionError as e:
            if '429' in str(e):
                print('Error: ' + str(e))
                rate_limited.add_metric([], value=1)
                yield rate_limited
                return
            raise

        rate_limited.add_metric([], value=0)
        yield rate_limited

if __name__ == '__main__':
    if 'AWAIR_TOKEN' not in os.environ:
        print("AWAIR_TOKEN must be set")

    REGISTRY.register(AwairCollector())

    # Start up the server thread in the background to expose the metrics.
    start_http_server(8000)

    import time
    while True:
        time.sleep(1)