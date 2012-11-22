# Dojima, a markets client.
# Copyright (C) 2012  Emery Hemingway
#
# The code herein is nearly verbatim work released into
# the public domain by Gavin Anderson.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import hashlib
import re

__b58chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
__b58base = len(__b58chars)

def b58decode(v, length):
    """decode v into a string of len bytes"""
    long_value = 0L
    for (i, c) in enumerate(v[::-1]):
        long_value += __b58chars.find(c) * (__b58base**i)

    result = ''
    while long_value >= 256:
        div, mod = divmod(long_value, 256)
        result = chr(mod) + result
        long_value = div
    result = chr(long_value) + result

    nPad = 0
    for c in v:
        if c == __b58chars[0]:
            nPad +=1
        else:
            break

    result = chr(0)*nPad + result
    if length is not None and len(result) != length:
        return None

    return result


def is_valid_address(address_string):
    if re.match(r'[1-9A-Za-z]{27,35}$', address_string) is None:
        return False

    address = b58decode(address_string, 25)
    if address is None:
        return False

    version = address[0]
    checksum = address[-4:]
    vh160 = address[:-4] # Version plus hash160 is what is checksummed

    h3 = hashlib.sha256( hashlib.sha256(vh160).digest() ).digest()
    if h3[0:4] == checksum:
        return True

    return False
