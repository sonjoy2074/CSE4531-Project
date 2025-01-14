import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def generate_aes_key_iv():
    key = os.urandom(32)  # 256-bit AES key
    iv = os.urandom(16)   # 128-bit IV
    return key, iv

def encrypt_with_aes(key, iv, data):
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv))
    encryptor = cipher.encryptor()
    return encryptor.update(data) + encryptor.finalize()

def encrypt_with_rsa(public_key_pem, data):
    public_key = serialization.load_pem_public_key(public_key_pem)
    return public_key.encrypt(
        data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
