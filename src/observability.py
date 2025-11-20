# src/observability.py
import logging
from time import time


logger = logging.getLogger("rural-ed-agent")
logger.setLevel(logging.INFO)




def timed(fn):
def wrapper(*args, **kwargs):
t0 = time()
res = fn(*args, **kwargs)
dt = time() - t0
logger.info(f"Function {fn.__name__} took {dt:.3f}s")
return res
return wrap