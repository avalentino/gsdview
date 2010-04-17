# -*- mode: python -*-

# development mode:
#   http://www.mail-archive.com/pyinstaller@googlegroups.com/msg01421.html
# Linux: policy change with system libraries :
#   http://groups.google.com/group/PyInstaller/browse_thread/thread/dbe36a6fd985631b?hl=en#

DEVELOPMENT_MODE = False
#DEVELOPMENT_MODE = True
EXTRA_QT_RESOURCES = []
GSDVIEWROOT = '..'
if sys.platform == 'darwin':
    GDALROOT = '/Library/Frameworks/GDAL.framework'
    GDAL_DATA = os.path.join(GDALROOT, 'Resources', 'gdal')
    GDALADDO = os.path.join(GDALROOT, 'unix', 'bin', 'gdaladdo')
    # Workaround fo pyinstaller bug #157 (http://www.pyinstaller.org/ticket/157)
    EXTRA_QT_RESOURCES = Tree('/Library/Frameworks/QtGui.framework/Resources/qt_menu.nib', os.path.join('Resources', 'qt_menu.nib'))
    #EXTRA_QT_RESOURCES = Tree(os.path.join(QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.LibrariesPath),
    #                          'QtGui.framework/Resources/qt_menu.nib'), os.path.join('Resources', 'qt_menu.nib'))
elif sys.platform[:3] == 'win':
    GDALROOT = r'c:\gdal170'
    GDAL_DATA = os.path.join(GDALROOT, 'data')
    GDALADDO = os.path.join(GDALROOT, 'bin', 'gdaladdo.exe')
else:
    # Standard unix
    GDALROOT = '/usr'
    GDAL_DATA = os.path.join(GDALROOT, 'share', 'gdal15')
    GDALADDO = os.path.join(GDALROOT, 'bin', 'gdaladdo')

a = Analysis([os.path.join(HOMEPATH,'support', '_mountzlib.py'),
              os.path.join(HOMEPATH,'support', 'useUnicode.py'),
              os.path.join(GSDVIEWROOT, 'scripts', 'gsdview'),
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

               # Packages resources: Qt4 UI files and images
               Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'ui'), 'ui',
                    excludes=['.svn']),
               Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'images'), 'images',
                    excludes=['.svn']),
               Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'gdalbackend', 'ui'),
                    'ui', excludes=['.svn']),
               Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'gdalbackend', 'images'),
                    'images', excludes=['.svn']),

               # Plugins
               Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'plugins'), 'plugins',
                    excludes=['.svn']),

               # Docs
               [('README.txt', os.path.join(GSDVIEWROOT, 'README.txt'), ''),
                ('LICENSE.txt', os.path.join(GSDVIEWROOT, 'LICENSE.txt'), ''),
               ],
               Tree(os.path.join(GSDVIEWROOT, 'doc', 'html'),
                    os.path.join('docs', 'html')),

               # GDAL tools and data
               [(os.path.basename(GDALADDO), GDALADDO, 'DATA'),],
               Tree(os.path.join(GDAL_DATA), 'data'),

               # Workaround fo pyinstaller bug #157 (http://www.pyinstaller.org/ticket/157)
               EXTRA_QT_RESOURCES,

               strip=False,
               upx=True,
               name=os.path.join(GSDVIEWROOT, 'dist', 'gsdview'),
)

BUILD_BUNDLE = True
if sys.platform == 'darwin' and BUILD_BUNDLE:
    sys.path.insert(0, os.path.abspath(os.pardir))
    from gsdview import info
    app = BUNDLE(exe, appname=info.name, version=info.version)

