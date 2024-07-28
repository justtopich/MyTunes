# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
datas = [
    ('CHANGES.md', 'docs')
]


a = Analysis(['myTunes\\main.py'],
             pathex=['./myTunes'],
             binaries=[],
             datas=datas,
             hiddenimports=['win32timezone', 'pkg_resources.py2_warn'],
             hookspath=[],
             runtime_hooks=[],
			 #excludes=[],
             excludes=['dummy_thread', 'setuptools', 'cryptography', 'lib2to3', '_cffi_backend'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='MyTunes',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          windowed=True,
		  icon='myTunes/resource/icon64.ico',
		  version='version.txt'
)
