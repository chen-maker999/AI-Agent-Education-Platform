import olefile
import re
import struct

doc_path = r'c:\Users\31897\Desktop\作业、实验报告批改案例\面向对象程序设计（Java）（作业）\对象与类作业-批改.doc'

ole = olefile.OleFileIO(doc_path)

# Read WordDocument stream
wd_stream = ole.openstream('WordDocument')
wd_data = wd.stream('WordDocument')

# Also read 1Table
try:
    table_stream = ole.openstream('1Table')
    table_data = table_stream.read()
    print(f'1Table size: {len(table_data)} bytes')
except:
    table_data = b''
    print('No 1Table stream')

# Read SummaryInformation
try:
    summary = ole.openstream('\x05SummaryInformation')
    summary_data = summary.read()
    print(f'SummaryInfo size: {len(summary_data)} bytes')
    
    # Parse summary info
    import pythoncom
    try:
        from win32com.storagecon import *
        import pywintypes
        # Try to get text
        summary_ole = OleEmbeddedObject(summary_data)
    except:
        pass
except:
    pass

print(f'WordDocument size: {len(wd_data)} bytes')
print(f'First 100 bytes hex: {wd_data[:100].hex()}')

# Try to extract text using pattern matching
# Word .doc files store text as Pascal strings and raw text
# Let's try to find readable text

text_parts = []

# Try to decode as unicode
try:
    # Try UTF-16LE
    text = wd_data.decode('utf-16le', errors='ignore')
    # Filter readable text
    readable = []
    for line in text.split('\n'):
        cleaned = ''.join(c for c in line if c.isprintable() or c in '\r\n\t')
        if len(cleaned) > 3:
            readable.append(cleaned)
    if readable:
        print('\n=== UTF-16LE text (first 5000 chars) ===')
        result = '\n'.join(readable)
        print(result[:5000])
except Exception as e:
    print(f'UTF-16LE error: {e}')

# Try to find ANSI text
try:
    text = wd_data.decode('gbk', errors='ignore')
    readable = []
    for line in text.split('\n'):
        cleaned = ''.join(c for c in line if c.isprintable() or c in '\r\n\t')
        if len(cleaned) > 3:
            readable.append(cleaned)
    if readable:
        print('\n=== GBK text (first 5000 chars) ===')
        result = '\n'.join(readable)
        print(result[:5000])
except Exception as e:
    print(f'GBK error: {e}')

ole.close()
