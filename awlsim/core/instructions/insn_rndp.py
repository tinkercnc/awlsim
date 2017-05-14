# -*- coding: utf-8 -*-
#
# AWL simulator - instructions
#
# Copyright 2012-2017 Michael Buesch <m@bues.ch>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from __future__ import division, absolute_import, print_function, unicode_literals
from awlsim.common.compat import *

from awlsim.common.datatypehelpers import *

from awlsim.core.instructions.main import * #+cimport
from awlsim.core.operators import * #+cimport


class AwlInsn_RNDP(AwlInsn): #+cdef

	__slots__ = ()

	def __init__(self, cpu, rawInsn=None, **kwargs):
		AwlInsn.__init__(self, cpu, AwlInsn.TYPE_RNDP, rawInsn, **kwargs)
		self.assertOpCount(0)

	def run(self): #+cdef
#@cy		cdef S7StatusWord s
#@cy		cdef double accu1

		s = self.cpu.statusWord
		accu1 = self.cpu.accu1.getPyFloat()
		try:
			rounded = int(accu1)
			if rounded >= 0 and\
			   not pyFloatEqual(float(rounded), accu1):
				rounded += 1
			if accu1 > 2147483647 or accu1 < -2147483648: #@nocy
#@cy			if accu1 > 2147483647LL or accu1 < -2147483648LL:
				raise ValueError
		except ValueError:
			s.OV, s.OS = 1, 1
			return
		self.cpu.accu1.setDWord(rounded)
