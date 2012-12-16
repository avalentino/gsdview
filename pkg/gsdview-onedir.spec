# -*- mode: python -*-

# development mode:
#   http://www.mail-archive.com/pyinstaller@googlegroups.com/msg01421.html
# Linux: policy change with system libraries:
#   http://groups.google.com/group/PyInstaller/browse_thread/thread/dbe36a6fd985631b?hl=en#

try:
    from subprocess import check_output
except ImportError:
    def check_output(*popenargs, **kwargs):
        from subprocess import Popen, CalledProcessError, PIPE

        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = Popen(*popenargs, stdout=PIPE, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise CalledProcessError(retcode, cmd, output=output)
        return output

DEVELOPMENT_MODE = False
#DEVELOPMENT_MODE = True
EXTRA_QT_RESOURCES = []
GSDVIEWROOT = '..'

if sys.platform == 'darwin':
    GDALROOT = '/Library/Frameworks/GDAL.framework'
    GDAL_DATA = os.path.join(GDALROOT, 'Resources', 'gdal')
    GDALINFO = os.path.join(GDALROOT, 'unix', 'bin', 'gdalinfo')
    GDALADDO = os.path.join(GDALROOT, 'unix', 'bin', 'gdaladdo')
    ICONFILE = os.path.join(GSDVIEWROOT, 'pkg', 'GSDView.icns')
elif sys.platform[:3] == 'win':
    GDALROOT = r'c:\gdal170'
    GDAL_DATA = os.path.join(GDALROOT, 'data')
    GDALINFO = os.path.join(GDALROOT, 'bin', 'gdalinfo.exe')
    GDALADDO = os.path.join(GDALROOT, 'bin', 'gdaladdo.exe')
    ICONFILE = os.path.join(GSDVIEWROOT, 'doc', 'source', '_static', 'logo.ico')
else:
    # Standard unix
    #GDALROOT = '/usr'
    #GDAL_DATA = os.path.join(GDALROOT, 'share', 'gdal16')
    GDALROOT = check_output(['gdal-config', '--prefix']).strip()
    GDAL_DATA = check_output(['gdal-config', '--datadir']).strip()
    GDALINFO = os.path.join(GDALROOT, 'bin', 'gdalinfo')
    GDALADDO = os.path.join(GDALROOT, 'bin', 'gdaladdo')
    ICONFILE = os.path.join(GSDVIEWROOT, 'doc', 'source', '_static', 'logo.ico')

a = Analysis([os.path.join(GSDVIEWROOT, 'scripts', 'gsdview')],
             pathex=[GSDVIEWROOT],
             hookspath=['.'],
             excludes=['matplotlib', 'scipy', #'multiprocessing',
                       'Pyrex', '_tkinter', 'nose',
                       'PySide', 'PySide.QtCore', 'PySide.QtGui',
                       'PySide.QtSvg'])

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
          strip=None,
          upx=True,
          console=False,
          icon=ICONFILE,
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
               [(os.path.basename(GDALINFO), GDALINFO, 'DATA'),
                (os.path.basename(GDALADDO), GDALADDO, 'DATA'),
               ],
               Tree(os.path.join(GDAL_DATA), 'data'),

               strip=None,
               upx=True,
               name=os.path.join(GSDVIEWROOT, 'dist', 'gsdview'),
)

# Bundle sipport for onedir mode still incomplete
BUILD_BUNDLE = True
if sys.platform == 'darwin' and BUILD_BUNDLE:
    sys.path.insert(0, os.path.abspath(os.pardir))
    from gsdview import info
    app = BUNDLE(coll,
                 name=os.path.join(GSDVIEWROOT, 'dist', info.name + '.app'),
                 version=info.version,
                 icon='GSDView.icns')
