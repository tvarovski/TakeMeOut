# TakeMeOut

Explore your Google Checkout geolocation data with this Python package.

![example_calendar_figure](outputs/example.png)

# Dependencies

You need to have the following installed:

- `iso8601`
- `matplotlib`
- `pandas`
- `seaborn`
- `calplot`

# How To Use

1. Download google location data from [here](https://takeout.google.com/settings/takeout?pli=1).
2. Change settings in the the code_package/config.py directory:
    - `data_path` is the path to the directory where you downloaded (and unzipped) your data
    - `year` is the claeendar year you want to look at
    - `activity` is the activity you want to track time spent on (e.g. "WALKING")
    - `location` the geographical location you want to analyze (use a name or coordinates from [Google Maps](https://www.google.com/maps/)). If set to `custom-location`, you need to set the following:
        a) `latitude` is the latitude of the location point
        b) `longitude` is the longitude of the location point
        c) `radius` is the radius of the zone around the coordinates you want to analyze
3. Run main.py
4. Explore your figures in the `outputs/` directory