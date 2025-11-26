import re
import unicodedata

# --- Налаштування персональних даних студента (вхідні дані) ---
person = {
    "first_name": "Валерія",
    "last_name": "Змєул",
    "birthdate": "06.12.2004"  # DD.MM.YYYY
}

# --- Допоміжні функції ---
def normalize_text(s):
    # Нормалізація: Unicode NFC, приведення до нижнього регістру
    if s is None:
        return ""
    return unicodedata.normalize("NFC", s).lower()

# Проста транслітерація кирилиці -> латиниця (для загальних випадків)
trans_map = {
    'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ie','ж':'zh','з':'z','и':'y','і':'i','ї':'i',
    'й':'i','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'kh',
    'ц':'ts','ч':'ch','ш':'sh','щ':'shch','ь':'','ю':'iu','я':'ia','є':'e'
}

def transliterate_cyrillic(s):
    s = normalize_text(s)
    out = []
    for ch in s:
        out.append(trans_map.get(ch, ch))
    return "".join(out)

def contains_personal_fragments(password, person):
    pwd = normalize_text(password)
    found = []
    for key in ("first_name", "last_name"):
        name = person.get(key, "")
        if not name:
            continue
        name_norm = normalize_text(name)
        name_trans = transliterate_cyrillic(name)
        for candidate in set([name_norm, name_trans]):
            if len(candidate) >= 3 and candidate in pwd:
                found.append((key, candidate))
            for L in range(3, min(6, len(candidate)+1)):
                if candidate[:L] in pwd:
                    found.append((key + "_prefix", candidate[:L]))
    dob = person.get("birthdate","")
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", dob)
    if m:
        dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
        if yyyy in pwd:
            found.append(("birth_year", yyyy))
        if dd+mm in pwd or dd + "." + mm in pwd or dd + "-" + mm in pwd:
            found.append(("birth_daymonth", dd+mm))
        if dd in pwd:
            found.append(("birth_day", dd))
        if mm in pwd:
            found.append(("birth_month", mm))
    return list({f for f in found})  # remove duplicates

# Простий словниковий список 
dictionary_words = {"password", "qwerty", "admin", "user", "test", "123456", "welcome", "login", "valeria", "ivan"}

def contains_dictionary_word(password):
    pwd = normalize_text(password)
    found = []
    for w in dictionary_words:
        if w in pwd:
            found.append(w)
    alpha_sequences = re.findall(r"[A-Za-zА-Яа-яІіЇїЄєґґ]{4,}", password)
    for s in alpha_sequences:
        if normalize_text(s) not in found:
            found.append(normalize_text(s))
    return found

def char_variety_score(password):
    score = 0
    types = 0
    if re.search(r"[a-z]", password): types += 1
    if re.search(r"[A-Z]", password): types += 1
    if re.search(r"\d", password): types += 1
    if re.search(r"[^\w\s]", password): types += 1  # special chars
    return int((types / 4.0) * 10), types

def length_score(password):
    L = len(password)
    if L < 6:
        return 1
    if L < 8:
        return 3
    if L < 12:
        return 6
    if L < 16:
        return 8
    return 10

def evaluate(password, person):
    pwd = password
    issues = []
    personal = contains_personal_fragments(pwd, person)
    dict_words = contains_dictionary_word(pwd)
    len_sc = length_score(pwd)
    var_sc, var_types = char_variety_score(pwd)
    base = (len_sc + var_sc) / 2.0
    penalty = 0
    details = []
    if personal:
        penalty += 40  # heavy penalty for personal data presence
        details.append(f"Знайдено фрагменти персональних даних у паролі: {personal}")
    if dict_words:
        penalty += 20
        details.append(f"Наявні словникові/очевидні слова/послідовності: {dict_words}")
    if len(pwd) < 6:
        details.append("Пароль дуже короткий (<6 символів).")
    if var_types < 3:
        details.append(f"Низька різноманітність символів (типів: {var_types} — рекомендовано >=3).")
    raw = base * 10  # turn into 0..100 scale
    raw_after = max(0, raw - penalty)
    final_score = int(round(raw_after / 10.0))
    final_score = max(1, min(10, final_score))
    recs = []
    if personal:
        recs.append("Уникайте використання імені, прізвища, і/або дат народження у паролі.")
        recs.append("Не використовуйте прості транслітерації імені/прізвища (наприклад 'valeria', 'zmеul').")
    if dict_words:
        recs.append("Уникайте словникових слів, очевидних підрядків і простих послідовностей.")
    if len(pwd) < 12:
        recs.append("Збільшіть довжину пароля до принаймні 12 символів; краще — 16+ для важливих акаунтів.")
    if var_types < 3:
        recs.append("Додайте великі літери, цифри та спеціальні символи; комбінуйте їх випадковим чином.")
    recs.append("Використовуйте фрази-паролі з 3+ слів або генератор паролів; зберігайте у менеджері паролів.")
    # конкретний приклад сильного пароля
    example = " ".join(["V@l3r!a", "06Dec", "9xT#"])  # демонстрація комбінації
    return {
        "password": pwd,
        "length": len(pwd),
        "length_score": len_sc,
        "variety_score": var_sc,
        "variety_types": var_types,
        "personal_matches": personal,
        "dictionary_matches": dict_words,
        "details": details,
        "penalty": penalty,
        "raw_score_0_100": int(raw_after),
        "final_score_1_10": final_score,
        "recommendations": recs,
        "example_stronger_password": example
    }

# --- Демонстраційні паролі для тестування---
tests = [
    ("Інсекьюрний (включає ім'я і дату)", "Валерія2004"),
    ("Інсекьюрний латиницею + дата", "valeria06122004"),
    ("Покращений приклад", "V@l3r!a#06Dec9xT")
]

# Виконати аналіз для кожного тестового пароля
results = []
for label, pwd in tests:
    res = evaluate(pwd, person)
    res["label"] = label
    results.append(res)

# Вивід у читабельному форматі
for r in results:
    print("—" * 80)
    print(f"Тест: {r['label']}")
    print(f"Пароль: {r['password']}")
    print(f"Довжина: {r['length']} (оцінка довжини: {r['length_score']}/10)")
    print(f"Різноманітність символів: типів = {r['variety_types']}, оцінка = {r['variety_score']}/10")
    if r['personal_matches']:
        print("=> ПРИМІТНО: знайдені фрагменти персональних даних у паролі:", r['personal_matches'])
    if r['dictionary_matches']:
        print("=> ПРИМІТНО: словникові/очевидні підрядки:", r['dictionary_matches'])
    if r['details']:
        for d in r['details']:
            print(" -", d)
    print(f"Штрафні бали (віднято зі шкали): {r['penalty']}")
    print(f"Сирий скор (0–100 після штрафів): {r['raw_score_0_100']}")
    print(f"Кінцева оцінка безпеки (1–10): {r['final_score_1_10']}")
    print("Рекомендації для покращення:")
    for rec in r['recommendations']:
        print(" *", rec)
    print("Приклад сильнішого пароля для натхнення (не копіюйте буквально):", r['example_stronger_password'])
print("—" * 80)
