import zipfile
import xml.etree.ElementTree as ET

path = r'c:\Users\31897\Desktop\作业、实验报告批改案例\面向对象程序设计（Java）（作业）\对象与类作业-批改 - 副本.docx'

try:
    with zipfile.ZipFile(path, 'r') as z:
        names = z.namelist()
        print('=== ZIP CONTENTS ===')
        for n in names:
            print(f'  {n}')

        # Try to find document.xml
        for name in names:
            if 'document' in name.lower() and name.endswith('.xml'):
                content = z.read(name).decode('utf-8')
                print()
                print(f'=== {name} (first 5000 chars) ===')
                print(content[:5000])
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
