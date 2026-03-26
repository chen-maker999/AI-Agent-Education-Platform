import zipfile
import io

# The actual .doc file
doc_path = r'c:\Users\31897\Desktop\作业、实验报告批改案例\面向对象程序设计（Java）（作业）\对象与类作业-批改.doc'
docx_path = r'c:\Users\31897\Desktop\作业、实验报告批改案例\面向对象程序设计（Java）（作业）\对象与类作业-批改 - 副本.docx'

# Try docx - doesn't work (it's a renamed binary doc)
# Try to extract text from .doc using various methods

# Method 1: Try olefile
try:
    import olefile
    print('olefile available')
    ole = olefile.OleFileIO(doc_path)
    streams = ole.listdir()
    print(f'OLE streams: {streams}')
    ole.close()
except ImportError:
    print('olefile not available')
except Exception as e:
    print(f'olefile error: {e}')

# Method 2: Try textract
try:
    import textract
    text = textract.process(doc_path)
    print('textract result:')
    print(text.decode('utf-8', errors='replace')[:5000])
except ImportError:
    print('textract not available')
except Exception as e:
    print(f'textract error: {e}')

# Method 3: Try subprocess with antiword or catdoc
import subprocess
try:
    result = subprocess.run(['catdoc', '-d', doc_path], capture_output=True, text=True)
    print('catdoc result:')
    print(result.stdout[:3000])
    print(result.stderr[:500])
except FileNotFoundError:
    print('catdoc not available')
except Exception as e:
    print(f'catdoc error: {e}')

# Method 4: Try python-docx2txt which can handle some doc files
try:
    import docx2txt
    text = docx2txt.process(doc_path)
    print('docx2txt result:')
    print(text[:5000])
except ImportError:
    print('docx2txt not available')
except Exception as e:
    print(f'docx2txt error: {e}')
