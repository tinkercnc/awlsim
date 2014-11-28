# -*- coding: utf-8 -*-
#
# AWL simulator - Asynchronous code validator
#
# Copyright 2014 Michael Buesch <m@bues.ch>
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

import multiprocessing

from awlsim.core import *


def _awlValidatorWorker(text):
	# Try to parse and translate the text.
	# On error return the erratic line numbers.
	try:
		p = AwlParser()
		p.parseText(text)
		s = AwlSim()
		s.getCPU().enableExtendedInsns(True)
		s.load(p.getParseTree())
	except AwlSimError as e:
		lineNr = e.getLineNr()
		if lineNr is not None:
			lineNr -= 1
			return ( lineNr, )
	except UnicodeError as e:
		pass
	return ()

class AwlValidatorResult(object):
	def __init__(self, mpAsync):
		self.__mpAsync = mpAsync

	def ready(self):
		return self.__mpAsync.ready()

	def getErrLines(self):
		return self.__mpAsync.get(None)

class AwlValidator(object):
	def __init__(self, maxNrWorkers=3):
		nrWorkers = min(maxNrWorkers, multiprocessing.cpu_count())
		self.__pool = multiprocessing.Pool(processes = nrWorkers,
						   maxtasksperchild = 4)

	def enqueue(self, sourceText):
		mpAsync = self.__pool.apply_async(_awlValidatorWorker,
						  (sourceText,))
		return AwlValidatorResult(mpAsync)
