# Dōjima

**This program is distributed in the hope that it will be useful,**
**but WITHOUT ANY WARRANTY; without even the implied warranty of**
**MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the**
**GNU General Public License for more details.**

This is a PyQt Bitcoin exchange client. It is still a little rough 
around the edges but it works. 

![screenshot](http://image.bayimg.com/b7560fe98133c157eeff5cfcf767f2b2dc0815a0.jpg)

## Rationale
I think trading through a browser sucks. With Dōjima you just run 
the client, bring up the market you want, and punch in orders. 
No logging in, no images to load.

I would very much like to support exchanges running 
[Open Transactions](https://github.com/FellowTraveler/Open-Transactions).
The internal structure of Dōjima was rebuilt for the 
purposes of Open Transactions, and support was about half done but
that is on hold for now until I can put together a general purpose 
Qt API wrapper for OT, rather than hack around some issues with the
Python GIL and interactivity.

## Supported Exchanges

 - [Bitstamp](https://www.bitstamp.net/)
 - [BTC-e](https://btc-e.com/)
 - [Campbx](https://campbx.com/) - [referral url](https://campbx.com/register.php?r=P3hAnksjDmY)

## Dependencies
 - Python-3.1
 - Matplotlib
 - PyQt4

## Issues
 - Passwords and API keys are stored plaintext.
 - Requests and responses are not logged graphically which may be
   confusing, but are printed to Standard Error. Run **dojima -v**
   in a terminal to see them.

## Install
I have not figured out how to get this thing to run from
within the repo, so it'll have to be installed with setup.py:

    sudo python3 setup.py install

If you don't want to commit to a sudo, you can install to ~/.local:

    python setup.py install --user
    # You'll need ~/.local/bin in your PATH or 
    # you'll have to run the command  ~/.local/bin/dojima

### Gentoo
    layman -a bitcoin && emerge dojima

### OS X
Probably works, but you'll have to manually install the dependecies.

### Ubuntu
    sudo apt-get instal python3-matplotlib python3-pyqt4
    git clone git@github.com:3M3RY/Dojima.git dojima
    cd dojima
    sudo python3 setup.py install

### Arch Linux
    sudo pacman -Sy python-pyqt4 python-matplotlib
    git clone git@github.com:3M3RY/Dojima.git dojima
    cd dojima
    sudo python3 setup.py install

### Windows
It works on windows, I've tested it. But the thing is installing 
Linux on your computer, and then installing this program is easier 
and than it is to install it on windows.

## Donate
Bitcoin: 1NKKQBSaQ6XMViwC46b4JCxGUiUp6EDZR5




*"This thing is pretty fun if you think of it as a game"* - Emery
