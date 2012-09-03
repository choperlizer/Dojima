# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: $

EAPI=4

PYTHON_DEPENDS="2"
SUPPORT_PYTHON_ABIS="1"
RESTRICT_PYTHON_ABIS="2.4"

inherit eutils distutils

DESCRIPTION="Graphical commodity market client."
#HOMEPAGE="http://foo.example.org/"
SRC_URI="ftp://foo.example.org/${P}.tar.bz2"


LICENSE="GPL-3"
SLOT="0"
KEYWORDS="~x86 ~amd64"
IUSE=""

#RESTRICT="test"

RDEPEND="dev-python/PyQt4"
DEPEND="${RDEPEND}"
