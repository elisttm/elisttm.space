import os, a2s, mcstatus, time, asyncio
from PIL import Image, ImageFont, ImageDraw

ip = "73.207.108.187"
servers = {
    "gmod": {
        "game": "gmod",
        "name": "eli gmod server",
        "ip": (ip, 27015),
    },
    "sandbox": {
        "game": "gmod",
        "name": "eli sandbox server",
        "ip": (ip, 27017),
    },
    "tf2": {
        "game": "tf2",
        "name": "eli tf2 server",
        "ip": (ip, 27016),
    },
    "hldm": {
        "game": "hldm",
        "name": "eli hldm server",
        "ip": (ip, 27013),
    },
    
    # extra
    "jazz": {
        "game": "gmod",
        "name": "eli jazztronauts",
        "ip": (ip, 27041),
    },
    "sven": {
        "game": "sven",
        "name": "eli sven server",
        "ip": (ip, 27040),
    },
    "mc": {
        "game": "minecraft",
        "name": "eli smp server",
        "ip": "mc.elisttm.space",
    },
    "creative": {
        "game": "minecraft",
        "name": "creative server",
        "ip": "creative.elisttm.space",
    }
}

path = os.path.dirname(os.path.realpath(__file__))+'/' # still stupid
source_games = ("gmod", "tf2", "hldm", "sven", "l4d2")
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

class server_info(object):
    max_players = 0
    player_count = 0
    player_list = []
    subtitle = ""
    map_name = ""
    def __init__(self, player_count, max_players, player_list, subtitle, map_name):
        self.player_count = player_count
        self.max_players = max_players
        self.player_list = player_list
        self.subtitle = subtitle
        self.map_name = map_name

def query_server(server):
    game = servers[server]["game"]
    ip = servers[server]["ip"]
    playerlist = []
    try:

        if game in source_games:
            q = a2s.info(ip, 0.2)
            if q.player_count > 0:
                for player in a2s.players(ip):
                    playerlist.append({
                        "name": "unconnected" if not player.name else player.name,
                        "score": player.score,
                        "time": seconds(round(player.duration))
                    })
            map_name = (q.map_name[:16] + " ...") if len(q.map_name) > 16 else q.map_name
            subtitle = (q.game[:24] + "...") if len(q.game) > 24 else q.game
            return server_info(q.player_count, q.max_players, playerlist, subtitle, map_name)
        
        elif game == "minecraft":
            q = mcstatus.JavaServer.lookup(ip, 0.2).status()
            if q.players.sample:
                for player in q.players.sample:
                    playerlist.append({"name": player.name,})
            return server_info(q.players.online, q.players.max, playerlist, ip, q.version.name)
    except (TimeoutError, ConnectionRefusedError):
        raise TimeoutError("server offline...")
    except Exception as e:
        print(f"EXCEPTION in query_server({server}): {e}")
        return None
    

async def draw_banners():
    global timestamp
    while True:
        for server in servers:
            game = servers[server]["game"]
            try:
                query = query_server(server)
                img = Image.open(f"{path}static/img/servers/template-{game}.gif")
                draw = ImageDraw.Draw(img)
                draw.text((160, 1), f"{query.player_count}/{query.max_players}", "white", ImageFont.truetype(f"{path}static/Verdana-Bold.ttf", 11))
                draw.text((160, 15.5), query.map_name, "white", ImageFont.truetype(f"{path}static/Arial.ttf", 10))
                draw.text((34, 15.5), query.subtitle, "white", ImageFont.truetype(f"{path}static/Arial.ttf", 10))
            except TimeoutError:
                img = Image.open(f"{path}static/img/servers/template-offline.gif")
                draw = ImageDraw.Draw(img)
            except Exception as e:
                print(server, str(e))
                img = Image.open(f"{path}static/img/servers/template-error.gif")
                draw = ImageDraw.Draw(img)
            draw.text((34, 1), servers[server]['name'], "white", ImageFont.truetype(f"{path}static/Verdana-Bold.ttf", 11))
            img.save(f"{path}static/img/servers/banner-{server}.gif")
        timestamp = int(time.time())
        await asyncio.sleep(60)
