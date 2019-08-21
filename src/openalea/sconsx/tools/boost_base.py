# -*-python-*-
#--------------------------------------------------------------------------------
#
#        OpenAlea.SConsX: SCons extension package for building platform
#                        independant packages.
#
#       Copyright 2006-2009 INRIA - CIRAD - INRA
#
#       File author(s): Christophe Pradal <christophe.prada@cirad.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
#--------------------------------------------------------------------------------
""" Boost.Python configure environment. """

__license__ = "Cecill-C"
__revision__ = "$Id$"

import os, sys, glob, re
from openalea.sconsx.config import *

from os.path import join
import sys

reg  = r".*boost.*([0-9]\.[0-9][0-9]\.?[0-9]?).*"
regc = re.compile(reg)

#sharedlib_ext = {'linux2' : 'so', 'win32' : 'dll', 'cygwin' : 'dll', 'darwin' : 'dylib', 
#                 'os2' : 'dll', 'os2emx' : 'dll', 'riscos' : 'so'}

def get_default_boost_libs_suffix(path, libname='boost_python'):
    import glob
    boost_libs_suffix=None
    bp = glob.glob(os.path.join(path,'*'+libname+'*.*'))
    if not bp is None and len(bp) > 0:
        bp = os.path.basename(bp[0])
        boost_libs_suffix = bp[bp.index(libname)+len(libname):bp.index('.')]
    return boost_libs_suffix



class BoostBase:
    def __init__(self, config):
        self.name = self.__class__.__name__.lower()
        self.config = config
        self._default = {}
        self.__usingEgg = False

    def depends(self):
        deps = []
        if isinstance(platform, Posix):
            deps.append('pthread')
        return deps

    def default(self):
        self._default['libs_suffix'] = '$compiler_libs_suffix'
        self._default['flags'] = ''
        self._default['defines'] = ''

        isPosix = isinstance(platform, Posix)



        # -- lets now look for decent flags --
        self._default['flags'] = self.get_default_flags()
        self._default['defines'] = self.get_default_defines()

        # -- lets now look for decent include dirs --
        if CONDA_ENV:
            self._default['include'] = join(CONDA_LIBRARY_PREFIX, 'include')
            self._default['libpath'] = join(CONDA_LIBRARY_PREFIX, 'lib')
            detectedsuffix = get_default_boost_libs_suffix(self._default['libpath'], libname=self.name) 
            if detectedsuffix:
                self._default['libs_suffix'] = detectedsuffix 
            self.__usingEgg = False
        else:
            try:
                # Try to use openalea egg
                from openalea.deploy import get_base_dir
                try:
                    base_dir = get_base_dir("boost")
                except:
                    base_dir = get_base_dir("boostpython")
                self._default['include'] = join(base_dir, 'include')
                self._default['libpath'] = join(base_dir, 'lib')
                self.__usingEgg = True
            except:
                try:
                    import openalea.config as conf
                    self._default['include'] = conf.include_dir
                    self._default['libpath'] = conf.lib_dir

                except ImportError as e:
                    defdir = detect_posix_project_installpath('include/boost')
                    self._default['include'] = join(defdir,'include')
                    self._default['libpath']     = join(defdir,'lib')
                    detectedsuffix = get_default_boost_libs_suffix(self._default['libpath'], libname=self.name) 
                    if detectedsuffix:
                        self._default['libs_suffix'] = detectedsuffix


    def get_default_flags(self):
        return ''

    def get_default_defines(self):
        return ''

    def option( self, opts):

        self.default()

        opts.AddVariables(
            PathVariable('boost_includes',
                            'boost include files',
                            self._default['include']),

            PathVariable(('boost_libpath','boost_lib'),
                            'boost libraries path',
                            self._default['libpath']),

            (self.name + '_flags',
              self.name + ' compiler flags',
              self._default['flags']),

            (self.name + '_defines',
              self.name + ' defines',
              self._default['defines']),

            (self.name + '_libs_suffix',
              self.name + ' library suffix name like -vc80-mt or -gcc',
              self._default['libs_suffix']),

            BoolVariable('WITH_BOOST',
              'Specify whether you want to compile your project with boost', True)
      )


    def update(self, env):
        """ Update the environment with specific flags """
        if env['WITH_BOOST']:
            env.AppendUnique(CPPPATH=[env['boost_includes']])
            env.AppendUnique(LIBPATH=[env['boost_libpath']])
            env.Append(CPPDEFINES='$%s_defines'%(self.name,))
            env.Append(CPPFLAGS='$%s_flags'%(self.name,))

            #boost > 1.43 changed naming scheme for mingw/cygwin.
            if env['compiler'] == 'mingw' or platform==Cygwin:
                if not self.__usingEgg: # ---- get version, from user boost or system
                    boostLibs = glob.glob(join(env['boost_lib'],'libboost*'))
                    version   = None
                    #find versions in there
                    for lib in boostLibs:
                        res = regc.search(lib)
                        if res and len(res.groups()):
                            version = res.groups()[0]
                            break
                else: #get version, from egg
                    from openalea.deploy import get_metainfo
                    try:
                        version = get_metainfo("boost", "version")
                    except:
                        version = get_metainfo("boostpython", "version")

                periods = version.count(".")
                if periods == 1:
                    maj, min = list(map(int, version.split(".")))
                    patch = 0
                elif periods == 2:
                    maj, min, patch = list(map(int, version.split(".")))
                else:
                    raise Exception("Cannot determine the version of boost.")
                # ---- OK we have the version numbers (maj, min, patch) and string (version)

                version = version.replace(".", "_")

                if maj >= 1 and min >= 43 :
                    boost_name= self.name +".dll" #on Windows mingw/cygwin we now only support boost compilations with --layout=system
                else:
                    boost_name= self.name + env[self.name + '_libs_suffix']
            else:
                boost_name= self.name + env[self.name + '_libs_suffix']
            env.AppendUnique(LIBS=[boost_name])


    def configure(self, config):
        return



