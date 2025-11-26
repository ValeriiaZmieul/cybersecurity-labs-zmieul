from hashlib import sha256
import os

person = {
    "first_name": "Валерія",
    "last_name": "Змєул",
    "birthdate": "06.12.2004"
}

MOD = 1000007  
K = 7  

def hash_to_int_hex(s: bytes) -> int:
    h = sha256(s).hexdigest()
    return int(h, 16)

def generate_keys(person, secret_salt="default_salt", mod=MOD, k=K):

    seed = (person.get("last_name","") + person.get("first_name","") + person.get("birthdate","") + secret_salt).encode('utf-8')
    priv_int = hash_to_int_hex(seed) % mod
    pub_int = (priv_int * k) % mod
    return priv_int, pub_int

def file_sha256_int(path):
    with open(path, "rb") as f:
        data = f.read()
    h = sha256(data).hexdigest()
    return int(h,16), h  

def sign_document(path, private_key, mod=MOD):
    doc_int, doc_hex = file_sha256_int(path)
    doc_mod = doc_int % mod
    signature = (doc_mod * private_key) % mod
    return signature, doc_hex

def verify_signature(path, signature, public_key, mod=MOD, k=K):
    doc_int, doc_hex = file_sha256_int(path)
    doc_mod = doc_int % mod
    lhs = (signature * k) % mod
    rhs = (doc_mod * public_key) % mod
    valid = (lhs == rhs)
    return valid, {"lhs": lhs, "rhs": rhs, "doc_mod": doc_mod, "doc_hex": doc_hex}

doc_path = "Змєул_резюме.pdf"
content = (
    "Резюме\n"
    "Ім'я: Валерія Змєул\n"
    "Дата народження: 06.12.2004\n"
    "\n"
    "Освіта:\n"
    "- Бакалавр, Комп'ютерні науки\n"
    "\n"
    "Досвід:\n"
    "- Практика в ІТ-проектах, розробка програмного забезпечення.\n"
)
with open(doc_path, "w", encoding="utf-8") as f:
    f.write(content)

private_key, public_key = generate_keys(person, secret_salt="s3cr3t_salt")

signature, doc_hex = sign_document(doc_path, private_key)

valid, details = verify_signature(doc_path, signature, public_key)

tampered_path = "Змєул_резюме_tampered.pdf"
with open(tampered_path, "w", encoding="utf-8") as f:
    f.write(content + "\nДодатковий рядок: зміна документа для тесту.\n")

valid_tampered, details_tampered = verify_signature(tampered_path, signature, public_key)
doc_mod_original = details["doc_mod"]

forged_signature_guess = (doc_mod_original * ((public_key * 12345) % MOD)) % MOD 
valid_forged, details_forged = verify_signature(doc_path, forged_signature_guess, public_key)

report_path = "digital_signature_report.txt"
with open(report_path, "w", encoding="utf-8") as rep:
    rep.write("Digital signature demo report\n\n")
    rep.write(f"Personal seed: {person['last_name']} {person['first_name']} {person['birthdate']}\n")
    rep.write(f"MOD = {MOD}, K = {K}\n\n")
    rep.write(f"Private key (int mod {MOD}): {private_key}\n")
    rep.write(f"Public key (int): {public_key}\n\n")
    rep.write(f"Document path: {doc_path}\n")
    rep.write(f"Document SHA256 (hex): {doc_hex}\n")
    rep.write(f"Signature (int mod {MOD}): {signature}\n\n")
    rep.write(f"Verification on original document: {valid}\n")
    rep.write(f"Verification details (original): {details}\n\n")
    rep.write(f"Tampered document path: {tampered_path}\n")
    rep.write(f"Verification on tampered document: {valid_tampered}\n")
    rep.write(f"Verification details (tampered): {details_tampered}\n\n")
    rep.write("Forged signature attempt:\n")
    rep.write(f" Forged signature guess: {forged_signature_guess}\n")
    rep.write(f" Verification result for forged signature: {valid_forged}\n")
    rep.write(f" Verification details (forged): {details_forged}\n")

print("=== Simplified Digital Signature Demo ===")
print("Document created at:", doc_path)
print("Private key (int mod):", private_key)
print("Public key (int):", public_key)
print("Document SHA256 (hex):", doc_hex)
print("Signature (int mod):", signature)
print("Verification valid (original):", valid)
print("Verification valid (tampered):", valid_tampered)
print("Forgery attempt valid:", valid_forged)
print()
print("Files generated:")
print(" - Document:", doc_path)
print(" - Tampered document:", tampered_path)
print(" - Report:", report_path)
