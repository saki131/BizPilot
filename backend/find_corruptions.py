# Find all corrupted byte sequences in the file
with open('pdf_generator.py', 'rb') as f:
    data = f.read()

# Look for patterns like: valid UTF-8 followed by 'E' (which breaks the sequence)
# Common pattern: \xE? (incomplete UTF-8 multibyte) followed by ASCII 'E'

print("Searching for corrupted sequences...")
print("=" * 60)

# Find sequences like: \xE1 followed by non-continuation byte
i = 0
corruptions = []
while i < len(data):
    byte = data[i]
    # Check for UTF-8 multi-byte starters
    if byte & 0xE0 == 0xC0:  # 2-byte sequence starter (110x xxxx)
        if i + 1 < len(data):
            next_byte = data[i + 1]
            if next_byte & 0xC0 != 0x80:  # Not a continuation byte (should be 10xxxxxx)
                corruptions.append((i, data[max(0, i-20):min(len(data), i+30)]))
    elif byte & 0xF0 == 0xE0:  # 3-byte sequence starter (1110 xxxx)
        if i + 1 < len(data):
            next_byte = data[i + 1]
            if next_byte & 0xC0 != 0x80:
                corruptions.append((i, data[max(0, i-20):min(len(data), i+30)]))
        if i + 2 < len(data):
            next_byte2 = data[i + 2]
            if next_byte2 & 0xC0 != 0x80:
                corruptions.append((i, data[max(0, i-20):min(len(data), i+30)]))
    i += 1

print(f"Found {len(corruptions)} potential corruptions:")
for pos, context in corruptions[:20]:  # Show first 20
    print(f"\nPosition {pos}:")
    print(f"  Context: {repr(context)}")
    
    # Try to show line number
    line_num = data[:pos].count(b'\n') + 1
    print(f"  Approximate line: {line_num}")
