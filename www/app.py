#-*- coding utf-8 -*-

#async web application.

import logging; logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from datetime import datetime
from aiohttp import web
from jinja2 import Environment,FileSystemLoader
import orm
from coroweb import add_route,add_static

async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        # await asyncio.sleep(0.3)
        return (await handler(request))
    return logger

async def response_factory(app,handler):
    async def response(request):
        logging.info('Response handler...')
        r = await handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r,bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r,str):
            if r.startswith('redirect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r,dict):
            template = r.get('__template__')
            if template in None:
                resp = web.Response(body=json.dump(r,ensure_ascii=Flase,default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__template__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
        if isinstance(r,int) and r >= 100 and r < 600:
            return web.Response(r)
        if isinstance(r,tuple) and len(r) == 2:
            t,m = r
            if isinstance(t,int) and t >= 100 and t < 600:
                return web.Response(t,str(m))
        #default
        resp = web.Response(body=str(r).encode('utf-8'))
        resp.content_type = 'text/plain;charset=utf-8'
    return response


async def init(loop):
    await orm.create_pool(loop=loop,host='127.0.0.1',port=3306,user='root',password='',db='awesome')
    app = web.Application(loop=loop,middlewares=[
        logger_factory,response_factory
    ])
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_route(app,'handlers')
    app_static(app)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv
loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()