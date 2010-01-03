# -*- mode: python -*-

# Linux: policy change with system libraries :
#   http://groups.google.com/group/PyInstaller/browse_thread/thread/dbe36a6fd985631b?hl=en#

GSDVIEWROOT = '..'
if sys.platform == 'darwin':
    GDALROOT = '/Libraries/Frameworks/GDALFramework/Current/unix'
    GDAL_DATA = os.path.join(GDALROOT, 'share', 'gdal')
    GDALADDO = os.path.join(GDALROOT, 'bin', 'gdaladdo')
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
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,

          # Packages resources: Qt4 UI files and images
          Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'ui'), 'ui',
               excludes=['.svn']),
          Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'images'), 'images',
               excludes=['.svn']),
          Tree(os.path.join(GSDVIEWROOT, 'gsdview', 'gdalbackend', 'ui'), 'ui',
               excludes=['.svn']),
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

          name=os.path.join(GSDVIEWROOT, 'dist', 'onefile', 'gsdview'),
          debug=False,
          strip=False,
          upx=True,
          console=1,  # @TODO: check
          icon=os.path.join(GSDVIEWROOT, 'doc', 'source', '_static',
                            'logo.ico'),
)

BUILD_BUNDLE = True
if sys.platform == 'darwin' and BUILD_BUNDLE:
    sys.path.insert(0, os.path.abspath(os.pardir))
    from gsdview import info
    app = BUNDLE(exe, appname=info.name, version=info.version) 
