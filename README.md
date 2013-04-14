# Dōjima

**This program is distributed in the hope that it will be useful,**
**but WITHOUT ANY WARRANTY; without even the implied warranty of**
**MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the**
**GNU General Public License for more details.**

This is a PyQt Bitcoin exchange client. It is still a little rough 
around the edges but it works. 

## Supported Exchanges

 - [Bitstamp](https://www.bitstamp.net/)
 - [BTC-e](https://btc-e.com/)
 - [Campbx](https://campbx.com/) - [referral url](https://campbx.com/register.php?r=P3hAnksjDmY)
 - [Open Transactions](https://github.com/FellowTraveler/Open-Transactions) *in progress*

## Dependencies
 - Python-3.1
 - Matplotlib
 - PyQt4

## Install
I have not figured out how to get this thing to run from
within the repo, so it'll have to be installed with setup.py:

    sudo python setup.py install

If you don't want to commit to a sudo, you can install to ~/.local:

    python setup.py install --user
    # You'll need ~/.local/bin in your PATH or 
    # you'll have to run the command  ~/.local/bin/dojima

### Gentoo
  layman -a bitcoin && emerge dojima

### OS X
Probably works, but too expensive to test.

### Ubuntu
It should work on Ubuntu in theory, but only Ubuntu raring whatever.
I hear debian doesn't have recent enough packages for matplotlib.

### Windows
It works in Windows, but it takes a lot of work. I could make an 
installer or standalone EXE but I hate windows.

## Donate
Bitcoin: 1NKKQBSaQ6XMViwC46b4JCxGUiUp6EDZR5
