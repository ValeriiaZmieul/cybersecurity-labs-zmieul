from hashlib import sha256
import base64

def derive_key(personal_data: str) -> bytes:
    return sha256(personal_data.encode()).digest()

def xor_crypt(data: bytes, key: bytes) -> bytes:
    return bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])

def encrypt_message(message: str, personal_data: str) -> str:
    key = derive_key(personal_data)
    encrypted = xor_crypt(message.encode("utf-8"), key)
    return base64.b64encode(encrypted).decode("utf-8")

def decrypt_message(ciphertext_b64: str, personal_data: str) -> str:
    key = derive_key(personal_data)
    encrypted = base64.b64decode(ciphertext_b64)
    decrypted = xor_crypt(encrypted, key)
    return decrypted.decode("utf-8")

email = "valeriia.zmieul@hneu.net"
personal_basis = "".join(ch for ch in email if ch.isalnum()) + "2004"

message = "Зустрічаємося завтра о 15:00"

ciphertext = encrypt_message(message, personal_basis)
recovered = decrypt_message(ciphertext, personal_basis)

print(ciphertext, "\n", recovered)