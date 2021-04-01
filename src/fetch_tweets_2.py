import time
import datetime
import requests
import sys
import json
import csv
import pandas as pd
from azure.servicebus import ServiceBusClient, ServiceBusMessage
import resources.azure_messaging_config as conf
import random
class TweetLoader:
    def __init__(self):
        self.start_date = None
        self.end_date = None
        self.token = None
        self.num_results = None
        self.search_query = None
        self.partition_size = None

    def load_auth_details(self, key_file):
        with open(key_file) as f:
            key_dict = json.load(f)
            self.token = key_dict["bearer_token"]

    # Loading and validating API request parameters
    def load_params(self, config_file):
        validity_check = True
        with open(config_file) as f:
            config_dict = json.load(f)
            self.start_date = config_dict.get("start_date", None)
            self.end_date = config_dict.get("end_date", None)
            self.num_results = config_dict.get("num_results")
            self.search_query = config_dict.get("search_query")
            self.partition_size = config_dict.get("partition_size", 1000)
        if self.start_date:
            try:
                self.start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d')
            except ValueError:
                print("Incorrect start date format should be YYYY-MM-DD")
                validity_check = False

        if self.end_date:
            try:
                self.end_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d')
            except ValueError:
                print("Incorrect end date format should be YYYY-MM-DD")
                validity_check = False
            current_date = datetime.datetime.now()
            if self.start_date > current_date:
                print("Start date cannot be greater than current date")
                validity_check = False

        if not self.search_query:
            print("Please enter search query to fetch data")
            validity_check = False

        if not self.num_results:
            self.num_results = 10

        if validity_check:
            self.fetch_tweets()

    def fetch_tweets(self):
        counter = 0
        total_results = 0
        next_token = None
        start_time = None
        end_time = None
        validate_response = True
        result = self.num_results
        response = {
            "data": [],
            "meta": [],
            "includes": {
                "users": [],
                "media": [],
                "tweets": [],
            }
        }

        if self.num_results > 500:
            result = 500

        while total_results < self.num_results:
            counter = counter + 1
            time.sleep(2)

            if self.start_date:
                start_time = self.start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            if self.end_date:
                end_time = self.end_date.strftime('%Y-%m-%dT%H:%M:%SZ')

            params = {
                # query must not be greater than 1024 characters FYI
                "query": self.search_query,

                # time box to these times, exclusive (ISO8601, "YYYY-MM-DDTHH:mm:ssZ")
                # example timestamp: "2020-01-01T00:00:00Z"
                "start_time": start_time,
                "end_time": end_time,

                # limit to ten results (minimum 10, maximum 500)
                # this limit is exclusive (i.e. 10 gets you 9)
                "max_results": result,

                # "expand" every field possible. this takes id numbers that appear in a
                # tweet and turns them in actual readable text.
                "expansions": "author_id,referenced_tweets.id,in_reply_to_user_id,attachments.media_keys,attachments.poll_ids,geo.place_id,entities.mentions.username,referenced_tweets.id.author_id",

                # fill out these fields
                "user.fields": "created_at,description,entities,id,location,name,protected,public_metrics,url,username,verified,withheld",
                "tweet.fields": "attachments,author_id,context_annotations,conversation_id,created_at,entities,geo,id,in_reply_to_user_id,lang,public_metrics,possibly_sensitive,referenced_tweets,source,text,withheld",
                "place.fields": "contained_within,country,country_code,full_name,geo,id,name,place_type",

                # how to paginate!
                "next_token": next_token,
            }

            headers = {
                "Authorization": "Bearer {}".format(self.token),
            }

            r = requests.get(
                "https://api.twitter.com/2/tweets/search/all",
                params=params,
                headers=headers,
            )
            try:
                r.raise_for_status()
                response["data"].extend(r.json()["data"])
                response["includes"]["users"].extend(r.json()["includes"]["users"])
                response["includes"]["media"].extend(
                    r.json()["includes"]["media"] if "media" in r.json()["includes"].keys() else [])
                response["includes"]["tweets"].extend(r.json()["includes"]["tweets"])
                response["meta"].extend(r.json()["meta"])
                results_fetched = int(r.json()["meta"]["result_count"])
                total_results = total_results + results_fetched
                result = self.num_results - total_results
                if result >= 500:
                    result = 500
                    next_token = r.json()["meta"]["next_token"]
                else:
                    result = ((result // 10) + 1) * 10
            except requests.RequestException as e:
                # print error message if response codes in 4xx and stop execution, else continue to retry
                if r.status_code >= 400 and r.status_code < 500:
                    print(r.text)
                    self.message_list.append(r.text)
                    validate_response = False
                    break
        if validate_response:
            data_rows = self.parse_data(response)
            self.partition_rows(data_rows)

    def parse_data(self, response):
        linked_tweets = {}
        users = {}
        media_map = {}
        data_rows = []
        tweets_map = {}
        for user in response["includes"]["users"]:
            user_id = user["id"]
            users[user_id] = user
        for tweet in response["includes"]["tweets"]:
            tweet_id = tweet["id"]
            linked_tweets[tweet_id] = tweet
        for media in response["includes"]["media"]:
            media_id = media["media_key"]
            media_map[media_id] = {
                "media_key": media_id,
                "type": media["type"]}
        for tweet in response["data"] + list(linked_tweets.values()):
            tweets_map = {}
            author = users.get(tweet["author_id"])
            media_list = []
            for media_key in tweet.get("attachments", {}).get("media_keys", []):
                if media_map.get(media_key, {}):
                    media_list.append(media_map.get(media_key, {}))
            tweets_map["id"] = tweet["id"]
            tweets_map["conversation_id"] = tweet["conversation_id"]
            tweets_map["created_at"] = tweet["created_at"]
            tweets_map["tweet"] = tweet["text"]
            tweets_map["source"] = tweet["source"]
            tweets_map["language"] = tweet["lang"]
            tweets_map["in_reply_to_user_id"] = tweet.get("in_reply_to_user_id", None)
            tweets_map["hashtags"] = [x["tag"] for x in tweet.get("entities", {}).get("hashtags", [])]
            tweets_map["urls"] = [x["expanded_url"] for x in tweet.get("entities", {}).get("urls", [])]
            tweets_map["media"] = [[media['media_key'], media["type"]] for media in media_list]
            tweets_map["retweet_count"] = tweet["public_metrics"]["retweet_count"]
            tweets_map["reply_count"] = tweet["public_metrics"]["reply_count"]
            tweets_map["like_count"] = tweet["public_metrics"]["like_count"]
            tweets_map["quote_count"] = tweet["public_metrics"]["quote_count"]
            tweets_map["user_id"] = tweet["author_id"]
            tweets_map["user_screen_name"] = author["username"]
            tweets_map["user_name"] = author["name"]
            tweets_map["user_description"] = author["description"]
            tweets_map["user_location"] = author.get("location")
            tweets_map["user_created_at"] = author["created_at"]
            tweets_map["user_followers_count"] = author["public_metrics"]["followers_count"]
            tweets_map["user_friends_count"] = author["public_metrics"]["following_count"]
            tweets_map["user_statuses_count"] = author["public_metrics"]["tweet_count"]
            tweets_map["user_verified"] = author["verified"]
            if tweet.get("referenced_tweets"):
                reference_list = []
                for ref in tweet.get("referenced_tweets"):
                    reference_list.append(json.dumps(ref))
            tweets_map["references"] = reference_list if tweet.get("referenced_tweets") else None
            reference_list = []
            data_rows.append(tweets_map)
        return data_rows

    def send_rows(self, sender, message, request_id, last_partition, sequence_num):
        data_packet = {}
        data_packet["data"] = message
        data_packet["request_id"] = request_id
        data_packet["last_partition"] = last_partition
        data_packet["sequence_num"] = sequence_num
        serialized_msg = ServiceBusMessage(json.dumps(data_packet))
        sender.send_messages(serialized_msg)

    def partition_rows(self, data_rows):
        #print(len(data_rows))
        request_id = "request_" + str(random.randint(1000,9999))
        print("creating partitions of size " + str(self.partition_size))
        if len(data_rows) < self.partition_size:
            try:
                servicebus_client = ServiceBusClient.from_connection_string(conn_str=conf.CONNECTION_STR,
                                                                            logging_enable=True)
                with servicebus_client:
                    # get a Queue Sender object to send messages to the queue
                    sender = servicebus_client.get_queue_sender(queue_name=conf.QUEUE_NAME)
                    with sender:
                        # send one message
                        self.send_rows(sender, data_rows, request_id, True)

            except Exception as e:
                print(e)

        else:
            servicebus_client = ServiceBusClient.from_connection_string(conn_str=conf.CONNECTION_STR,
                                                                        logging_enable=True)
            sender = servicebus_client.get_queue_sender(queue_name=conf.QUEUE_NAME)
            with servicebus_client:
                with sender:
                    for c, i in enumerate(range(0, len(data_rows), self.partition_size)):
                        try:
                            print("Sending msg packet: " + str(c+1))
                            last_partition = False if (i+self.partition_size) < len(data_rows)-1 else True
                            self.send_rows(sender, data_rows[i:min(i + self.partition_size, len(data_rows))], request_id, last_partition, c)
                        except Exception as e:
                            print(e)



    # def partition_rows(self, data_rows):
    #     request_id_dummy = "request1"
    #     if (len(data_rows)<=self.partition_size):
    #         dataset = pd.DataFrame(data_rows)
    #         dataset.to_csv(request_id_dummy + ".csv", index=False, encoding='utf-8')
    #     else:
    #         for c, i in enumerate(range(0, len(data_rows), self.partition_size)):
    #             dataset = pd.DataFrame(data_rows[i:min(i + self.partition_size, len(data_rows))])
    #             dataset.to_csv(request_id_dummy + "_" + str(c) + ".csv", index=False, encoding='utf-8')






if __name__ == '__main__':
    tweet_object = TweetLoader()
    tweet_object.load_auth_details('resources\keys.json')
    tweet_object.load_params('resources\config.json')
