import sys
import os
import signal
import asyncio
import aiohttp
import argparse
from urllib.parse import urlparse

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

BUILTIN_DOH = [
    'https://cloudflare-dns.com/dns-query',
    'https://security.cloudflare-dns.com/dns-query',
    'https://family.cloudflare-dns.com/dns-query',
    'https://dns.google/dns-query',
    'https://dns.google/resolve',
    'https://dns.quad9.net/dns-query',
    'https://dns.quad9.net:5053/dns-query',
    'https://doh.opendns.com/dns-query',
    'https://dns.adguard-dns.com/dns-query',
    'https://unfiltered.adguard-dns.com/dns-query',
    'https://family.adguard-dns.com/dns-query',
    'https://anycast.dns.nextdns.io/dns-query',
    'https://base.dns.mullvad.net/dns-query',
    'https://all.dns.mullvad.net/dns-query',
    'https://adblock.dns.mullvad.net/dns-query',
    'https://dns.controld.com/p2',
    'https://dns.alidns.com/dns-query',
    'https://common.dot.dns.yandex.net/dns-query',
    'https://dns-doh.dnsforfamily.com/dns-query',
    'https://dns0.eu/dns-query',
    'https://ada.openbld.net/dns-query',
    'https://basic.rethinkdns.com/dns-query',
    'https://child.joindns4.eu/dns-query',
    'https://child-noads.joindns4.eu/dns-query',
    'https://antivirus.bebasid.com/dns-query',
    'https://dns.bebasid.com/dns-query',
    'https://dns.bebasid.com/unfiltered',
    'https://dns.bebasid.com/dns-hagezi',
    'https://dns.bebasid.com/dns-oisd',
    'https://doh.dns.sb/dns-query',
    'https://doh.libredns.gr/dns-query',
    'https://ordns.he.net/dns-query',
    'https://dns.digitale-gesellschaft.ch/dns-query',
    'https://doh.ffmuc.net/dns-query',
    'https://doh.tiar.app/dns-query',
    'https://doh.applied-privacy.net/query',
    'https://dns.rubyfish.cn/dns-query',
    'https://freedns.controld.com/p0',
    'https://freedns.controld.com/p1',
    'https://freedns.controld.com/p2',
    'https://freedns.controld.com/p3',
    'https://freedns.controld.com/family',
    'https://public.dns.iij.jp/dns-query',
    'https://dns.switch.ch/dns-query',
    'https://doh.dnslify.com/dns-query',
    'https://doh.crypto.sx/dns-query',
    'https://jp.tiar.app/dns-query',
    'https://dns.aa.net.uk/dns-query',
    'https://doh.familyshield.opendns.com/dns-query',
    'https://dns10.quad9.net/dns-query',
]

async def check_doh(session, url, timeout, count, verbose):
    headers = {'accept': 'application/dns-message'}
    # Valid base64url encoded DNS query for www.google.com (A)
    params = {'dns': 'q80BAAABAAAAAAAAA3d3dwZnb29nbGUDY29tAAABAAE'}
    for _ in range(count):
        try:
            async with session.get(url, params=params, headers=headers, timeout=timeout, ssl=False, allow_redirects=True) as resp:
                if resp.status == 200 and 'application/dns-message' in resp.headers.get('content-type', ''):
                    return True
                if verbose:
                    sys.stderr.write(f"DEBUG: {url} status={resp.status} type={resp.headers.get('content-type')}\n")
        except Exception as e:
            if verbose:
                sys.stderr.write(f"DEBUG: {url} exception={type(e).__name__} {e}\n")
    return False

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
        # Fix: ensure path starts with /
        path = parsed.path
        if not path:
            path = '/dns-query'
        elif not path.startswith('/'):
            path = '/' + path
        
        # If path is just /, default to /dns-query
        if path == '/':
            path = '/dns-query'
            
        return f"{scheme}://{netloc}{path}"
    except:
        return None

async def worker(queue, session, timeout, count, seen, verbose):
    while True:
        try:
            url = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        
        if url is None:
            break
        if url not in seen:
            seen.add(url)
            if await check_doh(session, url, timeout, count, verbose):
                print(url)
                sys.stdout.flush()
            elif verbose:
                sys.stderr.write(f"ERR: {url}\n")
    queue.task_done()

async def main():
    # Force immediate exit on CTRL+C/SIGINT and SIGTERM
    def force_exit(sig, frame):
        os._exit(0)
    
    signal.signal(signal.SIGINT, force_exit)
    signal.signal(signal.SIGTERM, force_exit)

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--timeout', type=float, default=2.0, help='timeout (seconds)')
    parser.add_argument('-c', '--count', type=int, default=1)
    parser.add_argument('-w', '--workers', type=int, default=100)
    parser.add_argument('-b', '--builtin', action='store_true', help='probe built-in list of known DoH providers instead of stdin')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    queue = asyncio.Queue()
    seen = set()

    lines = BUILTIN_DOH if args.builtin else sys.stdin.readlines()
    for line in lines:
        url = normalize_url(line)
        if url:
            queue.put_nowait(url)

    if queue.empty():
        return

    num_workers = min(args.workers, queue.qsize())

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=num_workers)) as session:
        workers = [asyncio.create_task(worker(queue, session, args.timeout, args.count, seen, args.verbose)) for _ in range(num_workers)]
        await asyncio.gather(*workers)

def run():
    asyncio.run(main())

if __name__ == "__main__":
    run()
