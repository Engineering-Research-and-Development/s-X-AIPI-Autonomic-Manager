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
- bootstrap_servers: ‘host[:port]’ string (or list of ‘host[:port]’ strings) If no servers are specified, will default to localhost:9092.
- value_deserializer: callback function used to deserialize data. It may be a custom function, if needed.
- client_id: string representing the name for the client. May be useful server-side to understand who is consuming what
- group_id: string (or None) The name of the consumer group to join for dynamic partition assignment (if enabled), and to use for fetching and committing offsets. 
    If None, auto-partition assignment (via group coordinator) and offset commits are disabled. Default: None
- auto_offset_reset: A policy for resetting offsets on OffsetOutOfRange errors: ‘earliest’ will move to the oldest available message, 
    ‘latest’ will move to the most recent. Any other value will raise the exception. Default: ‘latest’.
'''

class Consumer:
    def __init__(self):
        nums_list = []
        self.consumer = KafkaConsumer('my_topic',
                                      bootstrap_server: 'localhost[:9092]'
                                      value_deserializer=lambda x: loads(x),
                                      group_id='my_group_id',
                                      auto_offset_reset='latest')

    def consume_data(self):
        for message in self.consumer:
            print(f"Received message :{message.value}")
            return message.value
