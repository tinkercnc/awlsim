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

from awlsim.common.exceptions import *

from awlsim.core.instructions.main import * #+cimport
from awlsim.core.operatortypes import * #+cimport
from awlsim.core.operators import * #+cimport


class AwlInsn_TRUNC(AwlInsn): #+cdef

	__slots__ = ()

	def __init__(self, cpu, rawInsn=None, **kwargs):
		AwlInsn.__init__(self, cpu, AwlInsn.TYPE_TRUNC, rawInsn, **kwargs)
		self.assertOpCount(0)

	def run(self): #+cdef
#@cy		cdef S7StatusWord s

		s = self.cpu.statusWord
		accu1 = self.cpu.accu1.getPyFloat()
		try:
			accu1 = int(accu1)
			if accu1 > 2147483647 or accu1 < -2147483648: #@nocy
#@cy			if accu1 > 2147483647LL or accu1 < -2147483648LL:
				raise ValueError
		except (ValueError, OverflowError) as e:
			s.OV, s.OS = 1, 1
			return
		self.cpu.accu1.setDWord(accu1)
