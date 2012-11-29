# -*- coding:utf-8 -*-
import sys
sys.path.append('./src')
from distutils.core import setup
from xiwangshe import __version__

setup(name='xiwangshe',
      version=__version__,
      description='基于UDP的可靠通信协议',
      long_description=open("README.md").read(),
      author='onlytiancai',
      author_email='onlytiancai@gmail.com',
      packages=['xiwangshe'],
      package_dir={'xiwangshe': 'src/xiwangshe'},
      package_data={'xiwangshe': ['stuff']},
      license="Public domain",
      platforms=["any"],
      url='https://github.com/onlytiancai/xiwangshe')
