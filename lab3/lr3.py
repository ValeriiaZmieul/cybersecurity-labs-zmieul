from PIL import Image
import numpy as np
import math, os, unicodedata, re

def text_to_bits(s: str) -> str:
    data = s.encode('utf-8')
    return ''.join(f'{byte:08b}' for byte in data)

def bits_to_text(b: str) -> str:
    bytes_list = [int(b[i:i+8], 2) for i in range(0, len(b), 8)]
    return bytes(bytes_list).decode('utf-8', errors='replace')

def hide_message(input_image_path: str, output_image_path: str, message: str, bits_per_channel: int = 1):
    if bits_per_channel < 1 or bits_per_channel > 2:
        raise ValueError("bits_per_channel must be 1 or 2 for this demo.")
    img = Image.open(input_image_path).convert('RGB')
    arr = np.array(img)
    h, w, _ = arr.shape
    capacity_bits = h * w * 3 * bits_per_channel
    payload_bits = text_to_bits(message)
    length_header = f'{len(payload_bits):032b}'
    full_payload = length_header + payload_bits
    if len(full_payload) > capacity_bits:
        raise ValueError(f"Message too large for capacity. Need {len(full_payload)} bits, capacity {capacity_bits} bits.")
    flat = arr.flatten()
    out_flat = flat.copy()
    bit_idx = 0
    for i in range(len(flat)):
        for b in range(bits_per_channel):
            if bit_idx < len(full_payload):
                bit = int(full_payload[bit_idx])
                mask = 0xFF ^ (1 << b)
                out_flat[i] = np.uint8((out_flat[i] & mask) | (bit << b))

                bit_idx += 1
            else:
                break
        if bit_idx >= len(full_payload):
            break
    out_arr = out_flat.reshape(arr.shape)
    out_img = Image.fromarray(out_arr.astype('uint8'), 'RGB')
    out_img.save(output_image_path, format='PNG')
    return {
        "message_bits": len(payload_bits),
        "total_payload_bits": len(full_payload),
        "capacity_bits": capacity_bits,
        "pixels_changed_estimate": int(math.ceil(len(full_payload) / (3*bits_per_channel)))
    }

def extract_message(stego_image_path: str, bits_per_channel: int = 1) -> str:
    img = Image.open(stego_image_path).convert('RGB')
    arr = np.array(img)
    flat = arr.flatten()
    seq_bits = []
    for i in range(len(flat)):
        for b in range(bits_per_channel):
            seq_bits.append(str((flat[i] >> b) & 1))
    header = ''.join(seq_bits[:32])
    length = int(header, 2)
    message_bits = ''.join(seq_bits[32:32+length])
    if len(message_bits) % 8 != 0:
        message_bits = message_bits[:(len(message_bits)//8)*8]
    return bits_to_text(message_bits)

# def generate_test_image(path: str, size=(512,512)):
#     w, h = size
#     arr = np.zeros((h, w, 3), dtype=np.uint8)
#     for y in range(h):
#         for x in range(w):
#             arr[y,x,0] = (x * 255) // (w-1)
#             arr[y,x,1] = (y * 255) // (h-1)
#             arr[y,x,2] = ((x+y) * 255) // (w+h-2)
#     Image.fromarray(arr).save(path, format='PNG')

def mse(img1_path, img2_path):
    a = np.array(Image.open(img1_path).convert('RGB'), dtype=np.float64)
    b = np.array(Image.open(img2_path).convert('RGB'), dtype=np.float64)
    if a.shape != b.shape:
        raise ValueError("Image shapes differ")
    return float(np.mean((a - b) ** 2))

def psnr(img1_path, img2_path):
    m = mse(img1_path, img2_path)
    if m == 0:
        return float('inf')
    max_pixel = 255.0
    return 20 * math.log10(max_pixel / math.sqrt(m))

orig_path = "anotherCat.jpg"
stego_path = "stego_image.png"
report_path = "stego_report.txt"

# generate_test_image(orig_path, size=(512,512))

secret_message = "Змєул Валерія 06.12.2004"

info = hide_message(orig_path, stego_path, secret_message, bits_per_channel=1)

extracted = extract_message(stego_path, bits_per_channel=1)

orig_size = os.path.getsize(orig_path)
stego_size = os.path.getsize(stego_path)
mse_val = mse(orig_path, stego_path)
psnr_val = psnr(orig_path, stego_path)

orig_arr = np.array(Image.open(orig_path).convert('RGB'))
stego_arr = np.array(Image.open(stego_path).convert('RGB'))
diff_pixels = np.sum(np.any(orig_arr != stego_arr, axis=2))
total_pixels = orig_arr.shape[0] * orig_arr.shape[1]

with open(report_path, "w", encoding="utf-8") as f:
    f.write("Steganography LSB demonstration report\n")
    f.write(f"Message: {secret_message}\n")
    f.write(f"Message bits: {info['message_bits']}\n")
    f.write(f"Total payload bits: {info['total_payload_bits']}\n")
    f.write(f"Capacity bits: {info['capacity_bits']}\n")
    f.write(f"Estimated pixels needed: {info['pixels_changed_estimate']}\n")
    f.write(f"Extraction successful: {extracted == secret_message}\n")
    f.write(f"File sizes: original={orig_size}, stego={stego_size}\n")
    f.write(f"MSE={mse_val}, PSNR={psnr_val}\n")
    f.write(f"Pixels changed: {diff_pixels} of {total_pixels}\n")

print("=== Steganography LSB demonstration ===")
print("Original image:", orig_path)
print("Stego image:   ", stego_path)
print()
print("Message to hide:", secret_message)
print("Message bits:", info["message_bits"])
print("Total payload bits (with 32-bit header):", info["total_payload_bits"])
print("Capacity bits:", info["capacity_bits"])
print("Estimated pixels needed:", info["pixels_changed_estimate"])
print()
print("Extraction result:", extracted)
print("Extraction successful:", extracted == secret_message)
print()
print("File sizes: original =", orig_size, "bytes; stego =", stego_size, "bytes")
print("MSE =", round(mse_val,6), "; PSNR =", round(psnr_val,6), "dB")
print(f"Pixels changed: {diff_pixels} of {total_pixels} ({diff_pixels/total_pixels*100:.6f} % )")
print()
print("Files:")
print(f" - Original: [Download original image](sandbox:{orig_path})")
print(f" - Stego:    [Download stego image](sandbox:{stego_path})")
print(f" - Report:   [Download report](sandbox:{report_path})")
