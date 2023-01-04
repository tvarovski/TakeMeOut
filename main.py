import code.config as cfg
import code.takeMeOut as tmo

if __name__ == "__main__":

  #open the config file
  DIR = cfg.settings['DIR']
  YEAR = cfg.settings['YEAR']
  LOCATION = cfg.settings['LOCATION']
  LATITUDE = cfg.settings['LATITUDE']
  LONGITUDE = cfg.settings['LONGITUDE']
  RADIUS = cfg.settings['RADIUS']
  ACTIVITY = cfg.settings['ACTIVITY']
  
  #run the analysis and save the stdout to a file
  tmo.runAnalysis(DIR, YEAR, LOCATION, LATITUDE, LONGITUDE, RADIUS, ACTIVITY)