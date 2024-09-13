import asyncio
import json
from dataclasses import dataclass
from typing import List

import websockets

from fed_messages_pb2 import Exchange
from md_pb2 import TOB


@dataclass(slots=True)
class DeribitOB:
    tob_queue: asyncio.Queue[TOB]

    async def subscribe_order_book(self, symbols: List[str]):
        async with websockets.connect("wss://www.deribit.com/ws/api/v2") as websocket:
            # Subscribe to the order book for the specified symbol
            subscribe_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "public/subscribe",
                "params": {
                    "channels": [f"book.{symbol}.none.10.100ms" for symbol in symbols]
                },
            }
            await websocket.send(json.dumps(subscribe_message))
            # Process incoming messages
            async for message in websocket:
                response = json.loads(message)
                # print(response)
                if "params" in response:
                    tob = TOB(
                        a=response["params"]["data"]["asks"][0][0],
                        b=response["params"]["data"]["bids"][0][0],
                        A=response["params"]["data"]["asks"][0][0],
                        B=response["params"]["data"]["asks"][0][0],
                        ts=response["params"]["data"]["timestamp"],
                        symbol=response["params"]["data"]["instrument_name"],
                        exchange=Exchange.DBT,
                    )
                    await self.tob_queue.put(tob)


async def tester():
    symbols = ["BTC-PERPETUAL", "ETH-PERPETUAL"]
    order_queue: asyncio.Queue[TOB] = asyncio.Queue()
    db = DeribitOB(order_queue)
    tob_queue = db.tob_queue

    t1 = asyncio.create_task(db.subscribe_order_book(symbols))
    while True:
        tob = await tob_queue.get()
        print(tob)


if __name__ == "__main__":
    asyncio.run(tester())
