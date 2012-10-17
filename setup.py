from distutils.core import setup

setup(name='tulpenmanie',
      version='0.7.0',
      description='Markets client',
      url='https://github.com/3M3RY/tulpenmanie',
      author='Emery Hemingway',
      author_email='tulpenmanie@emery.neomailbox.net',
      packages=['tulpenmanie',
                'tulpenmanie.data',
                'tulpenmanie.exchange_modules',
                'tulpenmanie.model',
                'tulpenmanie.model.ot',
                'tulpenmanie.network',
                'tulpenmanie.ui',
                'tulpenmanie.ui.edit',
                'tulpenmanie.ui.transfer'],
      scripts=['scripts/tulpenmanie'],
      requires=['PyQt4.QtCore',
                'PyQt4.GtGui',
                'PyQt4.QtNetwork'],
      provides=['tulpenmanie']
      )
