from distutils.core import setup

setup(name='dojima',
      version='0.0.1',
      description='Markets client',
      url='https://github.com/3M3RY/Dojima',
      author='Emery Hemingway',
      author_email='emery@fuzzlabs.org',
      packages=['dojima',
                'dojima.data',
                'dojima.exchange_modules',
                'dojima.model',
                'dojima.model.ot',
                'dojima.network',
                'dojima.ot',
                'dojima.ui',
                'dojima.ui.edit',
                'dojima.ui.ot',
                'dojima.ui.transfer'],
      scripts=['scripts/dojima'],
      requires=['matplotlib',
                'numpy',
                'PyQt4.QtCore',
                'PyQt4.GtGui',
                'PyQt4.QtNetwork'],
      provides=['dojima']
      )
