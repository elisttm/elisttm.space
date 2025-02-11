import os, asyncio, quart, hypercorn, sqlite3, time
from quart import request, redirect, render_template, send_from_directory
import servers as srv

path = os.path.dirname(os.path.realpath(__file__))+'/' # stupid

db = sqlite3.connect(f"{path}/data.db")
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS HITS (hits)")

app = quart.Quart(__name__)
app.config["BACKGROUND_TASK_SHUTDOWN_TIMEOUT "] = 0

@app.before_serving
async def startup():
    app.add_background_task = asyncio.ensure_future(srv.draw_banners())

@app.after_serving
async def shutdown():
    db.close()

@app.route('/')
async def _index():
    try:
        cur.execute("UPDATE HITS SET hits = hits + 1")
        cur.execute("SELECT hits FROM HITS")
        db.commit()
        hits = cur.fetchone()[0]
    except Exception:
        hits = None
    return await render_template('index.html', hits=hits)

@app.route('/projects')
@app.route('/eli')
@app.route('/bot')
@app.route('/pack')
@app.route('/pages')
async def _simple_page():
    return await render_template(f'{request.path[1:]}.html')

@app.route('/servers')
@app.route('/servers/extra')
async def servers():
    return await render_template(f'servers{"-extra" if "extra" in request.path else ""}.html', servers=srv.servers, time=srv.timestamp, curtime=int(time.time()))

@app.route('/gmod')
@app.route('/tf2')
@app.route('/mc')
async def _game_page():
    return await render_template(f'servers/{request.path[1:]}.html', servers=srv.servers, time=srv.timestamp)

@app.route('/motd', defaults={'game': None})
@app.route('/motd/<game>')
async def _motd(game):
    return await render_template('servers/motd.html', game=game, have_pages=srv.xtra.have_pages)

@app.route('/connect/<server>')
async def _server_connect(server):
    if server not in srv.servers or srv.servers[server]["game"] not in srv.xtra.source_games:
        return quart.abort(404)
    return redirect(f"steam://connect/{':'.join(map(str, srv.servers[server]['ip']))}/chungus", code=302)

@app.route('/info/<server>')
async def _server_info(server):
    if server not in srv.servers:
        return quart.abort(404)
    info = srv.servers[server]
    return await render_template('servers/info.html', game=server, info=info, time=srv.timestamp, xtra=srv.xtra)

@app.route('/index.html')
async def _redirect_index():
    return redirect("/", code=301)

@app.route('/trashbot')
@app.route('/sillybot')
@app.route('/elibot')
async def _redirect_sillybot():
    return redirect("/bot", code=301)

@app.route('/sona')
@app.route('/fursona')
async def _redirect_sona():
    return redirect("/eli", code=301)

@app.route('/minecraft')
async def _redirect_minecraft():
    return redirect("/mc", code=301)

@app.route('/homunculus')
async def homunculus():
    return await send_from_directory(app.static_folder, "img/homunculus.png")

@app.route('/sitemap.xml')
@app.route('/robots.txt')
@app.route('/favicon.ico')
async def static_from_root():
    return await send_from_directory(app.static_folder, request.path[1:])

@app.errorhandler(404)
@app.errorhandler(500)
async def error_handler(error):
    response = quart.Response(await render_template('error.html', errors={
        404: ["[404] page not found", "the url youre trying to access does not exist! you likely followed a dead link or typed something wrong"],
        500: ["[500] internal server error", "somewhere along the way there was an error processing your request. if this keeps happening, please get in contact asap!",],
    }, error=error,), error.code)
    response.headers.set("X-Robots-Tag", "noindex")
    return response

hyperconfig = hypercorn.config.Config()
hyperconfig.bind = ["0.0.0.0:7575"]

if __name__ == '__main__':
    asyncio.run(hypercorn.asyncio.serve(app, hyperconfig))
