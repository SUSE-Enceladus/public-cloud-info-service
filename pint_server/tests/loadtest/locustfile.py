import random
from locust import HttpUser, task

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

class PintLoadTest(HttpUser):
    @task
    def test(self):
        self.client.get(random.choice(urls_to_hit))
