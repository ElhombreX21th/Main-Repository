"""Resumable API-style synchronization with deduplication and retry semantics."""
import argparse
import json
from pathlib import Path

class TransientError(RuntimeError):
    pass

class FixtureSource:
    """Replace with HTTP client for an authorized external API in production."""
    def __init__(self, data, failures=None):
        self.rows = data
        self.failures = dict(failures or {})
    def fetch_page(self, cursor, page_size):
        if self.failures.get(cursor, 0) > 0:
            self.failures[cursor] -= 1
            raise TransientError('Simulated HTTP 503')
        offset = int(cursor)
        page = self.rows[offset:offset+page_size]
        next_cursor = str(offset+page_size) if offset+page_size < len(self.rows) else None
        return page, next_cursor

def retry_fetch(source, cursor, page_size, attempts=3, pause=lambda seconds: None):
    for i in range(attempts):
        try:
            return source.fetch_page(cursor, page_size)
        except TransientError:
            if i == attempts-1:
                raise
            pause(min(2**i, 8))

def synchronize(source, checkpoint=None, page_size=2, attempts=3):
    state = dict(checkpoint or {'cursor':'0','records':{}})
    state['records'] = dict(state.get('records',{}))
    cursor = state.get('cursor','0')
    count=0
    while cursor is not None:
        page,next_cursor=retry_fetch(source,cursor,page_size,attempts)
        for item in page:
            if 'id' not in item or 'updated_at' not in item:
                raise ValueError('Record must include id and updated_at')
            key=str(item['id'])
            old=state['records'].get(key)
            if old is None or str(item['updated_at']) >= str(old['updated_at']):
                state['records'][key]=item
            count += 1
        cursor=next_cursor
        state['cursor']=cursor
    return state,count

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default=str(Path(__file__).with_name('source.json')))
    parser.add_argument('--state', default=str(Path(__file__).with_name('sync_state.json')))
    parser.add_argument('--page-size',type=int,default=2)
    args=parser.parse_args()
    if args.page_size < 1: parser.error('page-size must be positive')
    rows=json.loads(Path(args.input).read_text(encoding='utf-8'))
    target=Path(args.state)
    checkpoint=json.loads(target.read_text(encoding='utf-8')) if target.exists() else None
    state,count=synchronize(FixtureSource(rows),checkpoint,args.page_size)
    tmp=target.with_suffix('.tmp')
    tmp.write_text(json.dumps(state,indent=2),encoding='utf-8')
    tmp.replace(target)
    print(f'Processed {count} source events; {len(state["records"])} unique records in {target}')

if __name__ == '__main__': main()
