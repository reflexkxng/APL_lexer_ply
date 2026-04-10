#!/bin/bash
echo "Building NovaLang executable..."
echo "Checking if PyInstaller is installed... :)"
if ! python -c "import PyInstaller" &> /dev/null
then
    echo "PyInstaller is not installed. Installing it now..."
    python -m pip install pyinstaller
fi
python -m PyInstaller --clean NovaLang.spec
cp .env dist/
echo "Build complete. Executable and .env can be found in the dist/ directory. :)"
