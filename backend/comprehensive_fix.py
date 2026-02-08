# Comprehensive fix for all corrupted sequences
# The pattern is: incomplete UTF-8 multibyte followed by 'E' or other ASCII
# We need to find a working version or recreate the file

import re

with open('pdf_generator.py', 'rb') as f:
    data = f.read()

# Common corruptions mappings (from error logs and inspection)
fixes = [
    # Main corruptions - these appear to be UTF-8 sequences where the last byte was replaced with 'E'
    (b'\xe6\x81E', b'\xe6\x81\x90'),  # 恐
    (b'\xe3\x81E', b'\xe3\x81\xae'),  # の
    (b'\xe3\x83\x81E', b'\xe3\x83\x86'),  # テ
    (b'\xe9\x81\xdf', b'\xe9\x81\xa0'),  # 遠 (might be 額)
    (b'\xe9\xa1\x81E', b'\xe9\xa1\x8d'),  # 額
    (b'\xe5\xae\x81E', b'\xe5\xae\x9a'),  # 定
    (b'\xe7\x94\x9f\xe6\x81E', b'\xe7\x94\x9f\xe6\x88\x90'),  # 生成
    (b'\xe3\x80\x81E', b'\xe3\x80\x81'),  # 、
    (b'\xef\xbc\x81E', b'\xef\xbc\x89'),  # )
    (b'\xe3\x82\xbf\xe3\x83\x81E', b'\xe3\x82\xbf\xe3\x83\x86'),  # タテ -> タベ
    (b'\xe3\x82\xbb\xe3\x83\x81E', b'\xe3\x82\xbb\xe3\x83\x83'),  # セッ
    (b'\xe3\x80\x81E\x81', b'\xe3\x80\x81\xe3\x81'),  # 、の
    (b'\xe3\x81\x81E', b'\xe3\x81\x84'),  # い
    (b'\xe5\x86\x81E', b'\xe5\x86\x86'),  # 円
    (b'\xe3\x83\x81E\x82', b'\xe3\x83\x86\xe3\x82'),  # テの
    (b'\xe3\x83\x81E\x83', b'\xe3\x83\x86\xe3\x83'),  # テの
    (b'\xe3\x81E\xe3', b'\xe3\x81\xae\xe3'),  # のの
    (b'\xe3\x80\x81E\x81E', b'\xe3\x80\x81\xe3\x83\x86'),  # 、テ
]

print("Applying fixes...")
fixed_data = data
for bad, good in fixes:
    count = fixed_data.count(bad)
    if count > 0:
        print(f"  Replacing {repr(bad)} -> {repr(good)}: {count} occurrences")
        fixed_data = fixed_data.replace(bad, good)

# Write fixed file
with open('pdf_generator_fixed.py', 'wb') as f:
    f.write(fixed_data)

# Test
try:
    content = fixed_data.decode('utf-8')
    print("\n✓ Success! File is valid UTF-8")
    print(f"  Total size: {len(fixed_data)} bytes")
    
    # Try to compile it
    compile(content, 'pdf_generator_fixed.py', 'exec')
    print("✓ File compiles successfully!")
    
except UnicodeDecodeError as e:
    print(f"\n✗ Still has UTF-8 errors: {e}")
    print("  Need more fixes...")
except SyntaxError as e:
    print(f"\n✗ Syntax error: {e}")
    print("  File decodes but has Python syntax errors")
