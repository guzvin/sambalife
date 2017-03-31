#!/usr/bin/env python
from channels.routing import route
from websocket.consumer import ws_message

channel_routing = [
    route('websocket.receive', ws_message)
]