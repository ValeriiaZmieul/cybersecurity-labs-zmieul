import re
import unicodedata
import pandas as pd


# --- Налаштування персональних даних (використані у генерації ключів) ---
person = {
    "first_name": "Валерія",
    "last_name": "Змєул",
    "birthdate": "06.12.2004"  # DD.MM.YYYY
}

plaintext = "Захист інформації – важлива дисципліна"

# --- Український алфавіт (малі літери) ---
uk_alphabet = list("абвгґдеєжзииіїйклмнопрстуфхцчшщьюя")
uk_alphabet = ['а','б','в','г','ґ','д','е','є','ж','з','и','і','ї','й','к','л','м','н','о','п','р','с','т','у','ф','х','ц','ч','ш','щ','ь','ю','я']

ALPHABET = uk_alphabet
ALPHA_SET = {c for c in ALPHABET}

def normalize_text(s):
    return unicodedata.normalize("NFC", s).lower()

# --- Генерація ключів на основі персональних даних ---
def caesar_key_from_birthdate(birthdate):
    # сумуємо всі цифри у даті
    digits = re.findall(r"\d", birthdate)
    s = sum(int(d) for d in digits)
    # зробимо зсув у межах довжини алфавіту (0..len-1)
    shift = s % len(ALPHABET)
    return shift

def vigenere_key_from_surname(surname):
    # використовуємо прізвище як ключ, нормалізуємо і видаляємо недопустимі символи
    s = normalize_text(surname)
    # замінюємо латинські аналоги, якщо користувач ввів латиницею - спрощено
    s = re.sub(r"[^а-яґєіїьюя]", "", s)
    # якщо після очищення порожньо, використаємо ім'я
    if not s:
        return "ключ"
    return s

# --- Цезар ---
def caesar_encrypt(text, shift):
    text_n = normalize_text(text)
    out = []
    for ch in text_n:
        if ch in ALPHA_SET:
            idx = ALPHABET.index(ch)
            out_idx = (idx + shift) % len(ALPHABET)
            out.append(ALPHABET[out_idx])
        else:
            out.append(ch)
    return "".join(out)

def caesar_decrypt(cipher, shift):
    text_n = normalize_text(cipher)
    out = []
    for ch in text_n:
        if ch in ALPHA_SET:
            idx = ALPHABET.index(ch)
            out_idx = (idx - shift) % len(ALPHABET)
            out.append(ALPHABET[out_idx])
        else:
            out.append(ch)
    return "".join(out)

# --- Віженер ---
def vigenere_extend_key(key, text):
    key_n = normalize_text(key)
    key_letters = [c for c in key_n if c in ALPHA_SET]
    if not key_letters:
        key_letters = ['к']  # fallback
    out = []
    j = 0
    for ch in normalize_text(text):
        if ch in ALPHA_SET:
            out.append(key_letters[j % len(key_letters)])
            j += 1
        else:
            out.append(ch)
    return "".join(out)

def letter_to_index(ch):
    return ALPHABET.index(ch)

def vigenere_encrypt(text, key):
    text_n = normalize_text(text)
    ext_key = vigenere_extend_key(key, text)
    out = []
    for pt_ch, k_ch in zip(text_n, ext_key):
        if pt_ch in ALPHA_SET:
            c = ALPHABET[(letter_to_index(pt_ch) + letter_to_index(k_ch)) % len(ALPHABET)]
            out.append(c)
        else:
            out.append(pt_ch)
    return "".join(out)

def vigenere_decrypt(cipher, key):
    cipher_n = normalize_text(cipher)
    ext_key = vigenere_extend_key(key, cipher)
    out = []
    for ct_ch, k_ch in zip(cipher_n, ext_key):
        if ct_ch in ALPHA_SET:
            p = ALPHABET[(letter_to_index(ct_ch) - letter_to_index(k_ch)) % len(ALPHABET)]
            out.append(p)
        else:
            out.append(ct_ch)
    return "".join(out)

# --- Метрики для порівняння ---
def readability_metric(text):
    # простий індикатор: доля зрозумілих (кірилічних) букв до загальної довжини
    if not text:
        return 0.0
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    cyr_count = sum(1 for c in letters if c in ALPHA_SET)
    return cyr_count / len(letters)

def key_complexity_caesar(shift):
    # для Цезаря: складність вимірюється розміром зсуву по відношенню до алфавіту
    # ближче до середини більш "заплутаний" — даємо просту метрику
    mid = len(ALPHABET) / 2
    dist = abs(shift - mid)
    complexity = 1 - (dist / mid)  # 0..1
    return max(0.0, complexity)

def key_complexity_vigenere(key):
    # для Віженера: довжина ключа і кількість унікальних символів
    k = [c for c in normalize_text(key) if c in ALPHA_SET]
    if not k:
        return 0.0
    uniq = len(set(k))
    complexity = (len(k) * uniq) / (len(ALPHABET) * len(k))  # simplified -> uniq/len(alphabet)
    return uniq / len(ALPHABET)

# --- Генерація ключів ---
caesar_shift = caesar_key_from_birthdate(person["birthdate"])
vigenere_key = vigenere_key_from_surname(person["last_name"])

# --- Шифрування ---
caesar_cipher = caesar_encrypt(plaintext, caesar_shift)
vigenere_cipher = vigenere_encrypt(plaintext, vigenere_key)

# --- Дешифрування (перевірка) ---
caesar_decrypted = caesar_decrypt(caesar_cipher, caesar_shift)
vigenere_decrypted = vigenere_decrypt(vigenere_cipher, vigenere_key)

# --- Обчислення метрик ---
metrics = []
for method, cipher, key_desc in [
    ("Caesar", caesar_cipher, f"shift={caesar_shift}"),
    ("Vigenere", vigenere_cipher, f"key='{vigenere_key}'")
]:
    metrics.append({
        "method": method,
        "key": key_desc,
        "plaintext_length": len(plaintext),
        "ciphertext_length": len(cipher),
        "readability_ratio": round(readability_metric(cipher), 3),
        "key_complexity": round(key_complexity_caesar(caesar_shift) if method=="Caesar" else key_complexity_vigenere(vigenere_key), 3)
    })

# --- Підсумкові результати ---
print("Персональні дані (використані для генерації ключів):")
print("  Прізвище:", person["last_name"])
print("  Ім'я:", person["first_name"])
print("  Дата народження:", person["birthdate"])
print()
print("Вхідний текст:")
print(" ", plaintext)
print()
print("Згенеровані ключі:")
print("  Caesar shift (сума цифр дати % len(alphabet)) ->", caesar_shift)
print("  Vigenere key (з прізвища) ->", vigenere_key)
print()
print("Результати шифрування:")
print("  Caesar ciphertext:")
print("   ", caesar_cipher)
print("  Vigenere ciphertext:")
print("   ", vigenere_cipher)
print()
print("Перевірка дешифрування:")
print("  Caesar decrypted == plaintext ?", caesar_decrypted == normalize_text(plaintext))
print("  Vigenere decrypted == plaintext ?", vigenere_decrypted == normalize_text(plaintext))
print()

# Підготовка таблиці порівняння
df = pd.DataFrame(metrics)
df["readability_percent"] = (df["readability_ratio"] * 100).astype(str) + "%"
df_display = df[["method","key","plaintext_length","ciphertext_length","readability_percent","key_complexity"]]

print(df_display)

# Висновки (короткі)
conclusions = []
conclusions.append("1) Довжина шифртексту для обох методів дорівнює довжині початкового повідомлення (символ-на-символ шифрування для букв).")
conclusions.append("2) Readability_ratio показує, наскільки багато кириличних літер залишаються впізнаваними у шифртексті; для Цезаря значення може бути відносно високим при малих зміщеннях, для Віженера зміни часто виглядають більш 'розбитими'.")
conclusions.append("3) Складність ключа: для Цезаря ключ — одне число, низька ентропія; для Віженера ключ — рядок, складність зростає з довжиною і унікальністю символів.")
conclusions.append("4) У контексті сучасної криптографії обидва методи є ненадійними для захисту реальних даних; їхня цінність — навчальна та історична.")
print("Короткі висновки:")
for c in conclusions:
    print(" ", c)

# Додаткові поради:
print()
print("Рекомендації для демонстраційного використання та тестів:")
print(" - Показувати різні варіанти ключів (короткі/довгі, з низькою/високою унікальністю символів).")
print(" - Додати аналіз криптостійкості (наприклад, частотний аналіз для Цезаря та к-р на ключ довжину для Віженера).")
print()
print("--- Кінець демонстрації ---")
