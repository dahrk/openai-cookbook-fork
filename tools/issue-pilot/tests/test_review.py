import base64
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import pilot

HEAD='a'*40
BASE='b'*40
ISSUE={'number':6,'body':'### Pilot outcome\n\nReview a pull request with GPT-6 Luna\n\n### Pull request number\n\n5\n\n### Review focus\n\nRemove only the empty heading and preserve links.'}
RESULT={'summary':'The patch removes only the empty heading and redundant whitespace.', 'findings':[], 'limitations':'Static inspection only. No links, code or CI were executed.'}

class API:
    repo=pilot.TARGET_REPO
    def __init__(self):
        self.pr={'state':'open','changed_files':1,'base':{'sha':BASE,'repo':{'full_name':self.repo}},'head':{'sha':HEAD,'repo':{'full_name':self.repo}}}
        self.files=[{'filename':'README.md','patch':'@@ -1,3 +1 @@\n-<h3></h3>\n- \n Keep [link](https://example.test).'}]
        self.reviews=[];self.posts=[];self.reads=0;self.move_head=False
    def pages(self,path):
        return self.files if path.endswith('/files') else self.reviews
    def call(self,path,data=None):
        if path=='/pulls/5':
            self.reads+=1
            pr=deepcopy(self.pr)
            if self.move_head and self.reads>1:pr['head']['sha']='c'*40
            return pr
        if path.startswith('/contents/README.md?ref='):
            content='Keep [link](https://example.test).\n'
            if path.endswith(BASE):content='<h3></h3>\n \n'+content
            return {'type':'file','encoding':'base64','size':len(content),'content':base64.b64encode(content.encode()).decode()}
        if path=='/pulls/5/reviews':
            self.posts.append(data)
            return {'html_url':'https://github.com/dahrk/openai-cookbook-fork/pull/5#pullrequestreview-test'}
        raise AssertionError('Unexpected API operation: '+path)

class ReviewTests(unittest.TestCase):
    def run_review(self,api,result=RESULT):
        with tempfile.TemporaryDirectory() as directory:
            args=SimpleNamespace(output=directory,telemetry=SimpleNamespace(boundary=lambda *a:None))
            with patch('pilot.CodexBrain') as brain, patch('pilot.terminal_outcome') as terminal:
                brain.return_value.review.return_value=deepcopy(result)
                pilot.review_pull_request(args,api,ISSUE)
                report=Path(directory,'review.json').read_text()
                return brain,terminal,report
    def test_focused_review_publishes_comment_at_exact_head_then_stops_for_human(self):
        api=API();brain,terminal,report=self.run_review(api)
        evidence=brain.return_value.review.call_args.args[0]
        self.assertIn('preserve links',evidence['focus'])
        self.assertEqual(evidence['head_sha'],HEAD)
        self.assertIn('<h3>',evidence['base_content'])
        self.assertNotIn('<h3>',evidence['head_content'])
        self.assertEqual(len(api.posts),1)
        self.assertEqual(api.posts[0]['event'],'COMMENT')
        self.assertEqual(api.posts[0]['commit_id'],HEAD)
        self.assertIn('No concrete findings',api.posts[0]['body'])
        self.assertIn('Advisory comment review only',api.posts[0]['body'])
        self.assertEqual(terminal.call_args.args[1],'needs_human_review')
        self.assertIn('PR #5',terminal.call_args.args[2])
        self.assertIn('review_url',report)
    def test_closed_foreign_and_non_readme_prs_fail_before_inference_or_publication(self):
        for kind in ('closed','foreign','multiple','path','missing_patch'):
            api=API()
            if kind=='closed':api.pr['state']='closed'
            if kind=='foreign':api.pr['head']['repo']['full_name']='someone/else'
            if kind=='multiple':api.pr['changed_files']=2
            if kind=='path':api.files[0]['filename']='code.py'
            if kind=='missing_patch':api.files[0].pop('patch')
            with patch('pilot.CodexBrain') as brain,self.assertRaises(ValueError):self.run_review(api)
            brain.assert_not_called();self.assertEqual(api.posts,[])
    def test_changed_head_refuses_stale_review(self):
        api=API();api.move_head=True
        with self.assertRaisesRegex(RuntimeError,'changed during review'):self.run_review(api)
        self.assertEqual(api.posts,[])
    def test_invalid_finding_is_never_published(self):
        for finding in ({'severity':'high','path':'other.py','line':1,'message':'Wrong path'}, {'severity':'low','path':'README.md','line':99,'message':'Out of range'}):
            api=API()
            with self.assertRaises(ValueError):self.run_review(api,{**RESULT,'findings':[finding]})
            self.assertEqual(api.posts,[])
    def test_retry_recovers_only_own_comment_review_at_the_same_head(self):
        api=API();api.reviews=[{'body':f'<!-- issue-pilot:agent-review:6:{HEAD} -->','commit_id':HEAD,'state':'COMMENTED','user':{'login':'github-actions[bot]'},'html_url':'https://github.com/dahrk/openai-cookbook-fork/pull/5#old'}]
        brain,terminal,report=self.run_review(api)
        brain.assert_not_called();self.assertEqual(api.posts,[])
        self.assertIn('"recovered": true',report)
    def test_form_requires_explicit_review_target(self):
        self.assertEqual(pilot.issue_outcome(ISSUE),'review')
        self.assertEqual(pilot.review_request(ISSUE)[0],5)
        for body in ('', '### Pull request number\n\nhttps://outside.test/5', '### Pull request number\n\n0'):
            with self.assertRaises(ValueError):pilot.review_request({'body':body})

if __name__=='__main__':unittest.main()
