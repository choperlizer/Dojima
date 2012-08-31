from distutils.core import setup

setup(name='tulpenmanie',
      version='0.1.0',
      description='Graphical commodity market client.',
      author='Emery Hemingway',
      author_email='tulpenmanie@emery.neomailbox.net',
      packages=['tulpenmanie',
                'tulpenmanie.model',
                'tulpenmanie.providers',
                'tulpenmanie.ui'],
      requires=['PyQt4.QtCore',
                'PyQt4.GtGui',
                'PyQt4.QtNetwork'],
      provides=['tuplenmanie']
      )
