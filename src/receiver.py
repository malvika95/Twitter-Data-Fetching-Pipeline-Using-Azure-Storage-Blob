import os
from random import randint
from azure.storage.blob import BlobServiceClient
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import resources.azure_messaging_config as conf
import json
from datetime import datetime
import pandas as pd
import time


def read_queue():
    servicebus_client = ServiceBusClient.from_connection_string(conn_str=conf.CONNECTION_STR, logging_enable=True)
    with servicebus_client:
        # get the Queue Receiver object for the queue
        receiver = servicebus_client.get_queue_receiver(queue_name=conf.QUEUE_NAME, max_wait_time=5)
        queue_empty = True
        with receiver:
            for c, msg in enumerate(receiver):
                queue_empty = False
                print("Msg "+str(c+1))
                print("Received: " + str(msg))
                msg_dict = json.loads(str(msg))
                # complete the message so that the message is removed from the queue
                upload_to_blob(msg_dict)
                receiver.complete_message(msg)

        return queue_empty

def upload_to_blob(message):
    data_frame = pd.DataFrame(message["data"])
    local_path = "./tmp/"+message["request_id"]+"_"+str(randint(1000,9999))
    blob_path = "Blob_"+datetime.today().strftime("%d_%m_%Y")
    blob_storage_path = blob_path + "/" + str(message["request_id"])+"/fileblock_" + str(message["sequence_num"]) + ".csv"
    data_frame.to_csv(local_path, index_label=False,encoding="utf-8")
    # Blob upload logic should stay here not another func:
    try:
        connect_str = conf.AZURE_STORAGE_CONNECTION_STRING
        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        container_name = "container" + datetime.today().strftime("%m%Y")
        container_list = blob_service_client.list_containers()
        existing_containers = []
        for container in container_list:
             existing_containers.append(container.name)

        if container_name not in existing_containers:
            container_client = blob_service_client.create_container(container_name)
        blob_client = blob_service_client.get_blob_client(container=container_name,blob=blob_storage_path)

        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

            print("Finished uploading blob")

        os.remove(local_path)

    except Exception as ex:
        print('Exception:')
        print(ex)

if __name__ == '__main__':
    wait_time = 1
    while True:
        queue_empty = read_queue()
        wait_time = 5 if queue_empty else 1
        print("Waiting backoff: " + str(wait_time) + " seconds...")
        time.sleep(wait_time)