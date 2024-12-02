from shapely.geometry import LineString, MultiPolygon, GeometryCollection
from shapely.ops import split
import numpy as np


def convert_3d_to_2d(line):
    coords_2d = [(x, y) for x, y, z in line.coords]
    return LineString(coords_2d)


def create_transect(line, distance, length):
    """Create a transect line at a given distance along the polyline."""
    point = line.interpolate(distance)

    # Get the direction of the line at the interpolation point
    if distance == 0:
        direction = np.array(line.interpolate(distance + 0.01).coords[0])[:2] - np.array(point.coords[0])[:2]
    elif distance == line.length:
        direction = np.array(point.coords[0])[:2] - np.array(line.interpolate(distance - 0.01).coords[0])[:2]
    else:
        direction = np.array(line.interpolate(distance + 0.01).coords[0])[:2] - np.array(
            line.interpolate(distance - 0.01).coords[0])[:2]

    # Normalize the direction vector and calculate the perpendicular vector
    direction = direction / np.linalg.norm(direction)
    perp_vector = np.array([-direction[1], direction[0]]) * length / 2

    start = np.array(point.coords[0])[:2] + perp_vector
    end = np.array(point.coords[0])[:2] - perp_vector
    return LineString([start, end])


def split_polygon_with_polylines(polygon, polylines):
    result = [polygon]
    for line in polylines:
        new_result = []
        for geom in result:
            if geom.is_empty:
                continue
            split_result = split(geom, line)
            if isinstance(split_result, (MultiPolygon, GeometryCollection)):
                new_result.extend(split_result.geoms)
            else:
                new_result.append(split_result)
        result = new_result
    return result


def percentile(n):
    def percentile_(x):
        return np.percentile(x, n)
    percentile_.__name__ = f'percentile_{n}'
    return percentile_