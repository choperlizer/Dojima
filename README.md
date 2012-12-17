# Dōjima

THIS IS AN UNFINISHED OPEN TRANSACTIONS GUI CLIENT.
Hopefully there is some decent reusable Qt code for
dealing with OT in this mess. At present I wouldn't
trust it not to defenestrate your assets.

## The name
This is a rewrite of Tulpenmanie, a Bitcoin exchange client I made a bit ago.
I thought it best to to change the name because I don't believe algorithmic 
and private currencies will form bubbles as much as state currencies do. The 
inflation of state currencies is an incentive to invest, and the incentive to 
adopt competitive currencies is that they do not inflate. Bubbles may form in
new currencies but hopefully the currencies themselves will encourage less
malinvestment.

## Dependencies
 - Python-2.7
 - Matplotlib
 - PyQt4
 - >Open Transactions-0.87.g with Python SWIG wrapper

## Install
Unfortunatly I have not figured out how to get this thing to run from
within the repo, so it'll have to be installed with setup.py:
    sudo python setup.py install

If you don't want to commit to a sudo, you can install to ~/.local:
    python setup.py install --user
    # You'll need ~/.local/bin in your PATH or 
    # you'll have to run the command  ~/.local/bin/dojima

## Disclaimer
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

## Support this project
Bitcoin: 1NKKQBSaQ6XMViwC46b4JCxGUiUp6EDZR5
