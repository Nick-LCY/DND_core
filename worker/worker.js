export default {
  async fetch(request, env, _) {
    const path = new URL(request.url).pathname
    const idMatch = path.match(/^\/data\/([^\/]+)$/)
    if (idMatch) {
      console.log({ "result": "ID Matched", path })
      const dataId = path.split("/")[1]
      try {
        const data = await env.DND5E_KV_NS.get(dataId)
        return new Response(
          data,
          { headers: { 'Content-Type': 'application/json' } },
        )
      } catch (e) {
        console.error(e)
        return new Response('Not Found', { status: 404 })
      }
    }
    const typeMatch = path.match(/^\/data\/([^\/]+)\/([^\/]+)$/);
    if (typeMatch) {
      console.log({ "result": "Type Matched", path })
      const namespace = typeMatch[1];
      const resourceType = typeMatch[2];
      try {
        const indexStr = await env.DND5E_KV_NS.get(`${namespace}:index`)
        const index = JSON.parse(indexStr);
        return new Response(
          JSON.stringify(index.dirs[resourceType].files),
          { headers: { 'Content-Type': 'application/json' } },
        )
      } catch (e) {
        console.error(e)
        return new Response('Not Found', { status: 404 })
      }
    }
    console.warn({ "result": "Nothing Matched", path })
    return new Response('Not Found', { status: 404 })
  },
};