import olefile
import re

doc_path = r'c:\Users\31897\Desktop\作业、实验报告批改案例\面向对象程序设计（Java）（作业）\对象与类作业-批改.doc'

ole = olefile.OleFileIO(doc_path)
wd_data = ole.openstream('WordDocument').read()
ole.close()

print(f'WordDocument size: {len(wd_data)} bytes')

# Try GBK decode first (Chinese Windows default)
for encoding in ['gbk', 'utf-16le', 'cp1252', 'latin-1']:
    try:
        text = wd_data.decode(encoding, errors='ignore')
        # Filter for readable lines
        lines = []
        for line in text.split('\n'):
            cleaned = ''.join(c for c in line if c.isprintable() or c in '\r\n\t')
            if len(cleaned) > 5:
                lines.append(cleaned)
        if lines:
            result = '\n'.join(lines)
            print(f'\n=== {encoding} text (first 8000 chars) ===')
            print(result[:8000])
            print('=== END ===')
            break
    except Exception as e:
        print(f'{encoding} error: {e}')
