from lxml import etree
import numpy as np
from shapely.geometry import Polygon
from geopandas.geodataframe import GeoDataFrame

__all__ = ['extract_footprint_from_prism']

ns_citygml = "http://www.opengis.net/citygml/2.0"
ns_gml = "http://www.opengis.net/gml"
ns_bldg = "http://www.opengis.net/citygml/building/1.0"


def room_finder(gml_element):
    """
    Find the <bldg:Room> element.
    :param gml_element:
    :return: rooms
    """
    rooms = gml_element.findall('.//{%s}Room' % ns_bldg)
    return rooms


def polygon_finder(gml_element):
    """
    Find the <gml:polygon> element.
    :param gml_element:
    :return: polygons within the element
    """
    polygons = gml_element.findall('.//{%s}Polygon' % ns_gml)
    return polygons


def extract_ring(gml_element):
    """
    Extracts the <gml:exterior> and <gml:interior> of a <gml:Polygon>.
    :param gml_element:
    :return: exterior, interiors
    """
    exterior = gml_element.findall('.//{%s}exterior' %ns_gml)
    interior = gml_element.findall('.//{%s}interior' %ns_gml)
    return exterior, interior


def extract_points(ring):
    """
    Extract points from a <gml:LinearRing>.
    :param ring: a ring
    :return:
    """
    list_points = []
    if len(ring.findall('.//{%s}posList' %ns_gml)) > 0:
        points = ring.findall('.//{%s}posList' %ns_gml)[0].text
        coords = points.split()
        assert(len(coords) % 3 == 0)
        for i in range(0, len(coords), 3):
            list_points.append([float(coords[i]), float(coords[i+1]), float(coords[i+2])])
    elif len(ring.findall('.//{%s}pos' %ns_gml)) > 0:
        points = ring.findall('.//{%s}pos' %ns_gml)
        for p in points:
            coords = p.text.split()
            assert(len(coords) % 3 == 0)
            for i in range(0, len(coords), 3):
                list_points.append([float(coords[i]), float(coords[i+1]), float(coords[i+2])])
    else:
        return None

    return list_points


def extract_footprint(polygons):
    """
    Extract 2D footprints. Assume that the input data is represented as a prism in 3D.
    :param polygons: a pair of lower and upper polygon
    :return: footprints, height of the lower polygon
    """
    heights = []
    prisms = []
    for poly in polygons:
        exterior, interior = extract_ring(poly)
        epoints = extract_points(exterior[0])
        #irings = []
        #for iring in inteior:
        #    irings.append(gml_points(iring))
        height = 0
        for i in range(len(epoints)):
            height += epoints[i][2]

        heights.append(height/len(epoints))
        prisms.append(epoints)

    index = np.array(heights).argmin()
    list_points = [coordinates[0:2] for coordinates in prisms[index]]

    return list_points, heights[index]


def extract_footprint_from_prism(path):
    citygml = etree.parse(path)
    root = citygml.getroot()
    if root.tag == "{http://www.opengis.net/citygml/1.0}CityModel":
        ns_citygml = "http://www.opengis.net/citygml/1.0"
        ns_gml = "http://www.opengis.net/gml"
        ns_bldg = "http://www.opengis.net/citygml/building/1.0"
    else:
        ns_citygml = "http://www.opengis.net/citygml/2.0"
        ns_gml = "http://www.opengis.net/gml"
        ns_bldg = "http://www.opengis.net/citygml/building/2.0"

    city_objects = []
    buildings = []
    footprints_by_floor = {}

    for obj in root.getiterator('{%s}cityObjectMember' % ns_citygml):
        city_objects.append(obj)

    if len(city_objects) > 0:
        for city_object in city_objects:
            for child in city_object.getchildren():
                if child.tag == '{%s}Building' % ns_bldg:
                    buildings.append(child)

        for b in buildings:
            rooms = room_finder(b)
            for room in rooms:
                polys = polygon_finder(room)
                footprint, height = extract_footprint(polys)

                if height not in footprints_by_floor:
                    footprints_by_floor[height] = []

                footprints_by_floor[height].append(Polygon(footprint))

    footprints_of_buildings = GeoDataFrame()
    for i in range(len(footprints_by_floor[0.0])):
        footprints_of_buildings.loc[i, 'geometry'] = footprints_by_floor[0.0][i]

    return footprints_of_buildings


if __name__ == '__main__':
    extract_footprint_from_prism('../data/lwm-prism.gml')


