import os, asyncio, quart, hypercorn, pickle, datetime
from quart import request, redirect, render_template, send_from_directory
import servers as srv

path = os.path.dirname(os.path.realpath(__file__))+'/' # stupid
app = quart.Quart(__name__)

server_info = srv.server_info
def get_queries():
    with open("servers.dat", "rb") as f:
        return pickle.load(f)

def find_crawlers(request): # TEMPORARY! trying to collect non-identified crawler/spam analytics
    try:
        if any(x in request.headers.get("User-Agent").lower() for x in ("eli.toys", "192.168")) not in request.headers.get("Referer").lower() and request.headers.get("User-Agent") and not any(x in request.headers.get("User-Agent").lower() for x in ("bot","search","scan","crawl")):
            crawl_log = f"{request.path} :: {request.headers.get("User-Agent")} :: {request.headers.get("Referer")}"
            print(crawl_log)
            with open("crawlers.txt", "a") as file:
                file.write(f"{crawl_log}\n")
        return
    except Exception:
        return None

def get_age():
    born = datetime.datetime(2005, 2, 10)
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

print(get_age())

@app.before_request
async def run_before_request():
    find_crawlers(request)

# regular pages

@app.route('/')
async def _index():
    return await render_template('index.html')

@app.route('/about')
@app.route('/projects')
@app.route('/eli')
@app.route('/links')
@app.route('/donate')
async def _simple_page():
    return await render_template(f'{request.path[1:]}.html')

# server pages

@app.route('/servers')
@app.route('/servers/all')
async def _servers():
    return await render_template(f'servers{"-all" if "all" in request.path else ""}.html', servers=srv.servers, queries=get_queries(), source_games=srv.xtra.source_games)

@app.route('/gmod')
@app.route('/tf2')
@app.route('/mc')
async def _game_page():
    return await render_template(f'servers/{request.path[1:]}.html', servers=srv.servers, queries=get_queries(), server_keys=srv.xtra.server_keys)

@app.route('/motd', defaults={'game': None})
@app.route('/motd/<game>')
async def _motd(game):
    return await render_template('servers/motd.html', game=game, servers=srv.servers, queries=get_queries(), server_keys=srv.xtra.server_keys)

@app.route('/connect/<server>')
async def _server_connect(server):
    if server not in srv.servers or srv.servers[server]["game"] not in srv.xtra.source_games:
        return quart.abort(404)
    return redirect(f"steam://connect/{':'.join(map(str, srv.servers[server]['ip']))}/chungus", code=302)

@app.route('/info/<server>')
async def _server_info(server):
    if server not in srv.servers:
        return quart.abort(404)
    return await render_template('servers/info.html', game=server, info=srv.servers[server], query=get_queries()[server], xtra=srv.xtra)

# redirects / extra paths

@app.route('/index.html')
async def _redirect_index():
    return redirect("/", code=301)

@app.route('/trashbot')
@app.route('/sillybot')
@app.route('/elibot')
@app.route('/bot')
@app.route('/pack')
async def _redirect_projects():
    return redirect("/projects", code=301)

@app.route('/sona')
@app.route('/fursona')
async def _redirect_sona():
    return redirect("/eli", code=301)

@app.route('/minecraft')
async def _redirect_minecraft():
    return redirect("/mc", code=301)

@app.route('/homunculus')
async def _homunculus():
    return await send_from_directory(app.static_folder, "img/homunculus.png")

@app.route('/favicon.ico')
@app.route('/robots.txt')
@app.route('/sitemap.xml')
async def _static_from_root():
    return await send_from_directory(app.static_folder, request.path[1:])

@app.route('/.well-known/<file_name>')
async def _well_known(file_name):
    return await send_from_directory(f"{app.static_folder}/.well-known/", file_name)

@app.errorhandler(404)
@app.errorhandler(500)
async def _error_handler(error):
    response = quart.Response(await render_template('error.html', error=error,), error.code)
    response.headers.set("X-Robots-Tag", "noindex")
    return response

# webserver

hyperconfig = hypercorn.config.Config()
hyperconfig.bind = ["0.0.0.0:7574"]

if __name__ == '__main__':
    asyncio.run(hypercorn.asyncio.serve(app, hyperconfig))
