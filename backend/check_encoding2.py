with open('pdf_generator.py', 'rb') as f:
    data = f.read()
    print("First 200 bytes (raw):")
    print(repr(data[:200]))
    print("\n===Testing different encodings===")
    
    for encoding in ['utf-8', 'shift-jis', 'euc-jp', 'iso-2022-jp', 'cp932']:
        try:
            with open('pdf_generator.py', 'r', encoding=encoding) as f:
                lines = f.readlines()
                print(f"\n{encoding} - SUCCESS - First 5 lines:")
                for i, line in enumerate(lines[:5]):
                    print(f"  {i+1}: {line[:80]}", end='')
                if len(lines[0]) > 80:
                    print("...")
        except Exception as e:
            print(f"\n{encoding} - FAILED: {e}")
