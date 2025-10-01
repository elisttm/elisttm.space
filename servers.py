import os, a2s, mcstatus, time, asyncio, requests, subprocess, json, traceback
from PIL import Image, ImageFont, ImageDraw

running = True
path = os.path.dirname(os.path.realpath(__file__))+'/' # still stupid
timestamp = 0

qstat_bin = "/usr/bin/quakestat"

ip = "73.207.108.187"
servers = {
    "sandbox": {
        "game": "gmod",
        "name": "eli sandbox server",
        "ip": (ip, 27017),
        "password": "chungus",
    },
    "gmoda": {
        "game": "gmod",
        "name": "eli gmod server A",
        "ip": (ip, 27015),
    },
    "gmodb": {
        "game": "gmod",
        "name": "eli gmod server B",
        "ip": (ip, 27018),
    },
    "jazz": {
        "game": "gmod",
        "name": "eli jazztronauts",
        "ip": (ip, 27041),
    },
    "tf2a": {
        "game": "tf2",
        "name": "eli tf2 server A",
        "ip": (ip, 27016),
    },
    "tf2b": {
        "game": "tf2",
        "name": "eli tf2 server B",
        "ip": (ip, 27019),
    },
    "tf2z": {
        "game": "tf2",
        "name": "eli tf2 server Z",
        "ip": (ip, 27043),
    },
    "hl2mp": {
        "game": "hl2mp",
        "name": "eli hl2mp server",
        "ip": (ip, 27039),
    },
    "hldm": {
        "game": "hldm",
        "name": "eli hldm server",
        "ip": (ip, 27013),
    },
    "sven": {
        "game": "sven",
        "name": "eli sven coop",
        "ip": (ip, 27040),
    },
    "smp": {
        "game": "mc",
        "name": "eli smp",
        "ip": "mc.elisttm.space",
    },
    "creative": {
        "game": "mc",
        "name": "creative server",
        "ip": "creative.elisttm.space",
    },
    "eldewrito": {
        "game": "eldewrito",
        "name": "eli halo server",
        "ip": (ip, 11775),
    },
    "haloce": {
        "game": "halo",
        "name": "eli haloce server",
        "ip": (ip, 2302),
    },
    "quake": {
        "game": "quake",
        "name": "eli qw server",
        "ip": (ip, 27049),
    }
}

qstat_games = {
    "quake": "qws",
    "halo": "gs2",
}

class xtra:
    source_games = ("gmod", "tf2", "hl2mp", "hldm", "sven")
    have_pages = ("gmod", "tf2", "mc")

    server_keys = {
        "gmod": ("sandbox", "gmoda", "gmodb"),
        "tf2": ("tf2a", "tf2b"),
        "mc": ("creative", "smp"),
    }
    
    full_names = {
        "gmod":      "Garry's Mod",
        "tf2":       "Team Fortress 2",
        "hl2mp":     "Half-Life 2: Deathmatch",
        "hldm":      "Half-Life: Deathmatch",
        "sven":      "Sven-Coop",
        "mc":        "Minecraft",
        "quake":     "QuakeWorld",
        "eldewrito": "Halo Online 0.7.1",
        "halo":      "Halo Custom Edition",
    }
    
    def tf2_gamemode(map_name):
        prefixes = {
            "arena_": "Arena",
            "ctf_":   "Capture the Flag",
            "cp_":    "Control Point",
            "koth_":  "King of the Hill",
            "mvm_":   "Mann vs. Machine",
            "pass_":  "PASS Time",
            "plr_":   "Payload Race",
            "pl_":    "Payload",
            "pd_":    "Player Destruction",
            "sd_":    "Special Delivery",
            "vsh_":   "Vs. Saxton Hale",
            "tow_":   "Tug of War",
            "zi_":    "Zombie Infection",

            "tf2ware_ultimate": "TF2Ware Ultimate"
        }
        for prefix, mode in prefixes.items():
            if map_name.lower().startswith(prefix):
                return mode
        return "Team Fortress 2"

class server_info(object):
    def __init__(self, player_count, max_players, player_list, map_name, gamemode, subtitleA, subtitleB):
        self.player_count = player_count
        self.max_players = max_players
        self.player_list = player_list
        self.map_name = map_name
        self.gamemode = gamemode
        self.subtitleA = subtitleA
        self.subtitleB = subtitleB

    def __eq__(self, other):
        if not other:
            return False
        return self.__dict__ == other.__dict__

def seconds(sec:int):
    min = hr = 0
    x = f"{sec}s"
    if sec >= 60:
        min, sec = divmod(sec, 60)
        x = f"{min}m {sec}s"
    if min >= 60:
        hr, min = divmod(min, 60)
        x = f"{hr}h {min}m {sec}s"
    return x

def truncate_str(string:str, length):
    string = str(string)
    return (string[:length] + "...") if len(string) > length else string

def parse_json(url):
    try:
        response = requests.get(url, timeout=0.2)
        response.raise_for_status()
        return response.json()
    except Exception:
        raise TimeoutError("server offline")

def qstat_query(server_address, game):
    qstat_args = [qstat_bin,'-json','-ts','-P','-R',f'-{qstat_games[game]}',server_address]
    result = subprocess.run(qstat_args, capture_output=True, text=True, check=True)
    result_json = json.loads(result.stdout)[0]
    if result_json["status"] != "online":
        raise TimeoutError("server offline")
    return result_json

def query_server(server):
    game = servers[server]["game"]
    ip = servers[server]["ip"]
    playerlist = []
    try:
        if game in xtra.source_games:
            q = a2s.info(ip, 0.3)
            if q.player_count > 0:
                for player in a2s.players(ip):
                    playerlist.append({
                        "name": truncate_str(player.name, 24) if player.name else "unconnected",
                        "score": player.score,
                        "time": seconds(round(player.duration))
                    })
            subtitleA = xtra.tf2_gamemode(q.map_name) if game == "tf2" else truncate_str(q.game, 24)
            subtitleB = truncate_str(q.map_name, 18)
            return server_info(q.player_count, q.max_players, playerlist, q.map_name, q.game, subtitleA, subtitleB)
        
        elif game == "mc":
            q = mcstatus.JavaServer.lookup(ip, 0.3).status()
            if q.players.sample:
                for player in q.players.sample:
                    playerlist.append({"name": player.name,})
            return server_info(q.players.online, q.players.max, playerlist, None, None, ip, q.version.name)

        elif game == "quake":
            q = qstat_query(':'.join(map(str, ip)), game)
            for player in q["players"]:
                playerlist.append({
                    "name": player["name"],
                    "frags": player["score"],
                    "time": seconds(int(player["time"]))
                })
            gametype = f'{q["rules"]["mode"].upper()} ({q["rules"]["status"]})'
            subtitleB = truncate_str(q["map"], 18)
            return server_info(q["numplayers"], q["maxplayers"], playerlist, q["map"], gametype, q["rules"]["*version"], subtitleB)

        elif game == "halo":
            q = qstat_query(':'.join(map(str, ip)), game)
            for player in q["players"]:
                playerlist.append({
                    "name": player["name"],
                    "score": player["score"],
                })
            subtitleA = truncate_str(q["gametype"], 24)
            subtitleB = truncate_str(q["map"], 18)
            return server_info(q["numplayers"], q["maxplayers"], playerlist, q["map"], q["gametype"], subtitleA, subtitleB)

        elif game == "eldewrito":
            q = parse_json(f"http://{':'.join(map(str, ip))}")
            for player in q["players"]:
                playerlist.append({
                    "name": f'[{player["serviceTag"]}] {player["name"]}',
                    "kills": player["kills"],
                    "deaths": player["score"],
                })
            subtitleA = truncate_str(q["variant"], 24) if q["status"] == "InGame" else "in lobby..."
            subtitleB = truncate_str(q["map"], 18) if q["status"] == "InGame" else ""
            return server_info(q["numPlayers"], q["maxPlayers"], playerlist, q["map"], subtitleA, subtitleA, subtitleB)

        return None

    except (TimeoutError, ConnectionRefusedError):
        raise TimeoutError("server offline")
    except Exception as e:
        print(f"EXCEPTION in query_server({server}): {type(e).__name__} {e}")
        #print(traceback.format_exc())
        return None

# populates servers dict with extra keys
for server in servers:
    servers[server]["query"] = None
    servers[server]["timestamp"] = None

verdana = ImageFont.truetype(f"{path}static/Verdana-Bold.ttf", 11)
arial = ImageFont.truetype(f"{path}static/Arial.ttf", 10)

async def draw_banners():
    global timestamp
    global running
    while running:
        timestamp = int(time.time())
        for server in servers.copy():
            try:
                query = query_server(server)
                if not query or query == servers[server]["query"]:
                    continue
                servers[server]["query"] = query
                servers[server]["time"] = timestamp
                img = Image.open(f"{path}static/img/servers/template-{servers[server]["game"]}.gif")
                draw = ImageDraw.Draw(img)
                draw.text((162, 1), f"{query.player_count}/{query.max_players}", "white", verdana)
                draw.text((35, 15.5), query.subtitleA, "white", arial)
                draw.text((162, 15.5), query.subtitleB, "white", arial)
            except TimeoutError:
                img = Image.open(f"{path}static/img/servers/template-offline.gif")
                draw = ImageDraw.Draw(img)
            except Exception as e:
                print(server, str(e))
                img = Image.open(f"{path}static/img/servers/template-error.gif")
                draw = ImageDraw.Draw(img)
            draw.text((35, 1), servers[server]['name'], "white", verdana)
            img.save(f"{path}static/img/servers/banner-{server}.gif")
        await asyncio.sleep(30)