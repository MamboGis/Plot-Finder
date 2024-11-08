import streamlit as st
import leafmap.foliumap as leafmap
import pandas as pd
from sqlalchemy import create_engine
from shapely import wkb
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import transform
from pyproj import CRS, Transformer
import folium
from streamlit_folium import st_folium

# Set up the database connection
connection_string = f"postgresql+psycopg2://{'postgres'}:{'39208072'}@{'localhost'}/{'SDB'}"
engine = create_engine(connection_string)

# Layout configuration
st.set_page_config(page_title="Georeferencing", page_icon="", layout="wide")

# Fetch data from the 'kwale' table
with engine.connect() as connection:
    query = "SELECT * FROM kwale"
    df = pd.read_sql(query, connection)

# Create text input for plot number
searched_plot = st.text_input('Enter Plot Number').strip()

# Check if a plot number is typed
if searched_plot:
    # Filter the dataframe by the entered plot number
    filtered_df_by_plot = df[df['plot_no'] == searched_plot]

    # Check if the entered plot number exists in the database
    if not filtered_df_by_plot.empty:
        # Extract unique sources for the typed plot number
        source_options = filtered_df_by_plot['source'].unique()
        
        # Display selectbox for source filtered by the plot number
        selected_source = st.selectbox('Select Source', source_options)
        
        # Filter the dataframe further based on the selected source
        plot_df = filtered_df_by_plot[filtered_df_by_plot['source'] == selected_source]

        # Map display and geometry processing logic
        m = leafmap.Map(minimap_control=True, center=[-4, 39], zoom=9)
        m.add_basemap("HYBRID")

        # Check if plot_df is not empty
        if not plot_df.empty:
            # Parse the geometry using shapely
            geom = plot_df.iloc[0]['geom']
            polygon = wkb.loads(geom, hex=True)

            # Define the source and destination CRS
            src_crs = CRS.from_epsg(21037)  # Example EPSG:32737 (UTM Zone 37S)
            dst_crs = CRS.from_epsg(4326)   # WGS84

            # Transformer to reproject the geometry
            transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)

            # Reproject the geometry to WGS84
            reprojected_polygon = transform(transformer.transform, polygon)

            # Get the bounding box of the reprojected polygon
            if isinstance(reprojected_polygon, Polygon):
                bounds = reprojected_polygon.bounds
            elif isinstance(reprojected_polygon, MultiPolygon):
                bounds = reprojected_polygon.envelope.bounds

            # Fit the map to the bounds of the reprojected polygon
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

            # Add the reprojected polygon to the map
            folium.GeoJson(
                data=reprojected_polygon.__geo_interface__,
                name='Selected Plot',
                tooltip=f"Plot Number: {searched_plot}\nSource: {selected_source}"
            ).add_to(m)

        # Display the map in Streamlit
        st_folium(m, height=500, width=1500)
    else:
        st.write("No data found for the entered plot number.")
