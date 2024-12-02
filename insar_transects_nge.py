import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union
from shapely.geometry import LineString
from utils import convert_3d_to_2d, create_transect, split_polygon_with_polylines, percentile

points_full_res_path = "C:/Users/eleonore.kong/Documents/NGE/170D_Uruguay_TramoA_fullres/170D_Uruguay_TramoA_fullres.shp"
points_rural_path = "C:/Users/eleonore.kong/Documents/NGE/170D_Uruguay_TramoA_rural/170D_Uruguay_TramoA_rural.shp"
trace_path = "C:/Users/eleonore.kong/Documents/NGE/Tracé.shp"
trace_id = "'TRAMO 1'"
output_folder = "C:/Users/eleonore.kong/Documents/NGE/"


buffer_dict = {5000:2, 1000:3, 500:4, 200:4}

gdf_trace = gpd.read_file(trace_path, where=f"Layer LIKE {trace_id}")
crs = gdf_trace.crs
gdf_trace['geometry'] = gdf_trace['geometry'].apply(convert_3d_to_2d)
trace_polyline = unary_union(gdf_trace.geometry)
trace_polyline = trace_polyline.simplify(tolerance=1000)

points_full_res = gpd.read_file(points_full_res_path)
points_rural = gpd.read_file(points_rural_path)
points_all = pd.concat([points_full_res, points_rural], ignore_index=True)
points_all = points_all.to_crs(crs)

for buffer_width, ratio in buffer_dict.items():
    num_points = int(trace_polyline.length // buffer_width)
    points_along_trace = [trace_polyline.interpolate(buffer_width * i) for i in range(num_points + 1)]
    points_along_trace_gdf = gpd.GeoDataFrame(geometry=points_along_trace, crs=gdf_trace.crs)
    points_along_trace_gdf['y'] = points_along_trace_gdf.geometry.y
    points_along_trace_gdf['x'] = points_along_trace_gdf.geometry.x
    points_along_trace_gdf.sort_values(by=['y','x'], inplace=True)
    line = LineString(points_along_trace_gdf["geometry"])

    buffer = trace_polyline.buffer(buffer_width, buffer_width, cap_style="square", join_style="bevel")

    transect_step = int(buffer_width * ratio)
    num_transects = int(line.length / transect_step)
    transect_length = transect_step + transect_step * 2.5
    transects = [create_transect(line, transect_step * i, transect_length) for i in range(1, num_transects + 1)]
    transects_gdf = gpd.GeoDataFrame(geometry=transects, crs=crs)
    transects_output = output_folder + f"insar_transect_line_{buffer_width}m.geojson"
    transects_gdf.to_file(transects_output, driver="GeoJSON")

    split_polygons = split_polygon_with_polylines(buffer, transects)
    split_polygons_gdf = gpd.GeoDataFrame(geometry=split_polygons, crs=crs)

    join = points_all.sjoin(split_polygons_gdf)
    agg_points = join.groupby("index_right").agg({
        "velocity": [
            "size",
            "mean",
            "median",
            percentile(80),
            percentile(20)
            ]
        }
    )

    agg_points.columns = ['_'.join(col) for col in agg_points.columns]
    stats_gdf = split_polygons_gdf.reset_index().merge(agg_points, right_on='index_right', left_on="index")
    stats_gdf.set_index("index", inplace=True)
    output_file = output_folder + f"insar_transect_stats_{buffer_width}m.geojson"
    stats_gdf.to_file(output_file, driver="GeoJSON")
#%%
