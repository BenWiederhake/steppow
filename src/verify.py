#!/usr/bin/env python3

import sys

from hashlib import sha256
from math import ceil, log2
from struct import Struct

TEST_CERTS = [
    (b'\x01' * 32, b'\x02' * 8, 8, 8, 1,  # Just for debugging x1
     b'\x00\xF7', 780, True),
    (b'\x01' * 32, b'\x02' * 8, 8, 8, 1,  # Just for debugging x1
     b'\x03\x0B', 780, True),
    (b'\x01' * 32, b'\x02' * 8, 8, 8, 20,  # Just for debugging x20
     b'\x03\x0B\x00\x7F\x00\x54\x01\x81\x00\x2E\x01\xFE\x00\x96\x00\x6A\x00\xBC\x01\x37\x00\x37\x00\x6A\x00\x34\x03\x92\x00\x4A\x00\x1C\x00\x3F\x01\xC4\x00\xFD\x00\x38', 4759, True),
     
    (b'\x00' * 32, b'\x00' * 8, 7, 7, 800,  # Basic sanity checks
     b'\xFF' * 10, -1, False),
    (b'\x00' * 32, b'\x00' * 8, 7, 7, 800,
     b'\xFF' * 1400, -1, False),
    (b'\x00' * 32, b'\x00' * 8, 7, 7, 33,
     b'\xFF' * 58, -1, False),
    (b'\x00' * 32, b'\x00' * 8, 7, 7, 33,  # First actual certificate
     b'\x02\x98\x07\xA0\x5C\x80\xC9\x02\x40\x02\xD0\x14\x00\x35\x00\xAC\x02\x00\x15\x40\x0C\x01\x50\x04\x00\x14\x00\xCB\x00\xBC\x06\x50\x2A\x40\x63\x00\x6C\x01\x50\x04\x40\x42\x03\x2C\x04\x40\x23\x00\x2E\x01\x54\x03\x60\x00\x80\x2E\x00\xD4', 3061, True),
    (b'\x01' * 32, b'\x00' * 8, 7, 7, 33,  # Differet inithash
     b'\x02\x98\x07\xA0\x5C\x80\xC9\x02\x40\x02\xD0\x14\x00\x35\x00\xAC\x02\x00\x15\x40\x0C\x01\x50\x04\x00\x14\x00\xCB\x00\xBC\x06\x50\x2A\x40\x63\x00\x6C\x01\x50\x04\x40\x42\x03\x2C\x04\x40\x23\x00\x2E\x01\x54\x03\x60\x00\x80\x2E\x00\xD4', -1, False),
    (b'\x00' * 32, b'\x01' * 8, 7, 7, 33,  # Differet token
     b'\x02\x98\x07\xA0\x5C\x80\xC9\x02\x40\x02\xD0\x14\x00\x35\x00\xAC\x02\x00\x15\x40\x0C\x01\x50\x04\x00\x14\x00\xCB\x00\xBC\x06\x50\x2A\x40\x63\x00\x6C\x01\x50\x04\x40\x42\x03\x2C\x04\x40\x23\x00\x2E\x01\x54\x03\x60\x00\x80\x2E\x00\xD4', -1, False),
    (b'\x00' * 32, b'\x00' * 8, 7, 7, 33,  # Certificate is slightly off
     b'\x02\x98\x07\xA0\x5C\x80\xC9\x02\x40\x02\xD0\x14\x00\x35\x00\xAC\x02\x00\x15\x40\x0C\x01\x50\x04\x00\x14\x00\xCB\x00\xBC\x06\x50\x2A\x40\x63\x00\x6C\x01\x50\x04\x40\x42\x03\x2C\x04\x40\x22\x00\x2E\x01\x54\x03\x60\x00\x80\x2E\x00\xD4', -1, False),
    (b'\x00' * 32, b'\x00' * 8, 7, 7, 33,  # Certificate's padding is wrong
     b'\x02\x98\x07\xA0\x5C\x80\xC9\x02\x40\x02\xD0\x14\x00\x35\x00\xAC\x02\x00\x15\x40\x0C\x01\x50\x04\x00\x14\x00\xCB\x00\xBC\x06\x50\x2A\x40\x63\x00\x6C\x01\x50\x04\x40\x42\x03\x2C\x04\x40\x23\x00\x2E\x01\x54\x03\x60\x00\x80\x2E\x00\xD5', -1, False),
    (b'\x5A' * 32, b'\x5A' * 8, 8, 7, 100,  # First "hard" certificate
     b'\x05\x92\x00\xBC\x07\xE0\x0F\xC0\x59\xA0\x0C\x00\x03\x00\x13\x00\xEE\x00\x30\x0E\x58\x0C\x50\x07\x00\x84\x40\x54\x00\x85\x01\xCC\x00\x18\x03\xF8\x15\x50\x03\x60\x2C\x40\x30\x00\x69\x00\x02\x01\xD4\x0E\x00\x15\xE0\x03\xA0\x1B\x80\xB1\x80\xA4\x00\x2C\x04\x38\x10\xE8\x1C\x10\x13\x80\x74\xC0\x55\x00\x5C\x01\x1A\x03\x08\x05\xF0\x01\x00\x29\xC0\x50\x00\xA2\x82\x15\x05\x5E\x07\xA0\x01\x40\x04\xD0\x18\x40\x63\x40\xC6\x80\xDC\x00\x90\x00\xFC\x04\x20\x19\x40\x17\x80\x3A\x00\x6C\x00\xBC\x00\xE8\x01\x18\x13\xA8\x01\x60\x0A\xA0\x11\x01\x46\x00\x7B\x00\x36\x00\x50\x02\x50\x15\xF0\x03\x20\x8D\xC0\x18\x80\xE2\x00\x06\x03\x84\x12\xE8\x1B\x90\x19\x60\x29\x01\xD1\x02\x67\x00\x6A\x02\x8C\x02\xE8\x24\x80\x18\x40\x08\x80\x6F\x80\xB2\x02\x14\x00\x8C\x08\xC8\x07\xD0', 23244, True),
    (b'\x0F' * 32, b'Hi mate!', 12, 7, 122,  # Another "hard" certificate
     b'\x00\x6F\x80\x01\x3C\x03\x34\x82\xD9\x60\x38\x18\x02\xAB\x40\x05\xE0\x38\x48\x03\x6C\xC0\x02\xBC\x0D\x65\x00\xE9\xF0\x02\x98\x02\xE5\x00\xDB\xA0\x1A\x4B\x02\x60\x00\xA1\x1C\x04\x24\x01\x2F\x00\x12\xCA\x06\x94\x00\xEF\x28\x18\x2B\x01\x13\xC0\x38\xA0\x02\x1C\x00\xDB\x70\x00\x26\x09\xD7\xC0\x7A\x40\x08\x9F\x00\x5E\xA0\x94\xB8\x06\xD2\x02\x1C\xC0\x19\x84\x0F\xA2\x01\x26\x38\x20\x81\x00\x40\x80\x0D\x7C\x05\xA1\x82\x3E\xF0\x2F\x94\x03\x7C\x80\x9F\xD8\x12\x93\x02\xB2\xC0\x32\x30\x01\xCD\x01\x24\x50\x3D\x44\x05\xDB\x40\x3C\x10\x0A\x3B\x01\xA8\x40\x5F\x14\x00\xC6\x00\xFE\x20\x5F\x34\x0A\x07\xC0\x0F\x18\x1C\xAA\x00\x97\x00\x38\x24\x0E\xF5\x80\xF5\xF0\x3E\x28\x07\x6F\xC3\xD6\x60\x00\x29\x02\x61\xA0\x30\xCC\x1B\xE3\x80\x3A\xA0\x06\xE0\x00\x1E\x40\x52\xB8\x2C\x90\x00\x3C\x40\x49\xF0\x16\x01\x00\x1D\xD0\x03\x04\x04\xB9\x40\x41\x90\x0B\x04\x06\x31\x80\x01\x9C\x10\xDE\x01\x9E\x70\x0F\x2A\x01\x9F\xC0\x1C\xD0\x3E\xDE\x01\xB0\x00\x0C\x10\x05\x13\x81\x78\x20\x1B\x86\x03\x6E\x40\x0E\x48\x1C\x42\x03\xC8\xC0\x85\xBC\x07\xD1\x01\x9C\x50\xB7\xF6\x00\x3D\x80\x0C\x18\x0D\x9D\x06\x0C\xA0\x0B\xE4\x03\x0C\x00\x63\xF0\x16\xEE\x01\x1E\x40\x63\xA8\x00\xF8\x00\x07\x60\x06\x88', 598812, True),
    (b'\x0F' * 32, b'Hi mate?', 12, 7, 122,  # Token is off
      b'\x00\x6F\x80\x01\x3C\x03\x34\x82\xD9\x60\x38\x18\x02\xAB\x40\x05\xE0\x38\x48\x03\x6C\xC0\x02\xBC\x0D\x65\x00\xE9\xF0\x02\x98\x02\xE5\x00\xDB\xA0\x1A\x4B\x02\x60\x00\xA1\x1C\x04\x24\x01\x2F\x00\x12\xCA\x06\x94\x00\xEF\x28\x18\x2B\x01\x13\xC0\x38\xA0\x02\x1C\x00\xDB\x70\x00\x26\x09\xD7\xC0\x7A\x40\x08\x9F\x00\x5E\xA0\x94\xB8\x06\xD2\x02\x1C\xC0\x19\x84\x0F\xA2\x01\x26\x38\x20\x81\x00\x40\x80\x0D\x7C\x05\xA1\x82\x3E\xF0\x2F\x94\x03\x7C\x80\x9F\xD8\x12\x93\x02\xB2\xC0\x32\x30\x01\xCD\x01\x24\x50\x3D\x44\x05\xDB\x40\x3C\x10\x0A\x3B\x01\xA8\x40\x5F\x14\x00\xC6\x00\xFE\x20\x5F\x34\x0A\x07\xC0\x0F\x18\x1C\xAA\x00\x97\x00\x38\x24\x0E\xF5\x80\xF5\xF0\x3E\x28\x07\x6F\xC3\xD6\x60\x00\x29\x02\x61\xA0\x30\xCC\x1B\xE3\x80\x3A\xA0\x06\xE0\x00\x1E\x40\x52\xB8\x2C\x90\x00\x3C\x40\x49\xF0\x16\x01\x00\x1D\xD0\x03\x04\x04\xB9\x40\x41\x90\x0B\x04\x06\x31\x80\x01\x9C\x10\xDE\x01\x9E\x70\x0F\x2A\x01\x9F\xC0\x1C\xD0\x3E\xDE\x01\xB0\x00\x0C\x10\x05\x13\x81\x78\x20\x1B\x86\x03\x6E\x40\x0E\x48\x1C\x42\x03\xC8\xC0\x85\xBC\x07\xD1\x01\x9C\x50\xB7\xF6\x00\x3D\x80\x0C\x18\x0D\x9D\x06\x0C\xA0\x0B\xE4\x03\x0C\x00\x63\xF0\x16\xEE\x01\x1E\x40\x63\xA8\x00\xF8\x00\x07\x60\x06\x88', -1, False),
    (b'\x0F' * 32, b'Hi mate!', 11, 8, 122,  # This is the previous "12,7" certificate!  Observe that less work is proven.
      b'\x00\x6F\x80\x01\x3C\x03\x34\x82\xD9\x60\x38\x18\x02\xAB\x40\x05\xE0\x38\x48\x03\x6C\xC0\x02\xBC\x0D\x65\x00\xE9\xF0\x02\x98\x02\xE5\x00\xDB\xA0\x1A\x4B\x02\x60\x00\xA1\x1C\x04\x24\x01\x2F\x00\x12\xCA\x06\x94\x00\xEF\x28\x18\x2B\x01\x13\xC0\x38\xA0\x02\x1C\x00\xDB\x70\x00\x26\x09\xD7\xC0\x7A\x40\x08\x9F\x00\x5E\xA0\x94\xB8\x06\xD2\x02\x1C\xC0\x19\x84\x0F\xA2\x01\x26\x38\x20\x81\x00\x40\x80\x0D\x7C\x05\xA1\x82\x3E\xF0\x2F\x94\x03\x7C\x80\x9F\xD8\x12\x93\x02\xB2\xC0\x32\x30\x01\xCD\x01\x24\x50\x3D\x44\x05\xDB\x40\x3C\x10\x0A\x3B\x01\xA8\x40\x5F\x14\x00\xC6\x00\xFE\x20\x5F\x34\x0A\x07\xC0\x0F\x18\x1C\xAA\x00\x97\x00\x38\x24\x0E\xF5\x80\xF5\xF0\x3E\x28\x07\x6F\xC3\xD6\x60\x00\x29\x02\x61\xA0\x30\xCC\x1B\xE3\x80\x3A\xA0\x06\xE0\x00\x1E\x40\x52\xB8\x2C\x90\x00\x3C\x40\x49\xF0\x16\x01\x00\x1D\xD0\x03\x04\x04\xB9\x40\x41\x90\x0B\x04\x06\x31\x80\x01\x9C\x10\xDE\x01\x9E\x70\x0F\x2A\x01\x9F\xC0\x1C\xD0\x3E\xDE\x01\xB0\x00\x0C\x10\x05\x13\x81\x78\x20\x1B\x86\x03\x6E\x40\x0E\x48\x1C\x42\x03\xC8\xC0\x85\xBC\x07\xD1\x01\x9C\x50\xB7\xF6\x00\x3D\x80\x0C\x18\x0D\x9D\x06\x0C\xA0\x0B\xE4\x03\x0C\x00\x63\xF0\x16\xEE\x01\x1E\x40\x63\xA8\x00\xF8\x00\x07\x60\x06\x88', 598812, True),
    (b'\x0F' * 32, b'Hi mate!', 13, 6, 122,  # It doesn't work the other way around.
      b'\x00\x6F\x80\x01\x3C\x03\x34\x82\xD9\x60\x38\x18\x02\xAB\x40\x05\xE0\x38\x48\x03\x6C\xC0\x02\xBC\x0D\x65\x00\xE9\xF0\x02\x98\x02\xE5\x00\xDB\xA0\x1A\x4B\x02\x60\x00\xA1\x1C\x04\x24\x01\x2F\x00\x12\xCA\x06\x94\x00\xEF\x28\x18\x2B\x01\x13\xC0\x38\xA0\x02\x1C\x00\xDB\x70\x00\x26\x09\xD7\xC0\x7A\x40\x08\x9F\x00\x5E\xA0\x94\xB8\x06\xD2\x02\x1C\xC0\x19\x84\x0F\xA2\x01\x26\x38\x20\x81\x00\x40\x80\x0D\x7C\x05\xA1\x82\x3E\xF0\x2F\x94\x03\x7C\x80\x9F\xD8\x12\x93\x02\xB2\xC0\x32\x30\x01\xCD\x01\x24\x50\x3D\x44\x05\xDB\x40\x3C\x10\x0A\x3B\x01\xA8\x40\x5F\x14\x00\xC6\x00\xFE\x20\x5F\x34\x0A\x07\xC0\x0F\x18\x1C\xAA\x00\x97\x00\x38\x24\x0E\xF5\x80\xF5\xF0\x3E\x28\x07\x6F\xC3\xD6\x60\x00\x29\x02\x61\xA0\x30\xCC\x1B\xE3\x80\x3A\xA0\x06\xE0\x00\x1E\x40\x52\xB8\x2C\x90\x00\x3C\x40\x49\xF0\x16\x01\x00\x1D\xD0\x03\x04\x04\xB9\x40\x41\x90\x0B\x04\x06\x31\x80\x01\x9C\x10\xDE\x01\x9E\x70\x0F\x2A\x01\x9F\xC0\x1C\xD0\x3E\xDE\x01\xB0\x00\x0C\x10\x05\x13\x81\x78\x20\x1B\x86\x03\x6E\x40\x0E\x48\x1C\x42\x03\xC8\xC0\x85\xBC\x07\xD1\x01\x9C\x50\xB7\xF6\x00\x3D\x80\x0C\x18\x0D\x9D\x06\x0C\xA0\x0B\xE4\x03\x0C\x00\x63\xF0\x16\xEE\x01\x1E\x40\x63\xA8\x00\xF8\x00\x07\x60\x06\x88', -1, False),
    (b'abcdefghijklmnopqrstuvwxyz123456', b'12345678', 9, 7, 200,  # Recommended profile "S".
      b'\x01\x35\x05\x17\x02\x1A\x05\xAE\x04\xB5\x04\xBA\x01\xCB\x00\xFF\x02\x00\x04\x9E\x04\x4D\x05\x17\x00\x8A\x00\xEC\x00\x2A\x03\x58\x05\x0C\x02\x29\x03\x21\x01\x01\x00\xE5\x04\x2A\x00\x40\x02\xC9\x00\x1C\x01\x58\x02\x78\x02\x8D\x04\x3B\x02\xAA\x03\xCB\x00\xF3\x00\xC2\x00\x12\x01\x58\x05\xFD\x01\x42\x06\x71\x00\x71\x05\xA4\x00\x34\x03\x5E\x00\x5B\x00\xDE\x01\x84\x00\x8B\x00\x60\x02\xC8\x01\xE7\x02\xA7\x00\x91\x03\x59\x03\x35\x01\x7B\x05\xD9\x03\x9B\x00\xA7\x01\x77\x01\x7A\x00\x4A\x00\x3A\x01\xEF\x00\xFE\x04\x8B\x01\x06\x00\x13\x02\xF8\x01\x04\x01\x6D\x00\xD2\x01\x07\x00\x6D\x01\x2E\x01\x0A\x04\x0B\x01\x5C\x05\xF6\x04\xF9\x00\x4E\x01\x76\x03\x4C\x04\xA5\x00\xE9\x01\xDE\x04\xFD\x03\x60\x01\x2E\x00\x52\x00\x8A\x01\x35\x01\x4B\x02\x81\x00\x47\x04\xEF\x00\x61\x00\x9A\x00\xDE\x01\x30\x02\x1B\x02\xCF\x00\x89\x05\x1D\x01\x83\x01\x84\x01\x72\x01\x2A\x00\x84\x02\xD8\x01\xBD\x00\xF6\x00\x87\x04\x15\x00\x15\x02\x5C\x02\x4C\x01\x1C\x02\x09\x02\xC5\x04\x34\x01\x46\x00\x2F\x01\x2D\x02\x30\x02\x34\x01\x8A\x00\x2A\x00\xDA\x00\x2C\x0B\xD2\x02\x1F\x02\x70\x03\x00\x03\x81\x01\xF1\x02\x42\x00\x99\x00\xF2\x00\xC0\x03\x8B\x04\x1E\x01\x54\x03\x52\x00\x29\x04\x9F\x02\x84\x00\xF4\x00\x7C\x00\xE0\x00\xEE\x03\x0D\x00\xA0\x01\x92\x04\x49\x00\x5B\x04\x10\x02\xCD\x01\xAC\x02\x0B\x01\x43\x01\xD8\x02\xC7\x02\x1D\x05\x21\x00\x69\x01\x56\x01\x52\x00\xD9\x00\xE7\x04\xA8\x00\xDC\x00\xEE\x00\x7C\x02\x65\x02\x3B\x05\x11\x00\x1B\x00\xEA\x04\x76\x00\x9A\x02\x6A\x01\x27\x01\xDA\x01\x8A\x00\xC0\x04\x9C\x01\x13\x00\x12\x05\xBF\x00\x3D\x00\x49\x02\xA2\x02\x8C\x01\x7A\x02\xAA\x03\xA1\x00\x99\x00\xB2\x08\xF2\x01\x41\x05\x17', 109895, True),
    # The other profiles are too large to be included here.
    (b'abcdefghijklmnopqrstuvwxyz123456', b'87654321', 17, 7, 160,  # A rather hard certificate (21.0M avg, 23.9M actual)
      b'\x00\xD2\x7B\x02\x9A\xB1\x00\x41\x79\x00\xE0\x93\x01\xD6\xB1\x00\x99\x28\x00\x84\x68\x05\x45\x94\x00\x72\xE9\x02\xA6\xBA\x01\x4C\xF5\x00\x0F\x67\x00\x43\x4C\x00\xDD\x1C\x02\x78\xEB\x00\xEB\x90\x02\xE6\xE4\x01\x0B\x04\x00\x15\xA8\x0C\x23\x50\x00\x17\x69\x00\x0A\xDB\x00\x6A\xE8\x02\x62\xE3\x01\x61\x35\x00\xA1\x75\x02\xA2\x67\x01\x5D\xE8\x03\x4A\x08\x03\xF4\x6C\x0D\xE5\x72\x04\x4C\xA1\x07\x27\x80\x00\x5A\x61\x00\xE1\x9A\x07\x4F\x7F\x02\x8A\xB7\x00\x88\x34\x02\x56\x71\x00\x3B\xBC\x00\x09\x46\x06\x39\xBB\x00\x67\xE1\x01\x18\xB8\x00\x01\x5F\x04\x9B\x60\x00\x1D\x3D\x05\x30\xC6\x02\x01\x35\x02\x6D\x21\x04\x48\x70\x00\x5D\xCB\x03\x3E\x60\x02\x3D\xA5\x01\x53\xF7\x01\x62\x29\x04\xF7\x74\x02\x46\x1D\x03\x93\x47\x03\x6D\xFE\x06\xAC\xB0\x00\x69\xC7\x04\x0C\x78\x01\x78\xE7\x09\x2A\x1A\x03\x50\x5B\x01\x7A\x06\x02\x3C\xC9\x03\xC0\xE8\x01\xC4\x40\x09\x22\x21\x04\x69\x7B\x01\xC2\x9E\x01\x66\xE9\x01\xDD\x04\x00\x12\x86\x05\x50\x94\x00\x4E\xDC\x01\x8E\xED\x00\x53\x45\x05\x4E\x35\x00\x37\xAB\x0C\x51\x6F\x02\x40\x54\x00\x16\xF5\x01\xC4\x20\x00\x14\xFA\x01\x5D\x89\x01\x79\x42\x02\x50\xAB\x01\x83\x15\x01\x54\xA0\x00\xE8\x6F\x00\x22\x56\x03\xBE\xBD\x00\x44\x71\x01\x34\xE0\x01\x82\xD9\x01\x29\xB3\x00\x23\x4E\x01\xA4\xCE\x02\x9F\xDA\x01\xAC\x59\x00\x59\x2F\x02\xCF\x33\x01\x47\x1E\x00\x75\xF2\x00\xB8\xDF\x04\x7C\xA0\x01\x80\x95\x03\x97\x70\x03\x45\x8A\x00\x8B\x96\x00\xEE\x08\x03\x8A\xC3\x00\xA8\x60\x01\xD2\x61\x01\xA0\x92\x00\x23\x5C\x05\x30\x96\x01\x55\x56\x00\x77\xCD\x00\x0B\x1D\x01\xD1\x5B\x00\x32\x5E\x02\x1E\x9D\x00\xB3\x67\x03\x27\xA1\x02\xCC\xE2\x00\xBC\x52\x01\x8E\xDB\x03\xAE\xCB\x01\x76\xB9\x08\xF5\xF7\x03\x35\x22\x00\x52\x52\x00\x89\xE4\x00\x67\x34\x00\x8A\x21\x00\xA3\x8E\x03\x61\x0A\x00\x04\x75\x04\x06\xE6\x01\x5F\xB9\x03\x4B\x8F\x04\x9A\x31\x01\x44\xCC\x01\xB7\xCF\x01\x0A\x96\x01\x8D\x9A\x01\x3D\xBE\x05\x2C\xA5\x00\x6C\x96\x00\xF5\x3E\x00\x1B\xBF\x05\x52\x40\x00\xAD\x62\x02\x9E\x2F\x00\xE9\xFD\x08\xEB\xEA', 23896052, True),
    (b'abcdefghijklmnopqrstuvwxyz123456', b'la8aW4zP', 24, 8, 10,  # An extremely hard certificate (168M avg, 141M actual)
      b'\x02\xA3\x0A\x20\x00\xF6\x1C\x17\x00\x04\x9D\x05\x00\xFB\x8D\x00\x02\x04\x41\xCF\x00\x72\x11\x1A\x00\x7A\x16\x24\x00\x09\x4B\xB4\x00\x15\x57\x4C\x00\xBF\x28\x44', 141001879, True),
    (b'abcdefghijklmnopqrstuvwxyz123456', b'la8aW4zP', 24, 8, 10,  # A slightly wrong certificate
      b'\x02\xA3\x0A\x20\x00\xF6\x1C\x17\x00\x04\x9D\x05\x00\xFB\x8D\x00\x02\x04\x41\xCF\x00\x72\x11\x1A\x00\x7A\x16\x24\x00\x09\x4B\xB4\x00\x15\x57\x4C\x00\xBE\x28\x44', -1, False),
]

# Magic numbers
H_LAST_HASH_OFF = 0
H_LAST_HASH_LEN = 256 // 8
H_NONCE_OFF = H_LAST_HASH_OFF + H_LAST_HASH_LEN
H_NONCE_LEN = 8
H_TOKEN_OFF = H_NONCE_OFF + H_NONCE_LEN
H_TOKEN_LEN = 8
H_STEP_OFF = H_TOKEN_OFF + H_TOKEN_LEN
H_STEP_LEN = 4
HASHBYTES = H_STEP_OFF + H_STEP_LEN
assert HASHBYTES == H_LAST_HASH_LEN + H_STEP_LEN + H_TOKEN_LEN + H_NONCE_LEN


def analyze_params(init_hash, token, difficulty, safety, steps, hashes_actual):
    print('Initial hash: {}'.format(init_hash))
    print('Token: {}'.format(token))
    print('Difficulty: {}'.format(difficulty))
    print('Safety: {}'.format(safety))
    print('Steps: {}'.format(steps))
    assert len(init_hash) == H_LAST_HASH_LEN
    assert len(token) == H_TOKEN_LEN
    assert difficulty + safety <= 64
    print('--------------------')
    print('Bits per step: {}'.format(difficulty + safety))
    print('Probability of impossibility: < 2^({})'.format(
        log2(steps) - 2 ** safety))
    print('E[num hashes]: {}'.format(steps * (2 ** difficulty)))
    print('Actual num hashes: {}'.format(hashes_actual))
    print('Certificate byte length: {}'.format(
        ceil(steps * (difficulty + safety) / 8)))
    print('--------------------')


def check_difficulty(buf, difficulty):
    digest = sha256(buf).digest()
    return digest, all(digest[i // 8] & (1 << (7 - i % 8)) == 0
                       for i in range(difficulty))


def extract_nonce(cert, cert_off, bits):
    nonce = bytearray(H_NONCE_LEN)
    nonce_off = 64 - bits
    for bit in range(0, bits):
        certbit = (cert[(cert_off + bit) // 8] << ((cert_off + bit) % 8)) & 0x80
        nonce[(nonce_off + bit) // 8] |= certbit >> ((nonce_off + bit) % 8)
    assert nonce != bytearray(H_NONCE_LEN), (cert, bits, cert_off, nonce_off)
    return nonce


def try_verify(init_hash, token, difficulty, safety, steps, certificate):
    if len(certificate) != ceil(steps * (difficulty + safety) / 8):
        print('Bad length.')
        return False
    remaining = (8 - (steps * (difficulty + safety)) % 8) % 8
    if certificate[-1] & ((1 << remaining) - 1) != 0:
        print('Bad padding.')
        return False
    # hashbuf = last_hash || nonce || token || step
    hashbuf = bytearray(H_LAST_HASH_LEN + H_NONCE_LEN)
    hashbuf.extend(token)
    hashbuf.extend(b'\xFF' * H_STEP_LEN)
    assert len(hashbuf) == HASHBYTES
    last_hash = init_hash
    step_struct = Struct('>I')
    for i in range(0, steps):
        nonce = extract_nonce(certificate, (difficulty + safety) * i, difficulty + safety)
        hashbuf[H_LAST_HASH_OFF:H_LAST_HASH_OFF + H_LAST_HASH_LEN] = last_hash
        assert len(hashbuf) == HASHBYTES
        hashbuf[H_NONCE_OFF:H_NONCE_OFF + H_NONCE_LEN] = nonce
        assert len(hashbuf) == HASHBYTES
        hashbuf[H_STEP_OFF:H_STEP_OFF + H_STEP_LEN] = step_struct.pack(i)
        assert len(hashbuf) == HASHBYTES
        last_hash, success = check_difficulty(hashbuf, difficulty)
        if not success:
            print('Failed at step {}, with buf {}, resulting in hash {}'.format(
                i, hashbuf, last_hash))
            return False
    return True


def run_on(init_hash, token, difficulty, safety, steps, certificate, hashes_actual, valid_expect):
    analyze_params(init_hash, token, difficulty, safety, steps, hashes_actual)
    valid_actual = try_verify(init_hash, token, difficulty, safety, steps, certificate)
    print('Valid: {}'.format(valid_actual))
    print('Matches expectation: {}'.format(valid_actual == valid_expect))
    if valid_actual != valid_expect:
        print('===================')
        print('== ERROR: Wrong! ==')
        print('===================')
        return False
    return True


SELFTEST_FORMAT = '''\
    {{
        "{name}",
        {{"{init_hash}",
            "{token}", {difficulty}, {safety}, {steps}}},
        1, {hashes},
        STEPPOW_STRING_AND_SIZE("{cert}")
    }}\
'''


def bytes_to_cstr(bb):
    return ''.join('\\x{:02x}'.format(b) for b in bb)


def print_selftests(certificates):
    parts = []
    for i, selftest in enumerate(certificates):
        init_hash, token, diff, safety, steps, cert, hashes, valid = selftest
        if not valid:
            continue
        parts.append(SELFTEST_FORMAT.format(
            name='verify.py #{}'.format(i),
            init_hash=bytes_to_cstr(init_hash),
            token=bytes_to_cstr(token),
            difficulty=diff,
            safety=safety,
            steps=steps,
            cert=bytes_to_cstr(cert),
            hashes = hashes,
        ))
    print(',\n'.join(parts))


def run_all(certificates):
    all_good = True
    for i, args in enumerate(certificates):
        print('========================================')
        print('Checking cert #{} ({} bytes)'.format(i, len(args[5])))
        all_good = run_on(*args) and all_good
    return all_good


def run(argv):
    if len(argv) == 1:
        if run_all(TEST_CERTS):
            exit(0)
        else:
            exit(1)
    elif len(argv) == 2 and argv[1] == '--print-selftests':
        print_selftests(TEST_CERTS)
        exit(0)
    else:
        print('Unrecognized argument(s): {}\nUSAGE: {} [--print-selftests]'.format(
            argv[1:], argv[0]), file=sys.stderr)
        exit(1)

if __name__ == '__main__':
    run(sys.argv)
