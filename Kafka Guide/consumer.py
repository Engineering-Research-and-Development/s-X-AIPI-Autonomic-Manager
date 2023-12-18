# For further information, please consult the official guide at: https://kafka-python.readthedocs.io/en/master/index.html
# Before using the consumer class, please, install the library by using "pip install kafka-python"

from json import loads
from kafka import KafkaConsumer


'''
The following snippet of code teaches how to use a KafkaConsumer to consume data from a kafka topic. The following class encapsulate an instance of a KafkaConsumer and a method to deserialize message.
It is possible to modify it using the following advices and/or any further hints from the provided library

A KafkaConsumer is a client that consumes data from a kafka topic. 
The base constructor of this client does not require any mandatory field, as explained in the docs: kafka.KafkaConsumer(*topics, **configs)
It accepts an optional list of topics and a series of keyword arguments.

From the topic perspective, it is possible to leave it empty and then subscribe to topics by using the "subscribe()" or "assign()" methods before receiving data
About the keyword arguments, here a list of the most used and important ones and their meaning:

'''

class Consumer:
    def __init__(self):
        nums_list = []
        self.consumer = KafkaConsumer('my_topic',
                                      value_deserializer=lambda x: loads(x),
                                      group_id='my_weather_group',
                                      auto_offset_reset='latest')

    def consume_data(self):
        for message in self.consumer:
            print(f"Received message :{message.value}")
            return message.value
