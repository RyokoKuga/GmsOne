from setuptools import setup

APP = ['main.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'icon.icns',  # icns file
    'packages': ['customtkinter', 'PIL'],
    'includes': ['packaging', 'tkinter'],
    'plist': {
        'CFBundleName': "GmsOne",
        'CFBundleDisplayName': "GmsOne",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHighResolutionCapable': True,
        'PyOptions': '-O',
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)