schedule = SchedulesDirect('user', 'pass')

print("Logging in to SchedulesDirect...")
if schedule.get_randhash():
    print("Successfully got random hash.")
else:
    print("Unable to get hash key. Exit.")
    sys.exit(-1)
    
print("Checking if server is allowing connections...")
if schedule.get_status():
    print("Server is allowing connections.")
else:
    print("Server is not accepting connections. Exit.")
    sys.exit(-1)
    
print("Getting available headends for 12207.")

# Seriously... don't iterate this way
for headend in schedule.get_headends(12207)['data']:
    print ("   Found: " + headend['name'])
    
#print("Adding headends for Cable ONE and Dish Network...")
#schedule.add_headend('WA11430')
#schedule.add_headend('DISH881')
    
print("Checking for subscribed headends...")
lineup_headends = []

# I'm serious, don't ever iterate this way
for headend in schedule.get_subscribed_headends()['data']:
    print("   Found: " + headend['name'])
    lineup_headends.append(headend['headend'])
    
print("Getting lineups for all subscribed headends...")
lineups = schedule.get_lineups(lineup_headends)

print("Generating a list of stations...")
stations = []
for content in lineups.read():
    print("   Parsing data for " + lineups.file_name)
    for device in content['deviceTypes']:
        for station in content[device]['map']:
            stations.append(station['stationID'])

print("      Found " + str(len(stations)) + " stations on all headends.")
print("Randomly selecting 50 stations to download data from.")

selected_stations = []
for i in sample(range(0, (len(stations) - 1)), 10):
    selected_stations.append(stations[i])

print("Downloading schedule data from selected stations.")
schedules = schedule.get_schedules(selected_stations)

print("Parsing schedule data for selected stations...")

selected_programs = []
for programs in schedules.read():
    print("   Parsing data for " + schedules.file_name)
    print("   Saving the first program from station " + schedules.file_name + ".")
    selected_programs.append(programs[0]['programID'])
    
print("Downloading the first program from each station")
program = schedule.get_programs(selected_programs)

for show in program.read():
    print("   Parsing data for " + program.file_name)
    print("      Found show \"" + show['titles']['title120'] + "\"")
