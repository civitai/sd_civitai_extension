# from blake3 import blake3 as hasher
import os.path

from modules import hashes as sd_hashes

# NOTE: About this file
# ---------------------------------
# This is not being used. It was added to see if Blake3 was faster than SHA256.
# It was not noticeably faster in our tests, so we are sticking with SHA256 for now.
# Especially since SHA256 is the standard inside this UI.

# cache_key = "civitai_hashes"

# def blake3_from_cache(filename, title):
#     hashes = sd_hashes.cache(cache_key)
#     ondisk_mtime = os.path.getmtime(filename)

#     if title not in hashes:
#         return None

#     cached_blake3 = hashes[title].get("blake3", None)
#     cached_mtime = hashes[title].get("mtime", 0)

#     if ondisk_mtime > cached_mtime or cached_blake3 is None:
#         return None

#     return cached_blake3

# def calculate_blake3(filename):
#     hash_blake3 = hasher()
#     blksize = 1024 * 1024

#     with open(filename, "rb") as f:
#         for chunk in iter(lambda: f.read(blksize), b""):
#             hash_blake3.update(chunk)

#     return hash_blake3.hexdigest()

# def blake3(filename, title):
#     hashes = sd_hashes.cache(cache_key)

#     blake3_value = blake3_from_cache(filename, title)
#     if blake3_value is not None:
#         return blake3_value

#     print(f"Calculating blake3 for {filename}: ", end='')
#     blake3_value = calculate_blake3(filename)
#     print(f"{blake3_value}")

#     if title not in hashes:
#         hashes[title] = {}

#     hashes[title]["mtime"] = os.path.getmtime(filename)
#     hashes[title]["blake3"] = blake3_value

#     sd_hashes.dump_cache()

#     return blake3_value
