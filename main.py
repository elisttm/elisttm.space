import os, asyncio, quart, hypercorn, sqlite3, time
from quart import request, redirect, url_for, render_template, send_from_directory
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
async def _projects():
    return await render_template('projects.html')

@app.route('/eli')
async def _sona():
    return await render_template('eli.html')

@app.route('/servers')
async def _servers():
    return await render_template('servers.html', time=srv.timestamp, curtime=int(time.time()))

@app.route('/servers/extra')
async def _servers_extra():
    return await render_template('servers-extra.html', time=srv.timestamp, curtime=int(time.time()))

@app.route('/gmod')
async def _gmod():
    return await render_template('servers/gmod.html', time=srv.timestamp)

@app.route('/tf2')
async def _tf2():
    return await render_template('servers/tf2.html', time=srv.timestamp)

@app.route('/mc')
async def _minecraft():
    return await render_template('servers/minecraft.html', time=srv.timestamp)

@app.route('/bot')
async def _sillybot():
    return await render_template('bot.html')

@app.route('/pack')
async def _pack():
    return await render_template('pack.html')

@app.route('/pages')
async def _pages():
    return await render_template('pages.html')


@app.route('/motd')
async def _motd():
    return await render_template('etc/motd.html')

@app.route('/connect/<server>')
async def _connect(server):
    if server not in srv.servers or srv.servers[server]["game"] not in srv.source_games:
        return quart.abort(404)
    return redirect(f"steam://connect/{srv.ip}:{srv.servers[server]['ip'][1]}/chungus", code=302)


@app.route('/index.html')
async def redirect_index():
    return redirect(url_for('_index'), code=301)

@app.route('/trashbot')
@app.route('/sillybot')
@app.route('/elibot')
async def redirect_sillybot():
    return redirect(url_for('_sillybot'), code=301)

@app.route('/sona')
@app.route('/fursona')
async def redirect_sona():
    return redirect(url_for('_sona'), code=301)

@app.route('/minecraft')
async def redirect_minecraft():
    return redirect(url_for('_minecraft'), code=301)

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
    response = quart.Response(await render_template('etc/error.html', errors={
        404: ["[404] page not found", "the url youre trying to access does not exist! you likely followed a dead link or typed something wrong"],
        500: ["[500] internal server error", "somewhere along the way there was an error processing your request. if this keeps happening, please get in contact",],
    }, error=error,), error.code)
    response.headers.set("X-Robots-Tag", "noindex")
    return response

hyperconfig = hypercorn.config.Config()
hyperconfig.bind = ["0.0.0.0:7575"]
app.jinja_env.cache = {}

if __name__ == '__main__':
    asyncio.run(hypercorn.asyncio.serve(app, hyperconfig))
