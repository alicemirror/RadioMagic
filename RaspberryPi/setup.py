#
# Cytonize the samplerbox audio engine for Python 3
#
# E.M., September 2020
#
# Important note on compiling .pyx files with Python 3 on the Raspbian
#
# 1. Install Cython with
#       $>pip3 install cython
# 2. Check that the installed version if 2.29 or higher, with the command $>cython -V
#       If Cython was already installed with a previous version, upgrade Cython for Python 3
#       to the last available version in the repository with the command
#       $>pip3 install --upgrade cython
#       Check the version again.
# 3. Add the comment
#       # cython: language_level=3
#       special setting in the comments on top of the pyx source
#       This set the language level of the compiler globally for all the sources
#       If you are compiling multiple sources, and only some of these are Python 3, instead,
#       you should use the settings for language level only for those sources.
#       For more details read the Cyton documentations:
#       https://cython.readthedocs.io/en/latest/src/userguide/migrating_to_cy30.html?highlight=python%203
# 4. If you need to import the C libraries of numpy there is a workaound that should
#       be applied to make the compilation working in the SPECIFIC CASE OF RASPBERRY PI if during the compilation
#       you get an error like
#       libf77blas.so.3: cannot open shared object file: No such file or directory
#       at the end of a series of compilation errors that involves numpy.
#       As described in the Numpy troubleshooting documentation
#       https://numpy.org/devdocs/user/troubleshooting-importerror.html
#       this is due to a missing library that should be installed from the Raspbian repositories with the command
#       $>sudo apt-get install libatlas-base-dev
#       This issue should be avoided also installing numpy with the Raspbian if the version if recent. Try before
#       with Buster distro or next ones, with the command
#       $>pip3 uninstall numpy
#       $>sudo apt install python3-numpy
#
# WARNING! Sometimes, the numpy error does not appear if compiling with setup.py. In this case, just try the manual
# coompilation from the Python console. The mentioned error at the end of a list of errors will happen when adding
# >>>import numpy
#
# Happy Cyton with Python (3)!
#
# cython: language_level=3
from distutils.core import setup
from Cython.Build import cythonize
import numpy

setup(ext_modules = cythonize("samplerbox_audio.pyx"), include_dirs=[numpy.get_include()])