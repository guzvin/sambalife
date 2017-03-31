"""
ASGI config for sambalife project.

It exposes the ASGI callable as a module-level variable named ``channel_layer``.

For more information on this file, see
https://channels.readthedocs.io/en/stable/deploying.html
"""

import os

from channels.asgi import get_channel_layer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sambalife.settings")

channel_layer = get_channel_layer()
