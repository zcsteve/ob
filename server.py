import asyncio
from concurrent import futures
from dataclasses import dataclass

import grpc

import fed_messages_pb2 as fed_msg
import md_pb2 as md
import md_pb2_grpc as md_grpc
from deribit import DeribitOB


@dataclass(slots=True)
class Book:
    exchange: fed_msg.Exchange
    symbol: str
    tob: md.TOB
    

    


class MDServicer(md_grpc.MDServicer):
    async def __init__(self):
        self.subscribed_symbols = {}
        self.tob_queue = asyncio.Queue()
        self.deribit_ob = DeribitOB(self.tob_queue)
        t1 = asyncio.create_task(
            self.deribit_ob.subscribe_order_book(["BTC-PERPETUAL", "ETH-PERPETUAL"])
        )
        asyncio.gather(t1)

    async def StreamTOB(self, request, context):
        exchange = request.exchange
        symbol = request.symbol
        while True:
            tob = await self.tob_queue.get()
            yield tob


async def serve():
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    md_grpc.add_MDServicer_to_server(MDServicer(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())
