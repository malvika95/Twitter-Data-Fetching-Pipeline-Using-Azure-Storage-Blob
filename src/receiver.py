from azure.servicebus import ServiceBusClient, ServiceBusMessage
import resources.azure_messaging_config as conf
import json

def read_queue():
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=conf.CONNECTION_STR, logging_enable=True)
    with servicebus_client:
        # get the Queue Receiver object for the queue
        receiver = servicebus_client.get_queue_receiver(queue_name=conf.QUEUE_NAME, max_wait_time=5)
        with receiver:
            for c, msg in enumerate(receiver):
                print("Msg "+str(c+1))
                print("Received: " + str(msg))
                msg_dict = json.loads(str(msg))
                # complete the message so that the message is removed from the queue
                receiver.complete_message(msg)


if __name__ == '__main__':
    read_queue()