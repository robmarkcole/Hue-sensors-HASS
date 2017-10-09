@requests_mock.Mocker()
def test_hue_sensors(self, mock_req):
    """Test for hue_sensors."""
    with requests_mock.mock() as mock_req:
        mock_url = hass.data[DOMAIN] + '/sensors'
        mock_req.get(mock_url, text=load_fixture('hue_sensors.json'))
        data = HueSensorData(mock_url, parse_hue_api_response)
        data.update()
        sensors = []
        for key in data.data.keys():
            sensor = HueSensor(key, data)
            sensor.update()
            sensors.append(sensor)
        assert len(sensors) == 6
        for sensor in sensors:
            if sensor.name == 'Living room motion sensor':
                assert sensor.state is 'off'
                assert sensor.device_state_attributes[
                    'light_level'] == 0
                assert sensor.device_state_attributes[
                    'temperature'] == 21.38
            elif sensor.name == 'Living room remote':
                assert sensor.state == '1_hold'
                assert sensor.device_state_attributes[
                    'last updated'] == ['2017-09-15', '16:35:00']
            elif sensor.name == 'Robins iPhone':
                assert sensor.state is 'on'
            else:
                assert sensor.name in [
                    'Bedroom motion sensor',
                    'Remote bedroom',
                    'Hall motion Sensor']
