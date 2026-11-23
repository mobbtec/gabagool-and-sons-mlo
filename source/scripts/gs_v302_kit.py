"""LONG PIG 3.0.2 – retail layout, protective trim and local wall wear."""
import gs_v300_kit as base
from gs_v300_kit import *
import gs_v302_shelf as shelf
import gs_v302_finish as finish

VERSION = '3.0.2'
shelf.install()
finish.arrange_wear(base)
base_market = base.market_faces


def market_faces():
    faces = list(base_market())
    return finish.finish_market(faces, base)


EXTRA_HALL_DRAWABLES = (('gs_v26_market',market_faces,base._market_specs),)

# All of these hand-sized goods use the interior's existing 25 m small-prop
# distance. The cases, signs and standing fixtures retain their own draw ranges.
RETAIL_SMALL = set(base.CIGS) | set(base.CHIPS) | set(base.CANDY)
