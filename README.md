# Usage:
1. Install python and the dependencies listed in `requirements.txt`.
1. If you're starting with a KMZ file, unpack it using an unzipping tool.  You should get a KML file.
1. Run `python run.py --kml_path [path to kml file]`, filling in `[path to kml file]` with the path to the KML file from the previous step.
1. In the same directory as the KML file, there should now be `raw_tables.csv` and `by_block_id.csv` files that contain the information from the tables in the KML file.
