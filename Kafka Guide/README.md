
The snippet of code can be used to consume data from a Kafka topic. 
The provided class encapsulates an instance of a KafkaConsumer and a method to deserialize messages.
It is possible to modify it using the following advices and/or any further hints from the provided kafka library

A KafkaConsumer is a client that consumes data from a kafka topic. 
The base constructor of this client does not require any mandatory field, as explained in the docs: kafka.KafkaConsumer(*topics, **configs)
It accepts an optional list of topics and a series of keyword arguments.

Here a list of the possible arguments accepted by the class:
 - **topics**: a topic or a list of topics to subscribe to. It is possible to leave it empty and then subscribe to topics by using the "subscribe()" or "assign()" methods before receiving data

- **bootstrap_servers**: ‘host:port’ string (or list of ‘host:port’ strings) If no servers are specified, will default to localhost:9092.
- **value_deserializer**: callback function used to deserialize data. It may be a custom function, if needed.
- **client_id**: string representing the name for the client. May be useful server-side to understand who is consuming what
- **group_id**: string (or None) The name of the consumer group to join for dynamic partition assignment (if enabled), and to use for fetching and committing offsets. If None, auto-partition assignment (via group coordinator) and offset commits are disabled. Default: None
- **auto_offset_reset**: A policy for resetting offsets on OffsetOutOfRange errors: ‘earliest’ will move to the oldest available message, 
    ‘latest’ will move to the most recent. Any other value will raise the exception. Default: ‘latest’.
The code is provided with almost every correct configuration. The only exceptions are the topic list and the URL which need to be modified based on your needs

The **consume_data** method prints the value of the received message and return it

```python
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
```
The above snippet is running part of the code. It is possible to add logic to process incoming data inside the try-catch construct, handling both success and failures while receiving data. 
