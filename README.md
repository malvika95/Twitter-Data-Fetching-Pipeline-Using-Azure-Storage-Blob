# Twitter-Data-Fetching-Pipeline-Using-Azure-Blob-Storage

## Overview
This project is a scalable data pipeline that extracts tweets for a user defined hashtag and uploads data to Azure Blob Storage in a csv format.  
The pipeline is divided into two modules, a **sender** that extracts tweets based on a particular hashtag and a **receiever** that recieves the data and uploads it to 
a Blob Storage. The two modules are connected through a *service bus* queue to prevent request timeouts and ensure independent scalability of the two modules. 
Project Website : https://prathameshmahankal.github.io/tracking-online-disinformation/  


## Installation
### Prerequistes
Before getting started with implementing this pipeline, make sure you have access to the following tools :
* Bearer token to access Twitter's full archive search API (version 2) to fetch tweets.
You can use the the following link to generate and use Bearer tokens :
https://developer.twitter.com/en/docs/authentication/oauth-2-0/bearer-tokens  
The Script makes use of the bearer token in the keys.json file [here](https://github.com/malvika95/Twitter-Data-Fetching-Pipeline/blob/master/fetch_tweets/sender_module/app/main/service/resources/keys.json)

* A valid Microsoft Azure subscription to use resources such as Azure Blob Storage and Azure Service Bus.  
**Service Bus**:  
You can use the following link to create a Service Bus Queue on your Azure Portal and access your queue connection strings:      
https://docs.microsoft.com/en-us/azure/service-bus-messaging/service-bus-quickstart-portal  
Once you have created a queue on azure service bus, fill in your primary connection string [here](https://github.com/malvika95/Twitter-Data-Fetching-Pipeline/blob/master/fetch_tweets/sender_module/app/main/service/resources/azure_messaging_config.py)
and [here](https://github.com/malvika95/Twitter-Data-Fetching-Pipeline/blob/master/receiver/receiver_module/src/resources/azure_messaging_config.py) in the field *CONNECTION_STR* and your queue name in the field *QUEUE_NAME*    
**Azure Blob Storage**:  
You can use the following link to create an Azure Storage Account on Your Azure Portal :
https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create?toc=%2Fazure%2Fstorage%2Fblobs%2Ftoc.json&tabs=azure-portal  
Once you have created your Azure Storage Account you can find your connection string [here](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)
(Copy your credentials from the Azure portal). Add your connection string [here](https://github.com/malvika95/Twitter-Data-Fetching-Pipeline/blob/master/receiver/receiver_module/src/resources/azure_messaging_config.py)
under the *AZURE_STORAGE_CONNECTION_STRING* parameter.

* Install all the libraries in <code>requirements.txt</code> using the following command :  
Navigate into the <code>fetch_tweets/sender_module</code> folder and run the command :  
<code>pip install -r requirements.txt</code>  
Similarly install all the requirements within the <code>/receiver/receiver_module</code> folder.  

### Configurations 
The config.json present [here](https://github.com/malvika95/Twitter-Data-Fetching-Pipeline/blob/master/fetch_tweets/sender_module/app/main/service/resources/config.json) can
be used to configure the following parameters to fetch tweets :
* num_results - The total number of tweets to be collected for a given hashtag
* start_date - Collect tweets posted from the given start date
* end_date - Collect tweets posted till the given end date

## Running Code

**Local execution**  
Since the code makes consists of two modules a sender and a receiver, that are connected through a service bus, the receiver needs to be run continuously
in the background to recieve tweets for different user requests from the sender and upload the same to the blob storage.  
**Note : Configuration changes should be made before executing the code**  

### Executing the Receiver Module  
To execute the receiever module, navigate to the <code>/receiver/receiver_module/src/</code> folder and run the following command :  
<code>python -u receiver.py</code>  

The code will then be listening on the service bus queue for requests from the sender.

### Executing the Sender Module  
The sender module is created as a lightweight flask application to ensure that it can be called by any application by triggering the flask endpoint and passing a hashtag of
interest. To start the flask application, navigate to the <code>fetch_tweets\sender_module</code> folder and execute the following command:  
<code>python -u manage.py run </code>  

The flask application will be running on localhost and will specify the endpoint the flask application is running on. You can click on the endpoint or paste the same
in your browser to view the swagger UI to trigger the sender module to fetch tweets by clicking the **try it out** button in the UI and passing your hashtag of interest.  
The endpoint can also be triggered using an IDE such as postman by calling the endpoint as <code>http://localhost:port_number/search/</code> and passing the hashtag
in the request body in a json format such as :  
<code>
{
    "hashtag": "#YourHastagOfInterest
}
</code>  

Once you have triggered the endpoint you shall see a "success" message as a response indicating your request has been processed successfully. You can then navigate to your
azure blob storage account and view the data uploaded.  
**Note - Ensure your receiver module is running background before triggering the sender module or the data will be piled up in the queue and not be uploaded to the Blob storage**  


## Deployment with Docker  
Both the sender and receiver modules can be deployed as images on Docker that can be subsequently pushed on **Azure Container Instance** to run on the Cloud. To build the docker image of the two modules, navigate to the docker file path for each of the modules (the docker file for the sender module can be found under <code>fetch_tweets/Dockerfile</code>
and for the receiever module under <code>receiver/Dockerfile</code> and run the [docker build](https://docs.docker.com/engine/reference/commandline/build/) command.










