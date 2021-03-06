#!/usr/bin/python

import sys, math

fill_paths = [

	("23", "soldermask.path"), # soldermask front
#	("21", "silkscreen.path"),
#	("15", "copper_top.path"),
	("15", "copper_top_x.path"),
	("0", "copper_bottom.path"),

	("0", "battery_holder.path"),
	("22", "battery_holder_mask.path"),
	("21", "ispmark.path"),
	("0", "safetypin.path"),
	("22", "safetypin.path"),
]

segment_paths = [
	("21", "silkscreen.segments", .9),
	("28", "edges_round.segments", .9),
#	("28", "edges.segments", .9),
	("20", "techincnl.segments", .9),
]

pads = [
	( (-129.50091,49.85), 2, 3 )
]


vias = [
	( 10, 10),
	( 20, 10),
	( 10, 20),
	( 20, 20),
]

name = "techinc_badge"

start = cur = None

cubic_sections = 32

in_dpi, out_dpi = 90., 10000.
scale = out_dpi/in_dpi


def dist(a, b):
	ax, ay = a
	bx, by = b
	return math.sqrt((ax-bx)**2 + (ay-by)**2)

def set_cur(newcur):
	global cur
	x, y = cur = newcur

def interpolate(pos1, pos2, d):
	x1, y1 = pos1
	x2, y2 = pos2
	return ( x1*(1-d) + x2*d, y1*(1-d) + y2*d )

def get_abs(coords):
	x, y = cur
	dx, dy = coords
	return (x+dx, y+dy)

def coord_fmt( coords ):
	x, y = coords
	return "%d %d" % ( round(x*scale), round(y*scale) )

def output_line( coords ):
	set_cur(coords)
	return [ "Dl " + coord_fmt(coords) ]

def output_rel_line( coords ):
	return output_line(get_abs(coords))

def output_move( coords ):
	global start
	if start == None:
		start = coords
	set_cur(coords)
	return [ "Dl " + coord_fmt(coords) ]

def output_rel_move( coords ):
	return output_move(get_abs(coords))

def output_cubic( guide1, guide2, end ):
	start = cur
	n = min(int(dist(start, end)*scale/40.)+1, cubic_sections)

	v = []
	for i in xrange(1, n+1):
		d = i/float(n)
		a = interpolate(start, guide1, d)
		b = interpolate(guide1, guide2, d)
		c = interpolate(guide2, end, d)

		ab = interpolate(a, b, d)
		bc = interpolate(b, c, d)
		abc = interpolate(ab, bc, d)
		v += output_line(abc)
	return v


def output_line_segment( coords, layer ):
	print "DS %s %s %d %s" % (coord_fmt(cur), coord_fmt(coords),width*scale,layer)
	set_cur(coords)

def output_cubic_segment( guide1, guide2, end, layer ):
	start = cur
	n = min(int(dist(start, end)*scale/40.)+1, cubic_sections)

	for i in xrange(1, n+1):
		d = i/float(n)
		a = interpolate(start, guide1, d)
		b = interpolate(guide1, guide2, d)
		c = interpolate(guide2, end, d)

		ab = interpolate(a, b, d)
		bc = interpolate(b, c, d)
		abc = interpolate(ab, bc, d)
		output_line_segment(abc, layer)


def output_rel_cubic( guide1, guide2, end ):
	return output_cubic( get_abs(guide1), get_abs(guide2), get_abs(end) )

def output_rel_move( coords ):
	return output_move(get_abs(coords))

def output_close():
	global start
	set_cur(start)
	start = None
	return [ "Dl " + coord_fmt(cur) ]

def get_coords(s):
	return map(float, s)

def pad_at(coords):
	return """$PAD
Sh "1" C 600 600 0 0 0
Dr 400 0 0
At STD N 00E0FFFF
Ne 0 ""
Po """+coord_fmt(coords)+"""
$EndPAD"""

def via_at(coords):
	return """$TRACK
Po 3 """+coord_fmt(coords)+" "+coord_fmt(coords)+""" 350 -1
De 15 1 0 0 0
$EndTRACK"""


def pad_grid(coords, w, h, pitch=.1):
	x, y = coords
	v = []
	for i in xrange(w):
		for j in xrange(h):
			v += [ pad_at( (x + pitch*in_dpi*i, y + pitch*in_dpi*j) ) ]

	return '\n'.join(v)
	

def print_path(data, layer):

	global start, cur
	values = (x for x in  data.replace(',', ' ').split(' ') if x != '' )

	mode = 'z'

	cur = (0.,0.)
	start = None

	v = []

	for x in values:
		if x[-1] == '\n':
			x = x[:-1]

		if x in 'mclMCL':
			mode = x
			continue

		if x in 'zZ':
			mode = x

		if mode in 'zZ':
			v += output_close()
			print 'DP 0 0 0 0 %d 1 %s' % (len(v), layer)
			print '\n'.join(v)
			v = []
		elif mode == 'm':
			v += output_rel_move(get_coords((x, values.next())))
			mode = 'l'
		elif mode == 'M':
			v += output_move(get_coords((x, values.next())))
			mode = 'L'
		elif mode == 'c':
			guide1 = x, values.next()
			guide2 = values.next(), values.next()
			end = values.next(), values.next()
			v += output_rel_cubic(get_coords(guide1), get_coords(guide2), get_coords(end))
		elif mode == 'C':
			guide1 = x, values.next()
			guide2 = values.next(), values.next()
			end = values.next(), values.next()
			v += output_cubic(get_coords(guide1), get_coords(guide2), get_coords(end))
		elif mode == 'l':
			v += output_rel_line(get_coords((x, values.next())))
		elif mode == 'L':
			v += output_line(get_coords((x, values.next())))
		else:
			print "ERROR: " + x
			sys.exit(1)


def print_segments(data, layer, width):

	global start
	values = (x for x in  data.replace(',', ' ').split(' ') if x != '' )

	set_cur( (0.,0.) )
	start = cur

	for x in values:
		if x[-1] == '\n':
			x = x[:-1]

		if x in 'mclMCL':
			mode = x
			continue

		if x in 'zZ':
			mode = x

		if mode in 'zZ':
			print "DS %s %s %d %s" % (coord_fmt(cur), coord_fmt(start),width*scale,layer)
			set_cur(start)
		elif mode == 'm':
			set_cur(get_abs(get_coords((x, values.next()))))
			start = cur
			mode = 'l'
		elif mode == 'M':
			set_cur(get_coords((x, values.next())))
			start = cur
			mode = 'L'
		elif mode == 'l':
			pos = get_abs(get_coords((x, values.next())))
			print "DS %s %s %d %s" % (coord_fmt(cur), coord_fmt(pos),width*scale,layer)
			set_cur(pos)
		elif mode == 'L':
			pos = get_coords((x, values.next()))
			print "DS %s %s %d %s" % (coord_fmt(cur), coord_fmt(pos),width*scale,layer)
			set_cur(pos)
		elif mode == 'c':
			guide1 = x, values.next()
			guide2 = values.next(), values.next()
			end = values.next(), values.next()
			output_cubic_segment(get_abs(get_coords(guide1)), get_abs(get_coords(guide2)), get_abs(get_coords(end)),layer)
		elif mode == 'C':
			guide1 = x, values.next()
			guide2 = values.next(), values.next()
			end = values.next(), values.next()
			output_cubic_segment(get_coords(guide1), get_coords(guide2), get_coords(end),layer)
		else:
			print "ERROR: " + x
			sys.exit(1)

print """PCBNEW-LibModule-V1
$INDEX
"""

print name
print """$EndINDEX
$MODULE """ + name + """
Po 0 0 0 15 00000000 00000000 ~~
Li """ + name

for layer, filename in fill_paths:
	f = open(filename)
	print_path(f.read(1000000), layer)
	f.close()

for layer, filename, width in segment_paths:
	f = open(filename)
	print_segments(f.read(1000000), layer, width)
	f.close()

for topleft, w, h in pads:
	print pad_grid(topleft, w, h)

#for coords in vias:
#	print via_at( coords )

print """$EndMODULE """ + name + """
$EndLIBRARY"""

