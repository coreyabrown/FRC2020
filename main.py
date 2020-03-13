import csv
import gviz_api
import os
import vari as V

team_page_template = """
<html>
  <head>
  <title>TBA Team Data</title>
    <script src="http://www.google.com/jsapi" type="text/javascript"></script>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script src="../js/frc.js"></script>
    <script>
   
    loadGoogleCharts();
      
      function drawTable() {
        %(jsteam)s
        
        var options = {
        width: 1200,
        height: 600,
        isStacked: true
        };
        
        var jsteam_table = new google.visualization.SteppedAreaChart(document.getElementById('chart_div'));
        jsteam_table.draw(jsteam_data, options);
           
      }
    </script>
  </head>
  <body>
    <H1>%(teamNumber)s - %(teamName)s Data</H1>
    <div id="chart_div"></div>
  </body>
</html>
"""

page_template = """
<html>
  <head>
  <title>TBA Data</title>
    <script src="http://www.google.com/jsapi" type="text/javascript"></script>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script src="../js/frc.js"></script>
    <script>
   
    loadGoogleCharts();

    function drawTable() {
        %(jscode)s
        %(jschart)s
        var jscode_table = new google.visualization.Table(document.getElementById('table_div_jscode'));
        jscode_table.draw(jscode_data, {allowHtml: true, showRowNumber: true, frozenColumns: 2});
        
        var options = {
        width: 1500,
        height: 1000,
        isStacked: true
        };
        
        var jschart_table = new google.visualization.BarChart(document.getElementById('chart_div'));
        jschart_table.draw(jschart_data, options);
        
        google.visualization.events.addListener(jscode_table, 'select', selectHandler);

        function selectHandler() {
            var selection = jscode_table.getSelection();
            for (var i = 0; i < selection.length; i++) {
                var item = selection[i];
                if (item.row != null && item.column != null) {
                    var str = jscode_data.getFormattedValue(item.row, item.column);
                } else if (item.row != null) {
                    var str = jscode_data.getFormattedValue(item.row, 0);
                } else if (item.column != null) {
                    var str = jscode_data.getFormattedValue(0, item.column);
                }
            }
        var teamsheet = "TBACharts_2018week0_" + str + ".html";
        //alert('You selected ' + document.getElementById("team_object").data + ' <--old. new--> ' + teamsheet);
        document.getElementById("team_object").data = teamsheet;
        document.getElementById("team_object").width = '1500px';
        document.getElementById("team_object").height = '800px';
        }
      }
    </script>
  </head>
  <body>
    <H1>TBA Table Data</H1>
    <div id="table_div_jscode" style="width: 1800; height:1200; overflow:auto;"></div>
    <div id ="team_data"> 
    <object id="team_object" type='text/html' data='' width='0' 
    height='0' style='overflow:auto;border:2px ridge blue'></object>
    </div>
    <H1>TBA Chart</H1>
    <div id="chart_div"></div>
  </body>
</html>
"""

if not os.path.exists(V.event):
    os.makedirs(V.event, 0o777)
f = open(V.csvFilePath, "w+", newline='')

teamData = csv.writer(f, quoting=csv.QUOTE_ALL)

teamData.writerow(["Team Number", "Team Name", "Number of Matches", "Ranking Points", "Win Percent", "Auto Points",
                   "Fuel Cell Points", "Color Wheel Points", "End Game Points", "Foul Points", "Average Score", "Best Match",
                   "Worst Match", "Trending Data"])

for team in V.teamObjects:
    ########## Start variables list to reset for each team ##########
    matchCount = 0
    winCount = 0
    winRP = 0
    colorRP = 0
    hangRP = 0
    auto = 0
    cellPoints = 0
    colorPoints = 0
    endGameScore = 0
    endGameStatus = 'None' # None, Park, Hang
    foulPoints = 0
    totalPoints = 0
    bestScore = 0
    worstScore = 0
    worstMatchNumber = V.NA
    bestMatchNumber = V.NA
    bestMatch = V.NA
    worstMatch = V.NA
    trendingData = {}
    dictMatch = {}
    teamNumber = getattr(team, "team_number")
    teamNameNotEncoded = getattr(team, "nickname")
    teamName = teamNameNotEncoded.encode("ascii", "replace")
    teamKey = getattr(team, "key")
    eventMatch = V.tba.team_matches(teamKey, V.event)
    ########## End variable list to reset for each team ##########

    print("Looking at team", teamNumber)

    # Look through matches
    for match in eventMatch:
        matchKey = getattr(match, "key")
        matchNumber = getattr(match, "match_number")
        matchLevel = getattr(match, "comp_level")
        matchCount += 1
        alliances = getattr(match, "alliances")
        redScore = alliances[V.red]["score"]
        blueScore = alliances[V.blue]["score"]
        winningAlliance = getattr(match, "winning_alliance")
        scoreDict = getattr(match, "score_breakdown")

        # check if played match
        if not V.isplayed(redScore, blueScore):
            break

        # which alliance is the team on
        if teamKey in alliances[V.red][V.teamKeys] or teamKey in alliances[V.red]["surrogate_team_keys"]:
            alliance = V.red
            score = redScore
            opponent = V.blue
        else:
            alliance = V.blue
            score = blueScore
            opponent = V.red
        compLevel = getattr(match, "comp_level")

        # which robot is it 1, 2, or 3 #
        robotIndex = alliances[alliance][V.teamKeys].index(teamKey)
        robotPos = int(robotIndex) + 1
        initLine = 'initLineRobot'+str(robotPos)
        climbStatus = 'endgameRobot'+str(robotPos)

        # Score breakdown below #
        if alliance == winningAlliance:
            winCount += 1
            outcome = "W"
        else:
            outcome = "L"

        # Ranking Points
        if compLevel == "qm":
            if scoreDict[alliance]["shieldEnergizedRankingPoint"]:
                hangRP += 1
            if scoreDict[alliance]["shieldOperationalRankingPoint"]:
                colorRP += 1
            if alliance == winningAlliance:
                winRP = winRP + 2
            if winningAlliance not in [V.blue, V.red]:
                winRP += 1

        # Set match numbers/scores
        matchAuto = scoreDict[alliance]["autoPoints"]
        indMobility = scoreDict[alliance][initLine]
        matchCell = scoreDict[alliance]["teleopCellPoints"]
        matchColor = scoreDict[alliance]["controlPanelPoints"]
        matchFoul = (scoreDict[opponent]["foulPoints"] * -1)
        matchPoints = alliances[alliance]["score"]
        matchEndGame = scoreDict[alliance]["endgamePoints"]
        indClimbStatus = scoreDict[alliance][climbStatus]

        # Set Trending Data
        trendingData.update({matchCount : [matchAuto + matchCell, indClimbStatus]})

        # Add Other scores
        auto = auto + matchAuto
        cellPoints = cellPoints + matchCell
        colorPoints = colorPoints + matchColor
        foulPoints = foulPoints + matchFoul
        totalPoints = totalPoints + matchPoints
        endGameScore = endGameScore + matchEndGame

        # Find best/worst match
        currentScore = alliances[alliance]["score"]
        if matchCount == 1:
            bestScore = currentScore
            worstScore = currentScore
            bestMatch = matchKey
            worstMatch = matchKey
            bestMatchNumber = ("%s-%s" % (matchLevel, matchNumber))
            worstMatchNumber = ("%s-%s" % (matchLevel, matchNumber))
        elif bestScore <= currentScore:
            bestScore = currentScore
            bestMatch = matchKey
            bestMatchNumber = ("%s%s" % (matchLevel, matchNumber))
        elif worstScore >= currentScore:
            worstScore = currentScore
            worstMatch = matchKey
            worstMatchNumber = ("%s%s" % (matchLevel, matchNumber))

        # Create match dictionaries
        dictMatchKey = ("%s%s - %s" % (matchLevel, matchNumber, outcome))

        # Determine Match Number for sorting
        if matchLevel == "qf":
            matchNumberSort = 100 + matchNumber
        elif matchLevel == "sf":
            matchNumberSort = 1000 + matchNumber
        elif matchLevel == "f":
            matchNumberSort = 10000 + matchNumber
        else:
            matchNumberSort = matchNumber

        matchList = [matchNumberSort, matchAuto, matchCell, matchColor, matchEndGame, matchFoul]
        dictMatch.update({dictMatchKey: matchList})

        # Find averages
    if matchCount > 0:
        winPercent = round((winCount / matchCount) * 100, 2)
        avgAuto = V.frc(auto, matchCount)
        avgCell = V.frc(cellPoints, matchCount)
        avgColor = V.frc(colorPoints, matchCount)
        avgEngGameScore = V.frc(endGameScore, matchCount)
        avgPoints = V.frc(totalPoints, matchCount)
        avgFoulPoints = V.frc(foulPoints, matchCount)
    else:
        winPercent = 0
        avgAuto = 0
        avgCell = 0
        avgColor = 0
        avgEngGameScore = 0
        avgPoints = 0
        avgFoulPoints = 0

    # Aggregate some data
    totalRP = winRP + hangRP + colorRP
    worstLink = V.createlink(worstMatch, worstMatchNumber)
    bestLink = V.createlink(bestMatch, bestMatchNumber)

    # Create data dictionaries for the charts
    dataList = [teamNumber, teamName, matchCount, totalRP, winPercent, avgAuto,
                avgCell, avgColor, avgEngGameScore, avgFoulPoints, avgPoints, bestLink, worstLink]
    dataChart = [avgAuto, avgCell, avgColor, avgEngGameScore, avgFoulPoints]

    # Write the row for the team
    teamData.writerow(dataList)

    V.dictList.update({teamNumber: dataList})
    V.dictChart.update({teamNumber: dataChart})

    # HTML for each team
    htmlFileTeam = ("TBACharts_%s_%s.html" % (V.event, teamNumber))
    htmlFileTeamPath = (V.event + "\\" + htmlFileTeam)
    teamDescription = {("Match Key", "string"): [("Match Number Sort", "number"),
                       ("Auto", "number"),
                       ("Cell", "number"),
                       ("Color Wheel", "number"),
                       ("End Game", "number"),
                       ("Foul Points", "number")]
                       }
    team_table = gviz_api.DataTable(teamDescription)
    team_table.LoadData(dictMatch)
    jsteam = team_table.ToJSCode("jsteam_data",
                                 columns_order=("Match Key", "Auto", "Cell",
                                                "Color Wheel", "End Game", "Foul Points"),
                                 order_by="Match Number Sort")
    hSub = open(htmlFileTeamPath, 'w')
    hSub.write("")
    hSub.write(team_page_template % vars())

    hSub.close()

f.close()

print("Data created")

# Create visualization of data
description = {("Team Number", "string"): [("Team Number", "string"),
               ("Team Name", "string"),
               ("Number of Matches", "number"),
               ("Ranking Points", "number"),
               ("Win Percent", "number"),
               ("Auto", "number"),
               ("Cell", "number"),
               ("Color Wheel", "number"),
               ("End Game", "number"),
               ("Foul Points", "number"),
               ("Average Score", "number"),
               ("Best Match", "string"),
               ("Worst Match", "string")]
               }

# get dictionary for table
data = V.dictList

# Loading it into gviz_api.DataTable
data_table = gviz_api.DataTable(description)
data_table.LoadData(data)

# Create a JavaScript code string.
jscode = data_table.ToJSCode("jscode_data",
                             columns_order=("Team Number", "Team Name", "Number of Matches", "Ranking Points",
                                            "Win Percent", "Auto", "Cell", "Color Wheel", "End Game",
                                            "Foul Points", "Average Score", "Best Match", "Worst Match"),
                             order_by="Team Number")
# Visualization Chart
descriptionChart = {("Team Number", "string"): [("Auto", "number"),
                    ("Cell", "number"),
                    ("Color Wheel", "number"),
                    ("End Game", "number"),
                    ("Foul Points", "number")]
                    }
# get dictionary for Chart
dataChart = V.dictChart
# More loading for Chart
data_table_chart = gviz_api.DataTable(descriptionChart)
data_table_chart.LoadData(dataChart)

# Data set for Chart
jschart = V.makechart(data_table_chart, "Team Number")

# Put the JS code and JSON string into the template.
h = open(V.htmlFilePath, 'w')
h.write("")
h.write(page_template % vars())

h.close()
os.system("start " + V.htmlFilePath)
print("Completed")
