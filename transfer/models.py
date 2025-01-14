from django.db import models
from django.contrib.auth.models import User
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class EncryptedImage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_images')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_images')
    encrypted_image = models.BinaryField()
    encrypted_key = models.BinaryField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def decrypt_image(self, private_key_pem):
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)

        decrypted_key_iv = private_key.decrypt(
            self.encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        aes_key = decrypted_key_iv[:32]  # First 32 bytes are the AES key
        iv = decrypted_key_iv[32:]       # Next 16 bytes are the IV

        cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
        decryptor = cipher.decryptor()
        return decryptor.update(self.encrypted_image) + decryptor.finalize()


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    public_key = models.TextField(blank=True, null=True)
    private_key = models.TextField(blank=True, null=True)

    def generate_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        public_key = private_key.public_key()

        # Serialize keys
        self.private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        self.public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

