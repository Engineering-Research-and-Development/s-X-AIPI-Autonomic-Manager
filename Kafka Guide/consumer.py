# For further information, please consult the official guide at: https://kafka-python.readthedocs.io/en/master/index.html
# Before using the consumer class, please, install the library by using "pip install kafka-python"

from json import loads
from kafka import KafkaConsumer



class Consumer:
    def __init__(self):
        nums_list = []
        self.consumer = KafkaConsumer('my_topic',
                                      bootstrap_servers = ['URL:9092'],
                                      value_deserializer =lambda x: loads(x),
                                      auto_offset_reset='latest')

    def consume_data(self):
        for message in self.consumer:
            print(f"Received message :{message.value}")
            return message.value


if __name__ == "__main__":
    consumer = Consumer()   
    while True:
        try:
            message = consumer.consume_data()
            # onSuccess flow -> do stuff
            # Add your logic for HITL
        except ValueError:
            # On error flow -> manage errors
            pass
