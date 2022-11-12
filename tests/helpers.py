import uuid
import json
import redis
import requests
from allocation import config


class _RandomRefs:
    def random_suffix(self):
        return uuid.uuid4().hex[:6]


    def random_sku(self, name=""):
        return f"sku-{name}-{self.random_suffix()}"


    def random_batchref(self,name=""):
        return f"batch-{name}-{self.random_suffix()}"


    def random_orderid(self,name=""):
        return f"order-{name}-{self.random_suffix()}"


class _APIClient:
    def post_to_add_batch(self, ref, sku, qty, eta):
        url = config.get_api_url()
        r = requests.post(
            f"{url}/add_batch", json={"ref": ref, "sku": sku, "qty": qty, "eta": eta}
        )
        assert r.status_code == 201

    def post_to_allocate(self, orderid, sku, qty, expect_success=True):
        url = config.get_api_url()
        r = requests.post(
            f"{url}/allocate",
            json={
                "orderid": orderid,
                "sku": sku,
                "qty": qty,
            },
        )
        if expect_success:
            assert r.status_code == 201
        return


r = redis.Redis(**config.get_redis_host_and_port())

class _RedisClient:
    def subscribe_to(self, channel):
        pubsub = r.pubsub()
        pubsub.subscribe(channel)
        confirmation = pubsub.get_message(timeout=3)
        assert confirmation["type"] == "subscribe"
        return pubsub

    def publish_message(self, channel, message):
        r.publish(channel, json.dumps(message))


random_refs = _RandomRefs()
api_client = _APIClient()
redis_client = _RedisClient()