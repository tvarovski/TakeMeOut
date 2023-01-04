#!pip install iso8601
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import iso8601
import calplot
import sys


#redirect the stderr to a file in the outputs directory
sys.stderr = open(f'outputs/err.txt', 'w')

def get_date_object(date_string):
  #converts the date string to a datetime object
  return iso8601.parse_date(date_string)


def isObject(timelineObjects, objectName=str):
  #checks if the objectName is in the timelineObjects dictionary, returns True if it is
  
  try:
    if timelineObjects[objectName]:
      return True

  except Exception as e:
    sys.stderr.write(f"Couldn't find {objectName} in timelineObjects in isObject()\n")
    sys.stderr.write(f"Error: {e}\n")
    return False

  return False


def extractObjectTime(timelineObject):
  #extracts the start and end time of the timelineObject, if it exists
  #returns the duration in minutes, and the start and end time as datetime objects,

  try:
    timelineObject_start_time = timelineObject['duration']['startTimestamp']
    timelineObject_end_time = timelineObject['duration']['endTimestamp']
    timelineObject_start_time = get_date_object(timelineObject_start_time).timestamp()*1000
    timelineObject_end_time = get_date_object(timelineObject_end_time).timestamp()*1000

  except Exception as e:
    sys.stderr.write(f"Couldn't retrieve timelineObject time in extractObjectTime()\n")
    sys.stderr.write(f"Error: {e}\n")

  try:
    duration_min = (((timelineObject_end_time-timelineObject_start_time)/1000)/60)
    dt_object_start = datetime.fromtimestamp(timelineObject_start_time/1000)
    dt_object_end = datetime.fromtimestamp(timelineObject_end_time/1000)

  except Exception as e:
    sys.stderr.write(f"Couldn't parse dt_object in extractObjectTime()\n")
    sys.stderr.write(f"Error: {e}\n")
  
  return(duration_min, dt_object_start, dt_object_end)


def calculateTime(data, query_loc, query_param):
  #calculates the total time spent at a specified location (query_loc)
  #returns the total time in hours spent in query_loc,
  #a list of the time spent at the specified location in each visit,
  #and a dictionary of the total time spent at each location

  '''this function needs to be cleaned up, it's a mess'''

  total_loc_time_min = 0
  places = {}
  data_out = []

  for timelineObjects in data['timelineObjects']:

    #check if placeVisit object is a current object
    #if not, move on to the next
    if not isObject(timelineObjects, 'placeVisit'):
      continue

    try:
      visit = timelineObjects['placeVisit']
      location = visit['location']

      duration_min, dt_object_start, dt_object_end = extractObjectTime(visit)

      if location[query_param] == query_loc:
        total_loc_time_min+=duration_min

      if location[query_param] not in places:
        places[location[query_param]] = duration_min/60
      else:
        places[location[query_param]] += duration_min/60
      
      data_out.append([location[query_param], duration_min, dt_object_start, dt_object_end])

    except Exception as e:
      sys.stderr.write("Couldn't parse data in calculateTime()\n")
      sys.stderr.write(f"Error: {e}\n")
      pass

  return(total_loc_time_min/60, data_out, places)


def calculateTimeCoordinates(data, latitude, longitude, radius):

  total_loc_time_min = 0
  data_out = []

  for timelineObjects in data['timelineObjects']:

    #check if placeVisit object is a current object
    #if not, move on to the next
    if not isObject(timelineObjects, 'placeVisit'):
      continue

    try:
      visit = timelineObjects['placeVisit']

      centerLat = visit['centerLatE7']
      centerLng = visit['centerLngE7']
      
      duration_min, dt_object_start, dt_object_end = extractObjectTime(visit)

      #check if location is within the radius of coordinates
      if (centerLat/(10000000) - latitude)**2 + (centerLng/(10000000) - longitude)**2 < radius**2:
        total_loc_time_min+=duration_min

        data_out.append(["custom-location", duration_min, dt_object_start, dt_object_end])
      
    except Exception as e:
      sys.stderr.write("Couldn't parse data in calculateTimeCoordinates()\n")
      sys.stderr.write(f"Error: {e}\n")
      pass

  return(total_loc_time_min/60, data_out)


def calculateActivityTime(data, query_activity):

  total_act_time_min = 0
  total_distance = 0
  activities = {}
  data_out = []

  for timelineObjects in data['timelineObjects']:
    #check if placeVisit object is a current object
    #if not, move on to the next

    if not isObject(timelineObjects, 'activitySegment'):
      continue

    try:
      activity = timelineObjects['activitySegment']
      duration_min, dt_object_start, dt_object_end = extractObjectTime(activity)

      activity_distance = activity['distance']

      if activity['activityType'] == query_activity:
        total_act_time_min+=duration_min
        total_distance+=activity_distance

      if activity['activityType'] not in activities:
        activities[activity['activityType']] = duration_min/60
      else:
        activities[activity['activityType']] += duration_min/60

      data_out.append([activity['activityType'], duration_min, dt_object_start, dt_object_end])

    except Exception as e:
      sys.stderr.write("couldn't retreive location data in calculateActivityTime()\n")
      sys.stderr.write(f"Error: {e}\n")

  sys.stdout.write(f"total distance {query_activity}: {total_distance/1000} km\n")
  return(total_act_time_min/60, data_out, activities)


def plotDays(data_out, query_loc, YEAR, MONTH):

  graph_order=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
  df = pd.DataFrame(data_out, columns =['Location', 'Duration_min', 'Daytime_start', 'Daytime_end'])
  df = df[df['Location'] == query_loc ]

  df['Date'] = df['Daytime_start'].dt.date
  df["Day_of_week"] = df['Daytime_start'].dt.day_name()

  df = df.groupby("Date").agg({'Duration_min':'sum', 'Day_of_week':'max'})

  df['Duration_hrs'] = df['Duration_min']/60
  
  sns.set_style("whitegrid")
  sns.set_context("talk")
  graph = sns.catplot(x="Day_of_week", y="Duration_hrs", jitter=False, data=df, order=graph_order, height=6, aspect=3/2
        ).set(title=f"{query_loc} in {MONTH}")
  graph.ax.axhline(10, ls='--',c='r')
  graph.ax.axhline(8, ls='--',c='b')

  #save the plot as a png file to the directory where the script is located
  
  plt.savefig(f"outputs/{query_loc}_{YEAR}_{MONTH}.png", dpi=300)


def plotCalendarHeatmap(df, query_loc, YEAR):
  #function that plots the data on a calendar heatmap where the color represents the amount of time spent in a location

  df = pd.DataFrame(df, columns =['Location', 'Duration_min', 'Daytime_start', 'Daytime_end'])
  df = df[df['Location'] == query_loc ]
  df["Day_of_week"] = df['Daytime_start'].dt.day_name()

  #if Daytime_start and Daytime_end are on different days, delete the row, split the duration at midnight and create two new rows, one for each day
  for index, row in df.iterrows():
    if row['Daytime_start'].date() != row['Daytime_end'].date():
      # remove the row and add two new rows
      df.drop(index, inplace=True)
      # calculate time from Daytime_start to midnight
      duration_min_day1 = (row['Daytime_start'].replace(hour=23, minute=59, second=59, microsecond=0) - row['Daytime_start']).total_seconds()/60
      # calculate time from midnight to Daytime_end
      duration_min_day2 = (row['Daytime_end'] - row['Daytime_end'].replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()/60
      

      df = pd.concat([df, pd.DataFrame.from_dict([{'Location': row['Location'],
                                                   'Duration_min': duration_min_day1,
                                                   'Daytime_start': row['Daytime_start'],
                                                   'Daytime_end': row['Daytime_start'].replace(hour=23, minute=59, second=59, microsecond=0),
                                                   'Date': row['Daytime_start'].date(),
                                                   'Day_of_week': row['Daytime_start'].day_name()
                                                  }])])

      df = pd.concat([df, pd.DataFrame.from_dict([{'Location': row['Location'],
                                                   'Duration_min': duration_min_day2,
                                                   'Daytime_start': row['Daytime_end'].replace(hour=0, minute=0, second=0, microsecond=0),
                                                   'Daytime_end': row['Daytime_end'], 'Date': row['Daytime_end'].date(),
                                                   'Day_of_week': row['Daytime_end'].day_name()
                                                   }])])

  #set the date as the datetime object
  df['Date'] = df['Daytime_start'].dt.date

  #print out all entries that end on Feb 11th 2022, ordered by the start time, troubleshooting
  #df_temp = df[df['Date'] == make_date(2022, 2, 11)]
  #df_temp = df_temp.sort_values(by=['Daytime_start'])
  #print(df_temp)

  #combine rows that have the same date and sum the duration
  df = df.groupby("Date").agg({'Duration_min':'sum', 'Day_of_week':'max'})

  df['Duration_hrs'] = df['Duration_min']/60
  df.reset_index(inplace=True)
 
  #set date as index
  df['Date'] = pd.to_datetime(df['Date'])
  df = df.set_index('Date')

  calplot.calplot(data = df['Duration_hrs'], textformat='{:.0f}', how = 'sum', cmap = 'magma_r', figsize = (16, 4), vmax = 16, vmin = 0, linewidth=1, edgecolor='black', textcolor='whitesmoke')
  
  #save the plot as a png file to the directory where the script is located
  plt.savefig(f"outputs/{query_loc}_{YEAR}_calendar.png", dpi=400)

def runAnalysis(DIR, YEAR, location, LATITUDE, LONGITUDE, RADIUS, ACTIVITY):
  #function that runs the analysis for a given location

  months = ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER']
  total_hours_location = 0
  total_hours_activity = 0

  calendar_df= pd.DataFrame(columns =['Location', 'Duration_min', 'Daytime_start', 'Daytime_end'])

  for MONTH in months:

    try:
      with open(f'{DIR}/Takeout/Location History/Semantic Location History/{YEAR}/{YEAR}_{MONTH}.json','r') as f:
          data = json.loads(f.read())
          #sys.stdout.write(f"FOUND: {DIR}/Takeout/Location History/Semantic Location History/{YEAR}/{YEAR}_{MONTH}.json\n\n")

    except Exception as e:
      print(f'Couldnt load data from {DIR}/Takeout/Location History/Semantic Location History/{YEAR}/{YEAR}_{MONTH}.json')
      print(e)
      continue

    if location != "custom-location":

      try:
        hours_location, data_out, places = calculateTime(data,location)
        sys.stdout.write(f"Month: {MONTH}, {hours_location} hours in {location}\n")
        sys.stdout.write(f"Places: {places}\n")

      except Exception as e:
        print(e)
        print(f"calculateTime() Failed!")

    else:

      try:
        #round coordinates to 7 decimal places
        latitude = round(LATITUDE, 7)
        longitude = round(LONGITUDE, 7)
        hours_location, data_out = calculateTimeCoordinates(data, latitude, longitude, RADIUS)
        sys.stdout.write(f"Month: {MONTH}, {hours_location} hours in {location}\n")

      except Exception as e:
        print(e)
        print(f"calculateTimeCoordinates() Failed!")

    #plot the data, save the plot as a png file to the directory where the script is located
    plotDays(data_out, location, YEAR, MONTH)

    #create a dataframe from the data_out list and append it to the calendar_df dataframe
    data_out_temp = pd.DataFrame(data_out, columns =['Location', 'Duration_min', 'Daytime_start', 'Daytime_end'])
    calendar_df = pd.concat([calendar_df, data_out_temp], ignore_index=True)

    total_hours_location+=hours_location

    hours_activity, data_out, activities = calculateActivityTime(data, ACTIVITY)

    sys.stdout.write(f"{hours_activity} hours {ACTIVITY} in {MONTH}\n")
    #print all activities in the month in the descending order of the duration
    #convert the dictionary to a list of tuples, sort the list by the second element in the tuple (the duration) and print it
    activities = sorted(activities.items(), key=lambda x: x[1], reverse=True)
    sys.stdout.write("All Activities:\n")
    for activity in activities:
      sys.stdout.write(f"  {activity[0]}: {activity[1]}\n")
    sys.stdout.write("\n")


    total_hours_activity+=hours_activity
  

  #print out the total time spent in the location and activity
  sys.stdout.write(f"\nTotal time in {location}: {total_hours_location}\n")
  sys.stdout.write(f"Total time {ACTIVITY}: {total_hours_activity}\n")

  #convert the columns to the correct data types
  calendar_df['Daytime_start'] = pd.to_datetime(calendar_df["Daytime_start"], errors='coerce')
  calendar_df['Daytime_end'] = pd.to_datetime(calendar_df["Daytime_end"], errors='coerce')
  calendar_df['Location'] = calendar_df['Location'].astype(str)
  calendar_df['Duration_min'] = calendar_df['Duration_min'].astype(float)

  #reset sns context and plot the calendar heatmap
  sns.set_context("notebook")
  plotCalendarHeatmap(calendar_df, location, YEAR)