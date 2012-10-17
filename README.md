# Tulpenmanie
A graphical markets client in PyQt4 that aims to provide a normalized 
trading experience across disparate markets, exchanges, and assets, with a 
GUI targeted at users with multi-monitor and tiling window managers.

## Supported Exchanges
 - [Bitstamp](https://www.bitstamp.net/)
 - [BTC-e](https://btc-e.com/)
 - [Campbx](https://campbx.com/)
 - [MtGox](https://mtgox.com/)
 - [VirWox](https://www.virwox.com?r=180bd)

## Dependencies
 - Python-2.7
 - PyQt4

## Install
    sudo python setup.py install

If you don't want to commit to a sudo, you can install to ~/.local

    python setup.py install --user
    # You'll need ~/.local/bin in your PATH or 
    # you'll have to run the command  ~/.local/bin/tulpenmanie

## Notes
### Getting started
Tulpenmanie makes no assumptions about what you trade, so you must first define
commodities, markets, and set exchange settings in the options->definitions
menu.

### balance display
Liquid balance is displayed, rather than total balance.
### request queuing
Requests are queue in the following descending priority:
 - order cancellation
 - ordering
 - account info
 - ticker requests, chosen at random between tickers on a given exchange

### Credential storage
Settings and API credentials are stored plain-text. On POSIX systems there are at
'~/.config/Emery Hemingway/tulpenmanie.conf' and on windows they are stored in 
the registry.

### Exchange Modules
#### CampBX
If you open a [CampBX](https://campbx.com/) account as a result of this program,
 support the author and receive a 10% lifetime discount on commissions by using 
this [referral url](https://campbx.com/register.php?r=P3hAnksjDmY).
Do note that a support ticket must be filed before API access enabled
by default. (But look into it, last I looked they do those cheap Dwolla 
transfers without the photo ID bullshit)

#### MtGox
The [MtGox](https://mtgox.com/) module uses HTTP POST methods rather than the 
streaming interface, streaming API support is planned, but not a high priority. 
You notice that the ask and bid buttons are disabled when first starting the 
application, this is because MtGox takes orders in whole integers, and the 
multiplication factor is requested at startup rather than stored locally.

### VirWoX
I'd like to give [VirWoX](https://www.virwox.com?r=180bd) an honorable mention 
as the bicoin exchange with the best API in my opinion. All relevant data is 
available over the API and all replies are in a consistant JSON format.

## Development Roadmap
 - [Open Transactions](https://github.com/FellowTraveler/Open-Transactions) 
   support
 - Modular and extensible charting with [Matplotlib](http://matplotlib.org/)
 - Websocket and Socket.IO streaming connections
 - Start pushing things down into C++ and SIP wrappers

## Disclaimer
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

## Support this project
Bitcoin: 1NKKQBSaQ6XMViwC46b4JCxGUiUp6EDZR5
