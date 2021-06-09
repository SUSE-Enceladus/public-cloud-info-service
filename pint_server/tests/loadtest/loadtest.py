from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import argparse
import random
import requests
import sys
import time

'''
To run this program, 
python loadtest.py --help displays the options the program takes
If you do not provide any options, there are default values for the options
python loadtest.py --num_requests 100 --duration 1 --url http://localhost:5000   
Here the duration is in minutes
'''

urls_to_hit = ["/v1/providers",
               "/v1/amazon/images", "/v1/amazon/servers",
               "/v1/google/images", "/v1/google/servers",
               "/v1/oracle/images", "/v1/oracle/servers",
               "/v1/microsoft/images", "/v1/microsoft/servers",
               "/v1/amazon/regions",
               "/v1/amazon/us-east-2/images",
               "/v1/microsoft/regions",
               "/v1/providers.xml",
               "/v1/alibaba/images.xml"]

time_buckets = {}

def task(base_url):
    url = base_url + random.choice(urls_to_hit)
    print("Hitting the endpoint", url)
    resp = requests.get(url, verify=False)
    if resp.status_code != 500:
        print("Response OK", resp.status_code)
    else:
        print("Response Not OK", resp.status_code)
    increment_time_bucket(resp.elapsed.total_seconds())
    #print("Task Executed {}".format(threading.current_thread()))

def increment_time_bucket(seconds):
    index = int(seconds // 0.5)
    if index in time_buckets.keys():
      time_buckets[index] += 1
    else:
      time_buckets[index] = 1

def print_time_buckets():
    total_count = 0
    print("========== response time histogram (seconds) ==========")
    for key in sorted (time_buckets.keys()) :
      timeStart = key * 0.5
      timeEnd = (key + 1) * 0.5
      print("Bucket: ", timeStart , " - ", timeEnd, " seconds : " , time_buckets[key], " requests")
      total_count = total_count + time_buckets[key]
    print("Total Count of Requests handled: ", total_count)


def main(argv):
    #handle command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--num_requests',
                        required=False,
                        type=int,
                        default=100,
                        dest="num_requests",
                        help="Number of requests to hit the API")
    parser.add_argument('-d', '--duration',
                        required=False,
                        type=int,
                        default=1,
                        dest="duration",
                        help="Duration in minutes")
    parser.add_argument('-u', '--url',
                        required=False,
                        type=str,
                        default="http://localhost:5000",
                        dest="base_url",
                        help="base url for the service")
    args = parser.parse_args()
    duration = args.duration
    num_requests = args.num_requests
    base_url = args.base_url


    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration)
    executor = ThreadPoolExecutor(max_workers=100)
    num_chunks = 0
    min_chunks = 5
    ''' 
    Dividing the number of requests into chunks so the requests can be
    spaced out evenly over the duration. In each chunk of time, fire
    the allocated number of requests for that chunk into the thread pool 
    to execute.
    '''
    chunks = num_requests/duration
    if (chunks < min_chunks):
        chunks = min_chunks
    while (num_chunks < chunks):
        num_requests_in_chunk_counter=0
        while (num_requests_in_chunk_counter < num_requests / chunks and datetime.now() < end_time):
            num_requests_in_chunk_counter = num_requests_in_chunk_counter + 1
            executor.submit(task(base_url))
        while (datetime.now() < (start_time + timedelta(minutes=(duration/chunks)*num_chunks))):
            time.sleep(1)
        num_chunks = num_chunks + 1
    print_time_buckets()


if __name__ == '__main__':
    main(sys.argv[1:])

