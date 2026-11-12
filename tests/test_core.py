import unittest,copy,json
from sqlite_outbox_crash_lab import run
DEMO={'operation_key': 'order-1', 'value': 'synthetic', 'crash_after_remote_commit': True}
class DomainTests(unittest.TestCase):
 def test_lost_ack_duplicates_naive_effect(self):
  x=run(DEMO)['experiments'];self.assertEqual(x['naive']['child_exit'],23);self.assertFalse(x['naive']['local_ack_after_child']);self.assertEqual(x['naive']['effects_after_retry'],2);self.assertEqual(x['idempotent']['effects_after_retry'],1)
 def test_no_crash_needs_no_retry(self):
  x=run(dict(DEMO,crash_after_remote_commit=False))['experiments'];self.assertEqual(x['naive']['effects_after_retry'],1);self.assertFalse(x['naive']['retry_performed'])
 def test_caller_data_not_shell(self):
  x=run(dict(DEMO,value="'; drop table effects;--"));self.assertEqual(x['experiments']['idempotent']['effects_after_retry'],1)
