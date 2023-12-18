from json import loads

from kafka import KafkaConsumer


class Consumer:
    def __init__(self):
        nums_list = []
        self.consumer = KafkaConsumer('weather_data',
                                      value_deserializer=lambda x: loads(x),
                                      group_id='my_weather_group',
                                      auto_offset_reset='latest')

    def consume_data(self):
        for message in self.consumer:
            print(f"Received message :{message.value}")
            return message.value
