from application.extractor import extract_footprint_from_prism
from geopandas.geodataframe import GeoDataFrame
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import osmnx as ox
import prism


def simplify_and_mapping(data_source):
    if data_source == 'lwm':
        tau = 2
        buildings = extract_footprint_from_prism('../data/lwm-prism.gml')
    else:  # Only for Manhattan, New York
        tau = 0.00003
        buildings = ox.footprints_from_place('{}, Manhattan, New York City'.format(data_source))
    douglas_peucker_buildings = GeoDataFrame()
    simplified_buildings = GeoDataFrame()
    sum_haus = [0.0, 0.0]
    total_points = [0, 0]
    tolerance = tau * 3/5

    def comparison(footprint, i):
        new_footprint = prism.simplify(footprint, tau=tau, epsilon=math.pi/30)
        if new_footprint is not None:
            simplified_buildings.loc[i, 'geometry'] = new_footprint
            haus = footprint.hausdorff_distance(new_footprint)
            sum_haus[1] += haus
            total_points[1] += len(new_footprint.exterior.coords)

            dp_footprint = footprint.simplify(tolerance)
            douglas_peucker_buildings.loc[i, 'geometry'] = dp_footprint

            haus = footprint.hausdorff_distance(dp_footprint)
            sum_haus[0] += haus
            total_points[0] += len(dp_footprint.exterior.coords)

    count = 0
    for geom in buildings['geometry']:
        if geom.geom_type == 'Polygon':
            comparison(geom, count)
            count += 1
        if geom.geom_type == 'MultiPolygon':
            for poly in geom:
                comparison(poly, count)
                count += 1

    print("Average Hausdorff Distance (Douglas Peucker):", sum_haus[0]/count)
    print("Average Hausdorff Distance (Indoor Simplification):", sum_haus[1] / count)
    print("Total Number of Points (Douglas Peucker):", total_points[0])
    print("Total Number of Points (Indoor Simplification):", total_points[1])

    cell_text = [[tolerance, tau], [sum_haus[0]/count, sum_haus[1] / count], [total_points[0] , total_points[1]]]
    # mapping
    minx, miny, maxx, maxy = buildings.total_bounds
    map_scale = 50
    width = maxx-minx
    height = maxy-miny
    ratio = width/height
    mbr = (ratio*map_scale, map_scale)
    fig, ax = plt.subplots(figsize=mbr)
    buildings.plot(ax=ax, facecolor='green', edgecolor='grey', linewidth=0.2, alpha=0.1)
    douglas_peucker_buildings.plot(ax=ax, facecolor='blue', alpha=0.1)
    simplified_buildings.plot(ax=ax, facecolor='red', alpha=0.1)

    ax.table(cellText=cell_text,
             rowLabels=[ "Distance Tolerance", "Average Hausdorff Distance", "Total Number of Points"],
             colLabels=["Douglas Peucker", "Indoor Simplification"],
             colWidths=[0.05/ratio, 0.05/ratio],
             loc='lower right')

    legend_elements = [Patch(facecolor='green', edgecolor='grey', linewidth=0.2, alpha=0.1, label='Original'),
                       Patch(facecolor='blue', alpha=0.1, label='Douglas Peucker'),
                       Patch(facecolor='red', alpha=0.1, label='Indoor Simplification')]
    ax.legend(handles=legend_elements, loc='upper right', title='Simplification Method', fontsize=map_scale,
              title_fontsize=map_scale)
    plt.tight_layout()
    plt.savefig('../examples/{}.pdf'.format(data_source), format='pdf')
    # plt.show()


if __name__ == '__main__':
    sources = ['lwm',  # Lotte World Mall
               'Midtown Manhattan', 'Murray Hill', 'Upper West Side', 'Upper East Side',  # Manhattan, New York
               'East Harlem', 'Harlem', 'Two Bridges', 'Lower Manhattan']
    for source in sources:
        simplify_and_mapping(source)
