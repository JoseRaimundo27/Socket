from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os
import base64

class AES:
    def __init__(self, key=None):
        """
        Inicializa o AES com uma chave de 32 bytes.
        Se nenhuma chave for fornecida, gera uma aleatória.
        """
        self.key = key if key and len(key) == 32 else os.urandom(32)
        self.backend = default_backend()

    def encrypt(self, plaintext):
        """
        Criptografa uma mensagem (string) e retorna o texto cifrado como base64.
        """
        iv = os.urandom(16)  # Vetor de inicialização
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext.encode()) + padder.finalize()

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()

        return base64.b64encode(iv + ciphertext).decode('utf-8')

    def decrypt(self, encrypted):
        """
        Descriptografa uma mensagem cifrada em base64 e retorna o texto original.
        """
        encrypted_data = base64.b64decode(encrypted)
        iv = encrypted_data[:16]  # Extrai o IV do início
        ciphertext = encrypted_data[16:]

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv), backend=self.backend)
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()

        return plaintext.decode('utf-8')
