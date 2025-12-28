import json
import os
import random

#sm, ig, sb, or, ne, cm, el, de, tu
class player :
    #raceName, win, loss
    scores = [
            ['Space Marines', 0, 1],
            ['Imperial Guard', 0, 1],
            ['Sisters of Battle', 0, 1],
            ['Orks', 0, 1],
            ['Necrons', 0, 1],
            ['Chaos Marines', 0, 1],
            ['Eldar', 0, 1],
            ['Dark Eldar', 0, 1],
            ['Tau', 0, 1]
        ] 
    name = ''
    lastRaces = [0,1,2]
    raceNumber = 0
    
    def to_dict(self):
        """Convert player object to dictionary for JSON serialization"""
        return {
            'scores': self.scores,
            'name': self.name,
            'lastRaces': self.lastRaces,
            'raceNumber': self.raceNumber
        }
    
    @staticmethod
    def from_dict(data):
        """Create player object from dictionary"""
        p = player()
        p.scores = data.get('scores', [[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0],[0,0]])
        p.name = data.get('name', '')
        p.lastRaces = data.get('lastRaces', [])
        p.raceNumber = data.get('raceNumber', 0)
        return p

    def playerRaceScore(self):
        raceWins = self.scores[self.raceNumber][1]
        raceLosses = self.scores[self.raceNumber][2]
        if raceWins == 0:
            return 0
        score = raceWins/(raceWins + raceLosses)
        return score
    
    def nextRace(self):
        self.raceNumber += 1
        if self.raceNumber == 9:
            self.raceNumber = 0
    
    def getRaceName(self):
        return self.scores[self.raceNumber][0]
    
    def raceWins(self):
        return self.scores[self.raceNumber][1]
    
    def cycleLastRaces(self):
        self.lastRaces[0] = self.lastRaces[1]
        self.lastRaces[1] = self.lastRaces[2]
        self.lastRaces[2] = self.raceNumber

    def recordWin(self):
        self.scores[self.raceNumber][1] += 1
    
    def recordLoss(self):
        self.scores[self.raceNumber][2] += 1
    
    def illegalRace(self):
        return self.raceNumber in self.lastRaces
    
    def averageScore(self):
        totalWins = 0
        totalGames = 0
        for race in self.scores:
            totalWins += race[1]
            totalGames += race[1] + race[2]
        averageScore = totalWins / totalGames
        return averageScore

##########################################################################################

def save_players(players, filename):
    """Save a list of players to a JSON file"""
    data = [p.to_dict() for p in players]
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def load_players(filename):
    """Load a list of players from a JSON file"""
    if not os.path.exists(filename):
        print(f"File {filename} not found. ")
        exit(1)
    
    with open(filename, 'r') as f:
        data = json.load(f)
    
    players = [player.from_dict(pdata) for pdata in data]
    return players

def calculateFairness(players):
    mid = len(players) // 2
    team1 = players[:mid]
    team2 = players[mid:]
    team1Score = 0
    team2Score = 0
    for player in team1:
        team1Score += player.playerRaceScore()
    for player in team2:
        team2Score += player.playerRaceScore()
    fairness = abs(team1Score - team2Score)
    return fairness

def firstRace(players):
    for player in players:
        while True:
            player.nextRace()
            if player.illegalRace() == False:
                break

    
def nextRaces(players):
    x = len(players) - 1
    while x >= 0:
        players[x].nextRace()
        if players[x].raceNumber != 0:
            break
        x -= 1

def illegalRace(players):
    for player in players:
        if player.raceNumber in player.lastRaces:
            return True
    return False

def printGame(players):
    mid = len(players) // 2
    team1 = players[:mid]
    team2 = players[mid:]
    print("Team 1:")
    for p in team1:
        print(f"{p.name} - {p.getRaceName()} - {p.playerRaceScore()}")
    print("Team 2:")
    for p in team2:
        print(f"{p.name} - {p.getRaceName()} - {p.playerRaceScore()}")
    print("fairness score: ", calculateFairness(players))

def printRaces(players):
    print(" | ".join(f"{p.getRaceName()}" for p in players))
    print(calculateFairness(players))

def printAwesome(players):
    averageScores = [[p.name, p.averageScore()] for p in players]
    averageScores.sort(key=lambda x: x[1], reverse=True)
    print("The most aweson players are:")
    for name, score in averageScores:
        print(f"{name}: {score:.2f}")
        

#get players
fullPlayers = load_players('players.json')
players=[]
notPlayingPlayers = []
for p in fullPlayers:
    response = input(f"Is {p.name} playing? (y/n): ").strip().lower()
    if response == "y":
        players.append(p)
    else:
        notPlayingPlayers.append(p)

random.shuffle(players)


firstRace(players)

#find and save fairest races
numberOfPerms = 9**len(players)
MostFair=calculateFairness(players)
save_players(players, 'mostFair.json')
n=0
while n < numberOfPerms:
    nextRaces(players)
    n += 1
    currentFairness = calculateFairness(players)
    if currentFairness < MostFair:
        # print("more fair found!")
        # printGame(players)
        if illegalRace(players):
            # print("illegal!")
            continue
        # print("more fair found!")
        # printGame(players)
        MostFair = currentFairness
        save_players(players, 'mostFair.json')

#load fairest places
players = load_players('mostFair.json')

printGame(players)

winner = input("Which team won? (1/2): ").strip()
teamSize = len(players) // 2
if winner == "1":
    startingWinningPlayer = 0
    startingLoosingPlayer = teamSize
    print("Recording win for Team 1")
elif winner == "2":
    startingWinningPlayer = teamSize
    startingLoosingPlayer = 0
    print("Recording win for Team 2")
else:
    print("Invalid input. No results recorded.")
n=0
while n < teamSize:
    players[startingWinningPlayer + n].recordWin()
    players[startingLoosingPlayer + n].recordLoss()
    n += 1

for p in players:
    p.cycleLastRaces()

fullPlayers = players + notPlayingPlayers

printAwesome(fullPlayers)

totalGames = 0
for p in fullPlayers:
    for race in p.scores:
        totalGames += race[1]
        totalGames += race[2]

save_players(fullPlayers, 'players.json')
save_players(fullPlayers, f'players_backup_{totalGames}.json')


def git_commit_and_push(files, message=None):
    """Stage, commit and push the given files if there are changes."""
    import subprocess
    try:
        # Stage files (ignore missing files)
        subprocess.run(['git', 'add'] + files, check=False)

        commit_msg = message or 'Update players data'
        res = subprocess.run(['git', 'commit', '-m', commit_msg], capture_output=True, text=True)
        if res.returncode != 0:
            out = (res.stdout or '') + (res.stderr or '')
            if 'nothing to commit' in out.lower():
                print('No changes to commit.')
                return
            print('Git commit failed:', out)
            return

        push_res = subprocess.run(['git', 'push'], capture_output=True, text=True)
        if push_res.returncode != 0:
            print('Git push failed:', push_res.stderr or push_res.stdout)
            return

        print('Committed and pushed changes to remote.')
    except Exception as e:
        print('Git operation failed:', e)


# Attempt to commit and push the updated JSON files
git_files = ['players.json', f'players_backup_{totalGames}.json', 'mostFair.json']
git_commit_and_push(git_files, message=f'Update players data after {totalGames} games')