import chardet

with open('pdf_generator.py', 'rb') as f:
    data = f.read()
    result = chardet.detect(data)
    print(f"Encoding: {result['encoding']}")
    print(f"Confidence: {result['confidence']}")
    
# Try to read with detected encoding
try:
    with open('pdf_generator.py', 'r', encoding=result['encoding']) as f:
        lines = f.readlines()
        print("\n=== First 30 lines ===")
        for i, line in enumerate(lines[:30]):
            print(f"{i+1}: {line}", end='')
except Exception as e:
    print(f"Error reading file: {e}")
