import os
import random
import string

image_dir = "savedImage/signOfStop"
image_extensions = ('.jpg', '.jpeg', '.png', '.bmp')

def random_name(length=12):
    chars = string.ascii_letters + string.digits  # a-z A-Z 0-9
    return ''.join(random.choices(chars, k=length))

files = [f for f in os.listdir(image_dir) if f.lower().endswith(image_extensions)]

used = set()
renamed = 0

for filename in files:
    ext = os.path.splitext(filename)[1].lower()
    while True:
        new_name = random_name() + ext
        if new_name not in used:
            used.add(new_name)
            break

    src = os.path.join(image_dir, filename)
    dst = os.path.join(image_dir, new_name)
    os.rename(src, dst)
    print(f"{filename}  →  {new_name}")
    renamed += 1

print(f"\n총 {renamed}개 파일 이름 변경 완료")
