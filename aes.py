# Code from https://www.quickprogrammingtips.com/python/aes-256-encryption-and-decryption-in-python.html
# AES 256 encryption/decryption using pycrypto library
 
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
 
BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s)%BLOCK_SIZE)*chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

def encrypt(raw, password):
    private_key = hashlib.sha256(password.encode("utf-8")).digest()
    raw = pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw)).decode ("utf-8")
 
 
def decrypt(enc, password):
    private_key = hashlib.sha256(password.encode("utf-8")).digest()
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(private_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[16:])).decode ("utf-8")

def test_aes ():
    password = base64.b64encode(Random.new().read(32)).decode ("utf-8")
    message = base64.b64encode(Random.new().read(128)).decode ("utf-8")

    enc = encrypt (message, password)
    dec = decrypt (enc, password)
    assert message == dec

if __name__ == "__main__":
    test_aes ()