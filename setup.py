from distutils.core import setup

setup(name='tulpenmanie',
      version='0.3.1',
      description='Graphical commodity market client.',
      url='https://github.com/3M3RY/tulpenmanie',
      author='Emery Hemingway',
      author_email='tulpenmanie@emery.neomailbox.net',
      packages=['tulpenmanie',
                'tulpenmanie.model',
                'tulpenmanie.provider_modules',
                'tulpenmanie.ui'],
      scripts=['scripts/tulpenmanie'],
      requires=['PyQt4.QtCore',
                'PyQt4.GtGui',
                'PyQt4.QtNetwork'],
      provides=['tulpenmanie']
      )
