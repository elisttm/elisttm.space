import os, a2s, mcstatus, time, asyncio
from PIL import Image, ImageFont, ImageDraw

ip = "73.207.108.187"
servers = {
    "sandbox": {
        "game": "gmod",
        "name": "eli sandbox server",
        "ip": (ip, 27017),
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
    }
}

class xtra:
    source_games = ("gmod", "tf2", "hl2mp", "hldm", "sven")
    have_pages = ("gmod", "tf2", "mc")

    server_keys = {
        "gmod": ("sandbox", "gmoda", "gmodb"),
        "tf2": ("tf2a", "tf2b", "tf2z"),
        "mc": ("creative", "smp"),
        "hl2mp": ("hl2mp"),
    }
    
    full_names = {
        "gmod":  "Garry's Mod",
        "tf2":   "Team Fortress 2",
        "hl2mp": "Half-Life 2: Deathmatch",
        "hldm":  "Half-Life: Deathmatch",
        "sven":  "Sven-Coop",
        "mc":    "Minecraft",
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
    max_players = 0
    player_count = 0
    player_list = []
    subtitleA = ""
    subtitleB = ""
    map_name = ""
    gamemode = ""
    version = ""
    game = ""
    def __init__(self, player_count, max_players, player_list, map_name, gamemode, subtitleA, subtitleB):
        self.player_count = player_count
        self.max_players = max_players
        self.player_list = player_list
        self.map_name = map_name
        self.gamemode = gamemode
        self.subtitleA = subtitleA
        self.subtitleB = subtitleB


path = os.path.dirname(os.path.realpath(__file__))+'/' # still stupid
timestamp = 0

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

def truncate_str(string, length):
    return (string[:length] + "...") if len(string) > length else string

def query_server(server):
    game = servers[server]["game"]
    ip = servers[server]["ip"]
    playerlist = []
    try:
        if game in xtra.source_games:
            q = a2s.info(ip, 0.2)
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
            q = mcstatus.JavaServer.lookup(ip, 0.2).status()
            if q.players.sample:
                for player in q.players.sample:
                    playerlist.append({"name": player.name,})
            return server_info(q.players.online, q.players.max, playerlist, None, None, ip, q.version.name)
        
    except (TimeoutError, ConnectionRefusedError):
        raise TimeoutError("server offline")
    except Exception as e:
        print(f"EXCEPTION in query_server({server}): {e}")
        return None

verdana = ImageFont.truetype(f"{path}static/Verdana-Bold.ttf", 11)
arial = ImageFont.truetype(f"{path}static/Arial.ttf", 10)

async def draw_banners():
    global timestamp
    while True:
        for server in servers.copy():
            servers[server]["query"] = None
            try:
                query = query_server(server)
                if not query:
                    continue
                servers[server]["query"] = query
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
        timestamp = int(time.time())
        await asyncio.sleep(60)
