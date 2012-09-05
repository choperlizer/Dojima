# Tulpenmanie
A commodities market client in PyQt4

## Supported Markets
 - BTC-e
 - Campbx
 - MtGox

### Module notes
#### CampBX
If you open a CampBX account as a result of this program, support the 
author and receive a 10% lifetime discount on commissions by using 
this [referral url](https://campbx.com/register.php?r=P3hAnksjDmY).

#### MtGox
The MtGox module uses POST methods rather than websocket interface. 
Websocket support will be investigated as the program matures. MtGox specifies 
that API calls should be atleast ten seconds apart, so this program spaces 
them by five. Attempting to reduce the inter-call period may trigger anti-DOS
measures.

## Dependencies
 - Python-2.7
 - PyQt4

## Install
sudo python setup.py install

## Getting started
Tulpenmanie makes no assumptions about what you trade, so you must first define
commodities and markets in the options->markets menu. After a market is defined,
set exchange and account settings in the option->providers menu. At this time 
the program must be restart for any new settings to take effect.

## Known Issues
Watching multiple markets with the same BTC-e account may cause problems. This 
is becasue of race condition between account object authentication nonces, a 
fix is in progress.

## Donations
Bitcoin: 1NKKQBSaQ6XMViwC46b4JCxGUiUp6EDZR5
