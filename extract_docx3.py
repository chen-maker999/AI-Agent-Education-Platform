import os
import zipfile

# List all files in the directory
desk_path = r'c:\Users\31897\Desktop\作业、实验报告批改案例\面向对象程序设计（Java）（作业）'
if os.path.exists(desk_path):
    print('Files in directory:')
    for f in os.listdir(desk_path):
        full_path = os.path.join(desk_path, f)
        size = os.path.getsize(full_path)
        print(f'  {f} ({size} bytes)')
        
        if f.endswith('.docx'):
            try:
                with zipfile.ZipFile(full_path, 'r') as z:
                    names = z.namelist()
                    print(f'    ZIP contents: {names}')
            except Exception as e:
                print(f'    Error: {e}')
        elif f.endswith('.doc'):
            with open(full_path, 'rb') as fobj:
                header = fobj.read(8)
                print(f'    Binary header: {header}')
else:
    print(f'Directory not found: {desk_path}')
    
    # Try alternate path
    alt = r'C:\Users\31897\Desktop'
    print(f'\nFiles on Desktop:')
    for item in os.listdir(alt):
        if '作业' in item or '批改' in item or 'Java' in item:
            print(f'  {item}')
