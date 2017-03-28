# -*- coding: utf-8 -*-
#
# AWL simulator - FUP - Wire classes
#
# Copyright 2016-2017 Michael Buesch <m@bues.ch>
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

from awlsim.common.xmlfactory import *

from awlsim.gui.geo2d import *
from awlsim.gui.util import *
from awlsim.gui.fup.fup_base import *


class FupWire_factory(XmlFactory):
	def parser_open(self, tag=None):
		self.inWire = False
		XmlFactory.parser_open(self, tag)

	def parser_beginTag(self, tag):
		if not self.inWire:
			if tag.name == "wire":
				self.inWire = True
				idNum = tag.getAttrInt("id")
				if idNum in (w.idNum for w in self.grid.wires):
					raise self.Error("<wire id=%d> does "
						"already exist." % idNum)
				# Create wire and add it to the grid.
				FupWire(grid=self.grid, idNum=idNum)
				return
		XmlFactory.parser_beginTag(self, tag)

	def parser_endTag(self, tag):
		if self.inWire:
			if tag.name == "wire":
				self.inWire = False
				return
		else:
			if tag.name == "wires":
				self.parser_finish()
				return
		XmlFactory.parser_endTag(self, tag)

	def composer_getTags(self):
		return [
			self.Tag(name="wire",
				attrs={
					"id" : str(self.wire.idNum),
				}),
		]

class FupWire(FupBaseClass):
	"""FUP/FBD wire connecting two FupConn connections."""

	factory = FupWire_factory

	BRANCH_DIA = 4

	def __init__(self, grid, idNum=None):
		FupBaseClass.__init__(self)
		self.grid = grid
		self.connections = set()	# The connections this wire is connected to
		self.outConn = None		# The out-connection this is connected to

		if idNum is None:
			idNum = grid.getUnusedWireIdNum()
		self.idNum = idNum		# The ID number of this wire
		grid.addWire(self)

		self.__wirePen = QPen(QColor("#000000"))
		self.__wirePen.setWidth(2)
		self.__wireCollidingPen = QPen(QColor("#C02020"))
		self.__wireCollidingPen.setWidth(2)
		self.__wireBranchPen = QPen(QColor("#000000"))
		self.__wireBranchPen.setWidth(1)
		self.__wireBranchBrush = QBrush(QColor("#000000"))

	def connect(self, conn):
		"""Add a connection to this wire.
		"""
		if conn in self.connections:
			return
		if conn.OUT and\
		   self.outConn is not None and\
		   self.outConn is not conn:
			# We already have an output connection.
			raise ValueError
		self.connections.add(conn)
		conn.wire = self
		if conn.OUT:
			self.outConn = conn

	def disconnectAll(self):
		"""Disconenct all connections.
		"""
		for conn in self.connections:
			conn.wire = None
		self.connections.clear()
		self.outConn = None
		self.grid.removeWire(self)

	def disconnect(self, conn):
		"""Disconnect a connection from this wire.
		"""
		conn.wire = None
		self.connections.remove(conn)
		if self.outConn is conn:
			# Only inputs left. Remove them all.
			self.disconnectAll()
		if len(self.connections) == 1:
			# Only one connection left. Remove that, too.
			self.disconnectAll()
		if not self.connections and not self.outConn:
			self.grid.removeWire(self)

	class DrawInfo(object):
		__slots__ = ("segStart", "segments", "segDirect")
		def __init__(self, segStart, segments, segDirect):
			self.segStart = segStart
			self.segments = segments
			self.segDirect = segDirect

	def draw(self, painter):
		if self.outConn is None:
			return # Only inputs. Do not draw.
		grid = self.grid

		# Branch circles diameter
		branchR, branchD = self.BRANCH_DIA // 2, self.BRANCH_DIA
		painter.setBrush(self.__wireBranchBrush)

		# Calculate the coordinates of all wire lines.
		wireLines = [] # List of DrawInfo()s
		xAbs0, yAbs0 = self.outConn.pixCoords
		cellPixWidth = self.grid.cellPixWidth
		for inConn in self.connections:
			if inConn is self.outConn:
				continue
			assert(inConn.IN)

			# Construct line segments to draw the wire from out to in.

			xAbs1, yAbs1 = inConn.pixCoords
			x = (xAbs0 // cellPixWidth) * cellPixWidth + cellPixWidth

			segStart = LineSeg2D.fromCoords(xAbs0, yAbs0, x, yAbs0)
			seg0 = LineSeg2D.fromCoords(x, yAbs0, x, yAbs1)
			seg1 = LineSeg2D.fromCoords(x, yAbs1, xAbs1, yAbs1)
			segDirect = LineSeg2D.fromCoords(x, yAbs0, xAbs1, yAbs1)

			wireLines.append(self.DrawInfo(segStart,
						       (seg0, seg1),
						       segDirect))

		def drawBranch(x, y):
			painter.setPen(self.__wireBranchPen)
			painter.drawEllipse(x - branchR, y - branchR,
					    branchD, branchD)

		def drawSeg(seg, handleBranches=True, pen=self.__wirePen):
			painter.setPen(pen)
			grid.drawWireLine(painter, self, seg)
			if not handleBranches:
				return
			for otherDrawInfo in wireLines:
				if drawInfo is otherDrawInfo:
					continue
				for otherSeg in otherDrawInfo.segments:
					inter = seg.intersection(otherSeg)
					if not inter.intersects:
						continue
					drawBranch(inter.pointA.x, inter.pointA.y)
					drawBranch(inter.pointB.x, inter.pointB.y)

		# Draw wire from output to all inputs
		for drawInfo in wireLines:
			drawSeg(drawInfo.segStart, handleBranches=False)
			if all(not grid.checkWireLine(painter, {self}, seg)
			       for seg in drawInfo.segments):
				for seg in drawInfo.segments:
					drawSeg(seg)
			else:
				drawSeg(drawInfo.segDirect, handleBranches=False,
					pen=self.__wireCollidingPen)
