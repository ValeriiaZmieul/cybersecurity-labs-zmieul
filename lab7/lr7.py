import os
import time
import hashlib
from PIL import Image
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class AnalyticalProtector:
    def __init__(self, personal_data_key: str):
        self.metrics = {}
        # Генерація ключа на основі персональних даних
        salt = b'fixed_salt_for_lab' 
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(personal_data_key.encode()))
        self.cipher = Fernet(key)

    def _get_file_hash(self, data):
        return hashlib.sha256(data).hexdigest()

    def encrypt_data(self, data: bytes):
        start_time = time.time()
        encrypted_data = self.cipher.encrypt(data)
        end_time = time.time()
        
        self.metrics['enc_time'] = end_time - start_time
        self.metrics['size_after_enc'] = len(encrypted_data)
        return encrypted_data

    def decrypt_data(self, encrypted_data: bytes):
        start_time = time.time()
        decrypted_data = self.cipher.decrypt(encrypted_data)
        end_time = time.time()
        
        self.metrics['dec_time'] = end_time - start_time
        return decrypted_data

    def lsb_hide(self, container_path: str, data: bytes, output_path: str):
        start_time = time.time()
        img = Image.open(container_path)
        encoded = img.copy()
        width, height = img.size
        
        # Перетворюємо дані у бітовий потік (додаємо довжину в початок)
        data_len = len(data).to_bytes(4, byteorder='big')
        full_payload = data_len + data
        bits = ''.join([format(b, '08b') for b in full_payload])
        
        if len(bits) > width * height * 3:
            raise ValueError("Занадто багато даних для цього зображення!")

        bit_idx = 0
        pixels = encoded.load()
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                if bit_idx < len(bits):
                    r = (r & ~1) | int(bits[bit_idx])
                    bit_idx += 1
                if bit_idx < len(bits):
                    g = (g & ~1) | int(bits[bit_idx])
                    bit_idx += 1
                if bit_idx < len(bits):
                    b = (b & ~1) | int(bits[bit_idx])
                    bit_idx += 1
                pixels[x, y] = (r, g, b)
                if bit_idx >= len(bits):
                    break
            if bit_idx >= len(bits):
                break
        
        encoded.save(output_path, "PNG")
        end_time = time.time()
        self.metrics['stego_hide_time'] = end_time - start_time
        self.metrics['stego_file_size'] = os.path.getsize(output_path)
        return output_path

    def lsb_reveal(self, stego_path: str):
        start_time = time.time()
        img = Image.open(stego_path)
        pixels = img.load()
        width, height = img.size
        
        extracted_bits = []
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                extracted_bits.append(str(r & 1))
                extracted_bits.append(str(g & 1))
                extracted_bits.append(str(b & 1))
        
        all_bits = "".join(extracted_bits)
        all_bytes = [int(all_bits[i:i+8], 2) for i in range(0, len(all_bits), 8)]
        all_bytes = bytes(all_bytes)
        
        # Читаємо перші 4 байти довжини
        data_len = int.from_bytes(all_bytes[:4], byteorder='big')
        extracted_data = all_bytes[4:4+data_len]
        
        end_time = time.time()
        self.metrics['stego_reveal_time'] = end_time - start_time
        return extracted_data

    def run_full_cycle(self, input_file, container_image):
        print(f"--- Запуск комплексного захисту для: {input_file} ---")
        
        # 0. Початкові метрики
        with open(input_file, 'rb') as f:
            original_data = f.read()
        self.metrics['original_size'] = len(original_data)
        original_hash = self._get_file_hash(original_data)

        # 1. ЕТАП ШИФРУВАННЯ
        print("Етап 1: Шифрування AES...")
        encrypted = self.encrypt_data(original_data)
        
        # 2. ЕТАП СТЕГАНОГРАФІЇ
        print("Етап 2: LSB-приховування...")
        stego_path = "protected_container.png"
        self.lsb_hide(container_image, encrypted, stego_path)

        # 3. ЕТАП ВІДНОВЛЕННЯ (ЗВОРОТНИЙ ПРОЦЕС)
        print("Етап 3: Вилучення та дешифрування...")
        extracted_encrypted = self.lsb_reveal(stego_path)
        recovered_data = self.decrypt_data(extracted_encrypted)
        
        # 4. ПЕРЕВІРКА ЦІЛІСНОСТІ
        recovered_hash = self._get_file_hash(recovered_data)
        integrity = (original_hash == recovered_hash)
        
        self.generate_report(integrity)

    def generate_report(self, integrity):
        print("\n" + "="*40)
        print("ЗВІТ АНАЛІТИЧНОГО МОДУЛЯ")
        print("="*40)
        print(f"Статус цілісності: {'УСПІШНО' if integrity else 'ПОМИЛКА'}")
        print(f"Розмір оригіналу: {self.metrics['original_size']} байт")
        print(f"Розмір після AES: {self.metrics['size_after_enc']} байт")
        print(f"Розмір стего-контейнера: {self.metrics['stego_file_size']} байт")
        print("-" * 20)
        print(f"Час шифрування: {self.metrics['enc_time']:.4f} сек")
        print(f"Час вбудовування: {self.metrics['stego_hide_time']:.4f} сек")
        print(f"Час вилучення: {self.metrics['stego_reveal_time']:.4f} сек")
        print(f"Час дешифрування: {self.metrics['dec_time']:.4f} сек")
        print("-" * 20)
        print("Рекомендації:")
        if self.metrics['size_after_enc'] > self.metrics['original_size'] * 1.5:
            print("- Увага: Оверхед шифрування високий. Розгляньте інший режим.")
        print("- Використовуйте зображення формату PNG для уникнення втрат при стисненні.")
        print("- Для підвищення безпеки змініть статичну сіль (salt) на динамічну.")

# ДЕМОНСТРАЦІЯ РОБОТИ
if __name__ == "__main__":
    # Створення тестових файлів
    with open("secret.txt", "w", encoding="utf-8") as f:
        f.write("Тестовий запис")
    
    # Створення простого зображення-контейнера 
    dummy_img = Image.new('RGB', (200, 200), color = 'red')
    dummy_img.save('container.png')

    # Ініціалізація системи (Ключ - Прізвище студента)
    protector = AnalyticalProtector(personal_data_key="Valeriia_Zmieul")
    
    # Виконання циклу
    protector.run_full_cycle("secret.txt", "container.png")

    # Демонстрація необхідності обох етапів
    print("\n--- Демонстрація необхідності обох етапів ---")
    print("1. Спроба відкрити стего-файл як текст: [Неможливо - це зображення]")
    print("2. Спроба отримати дані без дешифрування:")
    stego_data = protector.lsb_reveal("protected_container.png")
    print(f"   Результат вилучення (перші 20 байт): {stego_data[:20].hex()}... (виглядає як шум)")