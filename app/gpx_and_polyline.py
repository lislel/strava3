"""
This file contains functions used to manipulate gpx files and polylines
"""

import gpxpy
import polyline


def gpx_to_polyline(gpx_file):
	"""conver a GPX file to a polyline"""
	gpx = gpxpy.parse(gpx_file)

	point_list = list()
	for track in gpx.tracks:
		for segment in track.segments:
			for point in segment.points:
				#print('Point at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation))
				point_list.append((point.latitude, point.longitude))

	return polyline.encode(point_list)


if __name__ == '__main__':
	FILE = "C:\\Users\\cummi\\Downloads\\activity_6508241230.gpx"
	gpx_file = open(FILE, 'r')
	print(gpx_to_polyline(gpx_file))
