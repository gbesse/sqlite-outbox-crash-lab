import sqlite3,tempfile,subprocess,sys
from pathlib import Path
from .common import identifier
CHILD="""import sqlite3,sys,os
remote,local,key,value,mode,crash=sys.argv[1:]
with sqlite3.connect(remote)as db:db.execute(('insert or ignore'if mode=='idempotent'else'insert')+' into effects(op,value)values(?,?)',(key,value))
if crash=='yes':os._exit(23)
with sqlite3.connect(local)as db:db.execute('update outbox set acknowledged=1 where op=?',(key,))
"""
def run(data):
 key=identifier(data['operation_key']);value=identifier(data['value']);crash=data.get('crash_after_remote_commit',True)
 if not isinstance(crash,bool):raise ValueError('crash')
 output={}
 with tempfile.TemporaryDirectory(prefix='outbox-lab-')as tmp:
  for mode in ['naive','idempotent']:
   remote=str(Path(tmp)/(mode+'-remote.db'));local=str(Path(tmp)/(mode+'-local.db'))
   with sqlite3.connect(remote)as db:db.execute('create table effects(id integer primary key,op text'+(' unique'if mode=='idempotent'else'')+',value text)')
   with sqlite3.connect(local)as db:db.execute('create table outbox(op text primary key,acknowledged integer)');db.execute('insert into outbox values(?,0)',(key,))
   child=subprocess.run([sys.executable,'-I','-c',CHILD,remote,local,key,value,mode,'yes'if crash else'no'],capture_output=True,timeout=10)
   if child.returncode not in [0,23]:raise ValueError('child_failure')
   with sqlite3.connect(local)as db:ack=db.execute('select acknowledged from outbox').fetchone()[0]
   with sqlite3.connect(remote)as db:
    before=db.execute('select count(*)from effects').fetchone()[0]
    if not ack:db.execute(('insert or ignore'if mode=='idempotent'else'insert')+' into effects(op,value)values(?,?)',(key,value))
    after=db.execute('select count(*)from effects').fetchone()[0]
   output[mode]={'child_exit':child.returncode,'local_ack_after_child':bool(ack),'effects_before_retry':before,'effects_after_retry':after,'retry_performed':not bool(ack)}
 return {'experiments':output,'real_child_processes':True,'external_provider_called':False,'requires_remote_idempotency':True}
