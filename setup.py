from distutils.core import setup

setup(name='tulpenmanie',
      version='0.6.0',
      description='Graphical speculation platform',
      url='https://github.com/3M3RY/tulpenmanie',
      author='Emery Hemingway',
      author_email='tulpenmanie@emery.neomailbox.net',
      packages=['tulpenmanie',
                'tulpenmanie.exchange_modules',
                'tulpenmanie.model',
                'tulpenmanie.network',
                'tulpenmanie.ui',
                'tulpenmanie.ui.transfer'],
      scripts=['scripts/tulpenmanie'],
      requires=['PyQt4.QtCore',
                'PyQt4.GtGui',
                'PyQt4.QtNetwork'],
      provides=['tulpenmanie']
      )
