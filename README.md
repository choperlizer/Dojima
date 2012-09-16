# Tulpenmanie
A commodities market client in PyQt4

## Supported Markets
 - [Bitstamp](https://www.bitstamp.net/)
 - [BTC-e](https://btc-e.com/)
 - [Campbx](https://campbx.com/)
 - [MtGox](https://mtgox.com/)

### Module notes
#### CampBX
If you open a CampBX account as a result of this program, support the 
author and receive a 10% lifetime discount on commissions by using 
this [referral url](https://campbx.com/register.php?r=P3hAnksjDmY).

#### MtGox
The MtGox module uses POST methods rather than websocket interface. 
Websocket support will be investigated as the program matures. MtGox specifies 
that API calls should be atleast ten seconds apart, so this program spaces 
them by five. Attempting to reduce this period may trigger anti-DOS
measures. You may also notice that the ask and bid buttons are disabled when
first starting the application, this is because MtGox takes orders in whole 
integers, and tuplenmanie requests the multiplication factor from MtGox at 
startup.

## Dependencies
 - Python-2.7
 - PyQt4

## Install
    sudo python setup.py install

If you don't want to commit to a sudo, you can install to ~/.local

    python setup.py install --user
    # You'll need ~/.local/bin in your PATH or 
    # you'll have to run the command  ~/.local/bin/tuplenmanie

## Notes
### Credential storage
Settings and API credentials are stored at 
'~/.config/Emery Hemingway/tulpenmanie.conf' on POSIX systems. On windows they're
stored in the registry.

### Getting started
Tulpenmanie makes no assumptions about what you trade, so you must first define
commodities, markets, and set exchange settings in the options->definitions
menu.
### balance display
Liquid balance is displayed, rather than total balance.
### request queueing
Requests are queue in the following descending priority:
 - order cancelation
 - ordering
 - account info
 - ticker requests, chosen at random between tickers per-exchange

## Disclaimer
To reiterate from the GPL:
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

## Support this project
Bitcoin: 1NKKQBSaQ6XMViwC46b4JCxGUiUp6EDZR5
