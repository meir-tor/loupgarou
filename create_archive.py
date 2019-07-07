import fnmatch
import os
import zipfile

# Collect .py files
matches = []
for root, dirnames, filenames in os.walk('AIWoof-master'):
    for filename in fnmatch.filter(filenames, '*.py'):
        matches.append(os.path.join(root, filename))
        
# Create .zip archive
zipf = zipfile.ZipFile('loupgarou.zip', 'w', zipfile.ZIP_DEFLATED)
for path in matches:
    zipf.write(path)
zipf.close()
