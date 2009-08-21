# -*- mode: python -*-

# development mode:
#   http://www.mail-archive.com/pyinstaller@googlegroups.com/msg01421.html
# Linux: policy change with system libraries :
#   http://groups.google.com/group/PyInstaller/browse_thread/thread/dbe36a6fd985631b?hl=en#

DEVELOPMENT_MODE = False
#DEVELOPMENT_MODE = True
GSDVIEWROOT = '..'

a = Analysis([os.path.join(HOMEPATH,'support', '_mountzlib.py'),
              os.path.join(HOMEPATH,'support', 'useUnicode.py'),
              os.path.join(GSDVIEWROOT, 'gsdviewer'),
             ],
             pathex=[GSDVIEWROOT],
             hookspath=['.'],
             excludes=['matplotlib', 'scipy', #'multiprocessing',
                       'Pyrex', '_tkinter', 'nose'])

project_files = []
if DEVELOPMENT_MODE:
    project_files.extend(a.pure)
    #for dst, src, type_ in a.pure:
    #    pathlen = len(dst.split('.'))
    #    dstpath = src.split(os.path.sep)[-pathlen:]
    #    dstpath = os.path.sep.join(dstpath)
    #    project_files.append((dstpath, src, type_))
    while a.pure:
        a.pure.pop()

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build', 'pyi.'+sys.platform, 'gsdview', 'gsdview'),
          debug=False,
          strip=False,
          upx=True,
          console=1,
          icon=os.path.join(GSDVIEWROOT, 'doc', 'source', '_static',
                            'logo.ico'),
)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               project_files,

               # Qt4 UI files
               Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'ui'), 'ui',
                    excludes=['.svn']),
               Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'gdalbackend', 'ui'),
                    'ui', excludes=['.svn']),

               # Plugins
               Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'plugins'), 'plugins',
                    excludes=['.svn']),

               # Docs
               [('README.txt', os.path.join(GSDVIEWROOT, 'README.txt'), ''),
                ('LICENSE.txt', os.path.join(GSDVIEWROOT, 'LICENSE.txt'), ''),
               ],
               Tree(os.path.join(GSDVIEWROOT, 'doc', 'html'),
                    os.path.join('docs', 'html')),

               # GDAL tools and data @TODO: make it cross platform
               #[('gdaladdo.exe', os.path.join(GDALROOT, 'bin', 'gdaladdo.exe'), 'DATA'),
               #],
               #Tree(os.path.join(GDALROOT, 'data'), 'data'),

               strip=False,
               upx=True,
               name=os.path.join(GSDVIEWROOT, 'dist', 'gsdview'),
)
