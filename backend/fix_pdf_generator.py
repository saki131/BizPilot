# Fix the corrupted byte sequence in pdf_generator.py
with open('pdf_generator.py', 'rb') as f:
    data = f.read()

# The corrupted sequence is: \xe7\xbe\x81E (should be \xe7\xbe\x81\xe3\x80\x82 or just end with quote)
# Let's find and fix it
# Line 18 should be: "representative": "前鼻 和義",

# Find the bad sequence
bad_sequence = b'\xe7\xbe\x81E'
good_sequence = b'\xe7\xbe\xa9"'  # 義" (U+7FA9 = \xe7\xbe\xa9)

print(f"Looking for bad sequence: {repr(bad_sequence)}")
if bad_sequence in data:
    print("Found! Replacing...")
    fixed_data = data.replace(bad_sequence, good_sequence)
    
    with open('pdf_generator_fixed.py', 'wb') as f:
        f.write(fixed_data)
    print("Fixed file saved as pdf_generator_fixed.py")
    
    # Test if it can be imported
    try:
        with open('pdf_generator_fixed.py', 'r', encoding='utf-8') as f:
            content = f.read()
        print("\nSuccess! File is valid UTF-8")
        print("First 50 lines:")
        lines = content.split('\n')
        for i, line in enumerate(lines[:50]):
            print(f"{i+1}: {line}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Bad sequence not found")
    print("First 1000 bytes:")
    print(repr(data[:1000]))
