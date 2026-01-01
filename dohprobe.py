import sys
import os
import asyncio
import aiohttp
import argparse
from urllib.parse import urlparse

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

async def check_doh(session, url, timeout, count):
    headers = {'accept': 'application/dns-message'}
    params = {'dns': 'q80BAAABAAAAAAAAA3d3dwdnb29nbGUDY29tAAABAAE'}
    for _ in range(count):
        try:
            async with session.get(url, params=params, headers=headers, timeout=timeout, ssl=False, allow_redirects=True) as resp:
                if resp.status == 200 and 'application/dns-message' in resp.headers.get('content-type', ''):
                    continue
                return False
        except:
            return False
    return True

def normalize_url(input_str):
    input_str = input_str.strip()
    if not input_str:
        return None
    if '://' not in input_str:
        input_str = 'https://' + input_str
    try:
        parsed = urlparse(input_str)
        scheme = parsed.scheme if parsed.scheme in ['http', 'https'] else 'https'
        netloc = parsed.netloc or parsed.path.split('/')[0]
        path = parsed.path if parsed.netloc else ('/' + '/'.join(parsed.path.split('/')[1:]) if '/' in parsed.path else '')
        if not path or path == '/':
            path = '/dns-query'
        return f"{scheme}://{netloc}{path}"
    except:
        return None

async def worker(queue, session, timeout, count, seen):
    while True:
        url = await queue.get()
        if url is None:
            queue.task_done()
            break
        if url not in seen:
            seen.add(url)
            if await check_doh(session, url, timeout, count):
                print(url)
                sys.stdout.flush()
            else:
                sys.stderr.write(f"ERR: {url}\n")
        queue.task_done()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--timeout', type=float, default=0.5)
    parser.add_argument('-c', '--count', type=int, default=3)
    parser.add_argument('-w', '--workers', type=int, default=100)
    args = parser.parse_args()

    queue = asyncio.Queue()
    seen = set()
    
    for line in sys.stdin:
        url = normalize_url(line)
        if url:
            queue.put_nowait(url)

    if queue.empty():
        return

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=args.workers)) as session:
        workers = [asyncio.create_task(worker(queue, session, args.timeout, args.count, seen)) for _ in range(args.workers)]
        await queue.join()
        for _ in range(args.workers):
            await queue.put(None)
        await asyncio.gather(*workers)

def run():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        os._exit(0)

if __name__ == "__main__":
    run()
