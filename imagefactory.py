import os, io
from PIL import Image

img_cache_path = "./img_cache"

if not os.path.exists(img_cache_path):
    os.mkdir(img_cache_path)
