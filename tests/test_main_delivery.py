"""Main updates qualify exact immutable sources, never version-only release aliases."""
import copy
import json
import unittest
from unittest.mock import patch
from test_home import home, INFO, LOCK


class MainDeliveryTests(unittest.TestCase):
    def evidence(self):
        workflow=dict(id=10,path='.github/workflows/check.yml',state='active')
        run=dict(id=1,run_number=2,run_attempt=1,workflow_id=10,head_sha=INFO['rev'],
                 head_branch='main',event='push',path=workflow['path'],
                 repository={'full_name':home.REPOSITORY},head_repository={'full_name':home.REPOSITORY},
                 status='completed',conclusion='success')
        jobs=dict(total_count=1,jobs=[dict(name='CI gate',head_sha=INFO['rev'],status='completed',conclusion='success')])
        return [workflow,dict(total_count=1,workflow_runs=[run]),run,jobs,copy.deepcopy(run)]

    def test_exact_ci_and_latest_attempt_required(self):
        with patch.object(home,'github_api',side_effect=self.evidence()):
            self.assertEqual(home.require_main_ci(INFO['rev'])['runAttempt'],1)
        for changes in ({'head_sha':'b'*40},{'event':'pull_request'}, {'path':'.github/workflows/other.yml'},
                        {'repository':{'full_name':'other/foundation'}},{'head_repository':{'full_name':'other/foundation'}},
                        {'status':'in_progress'}, {'conclusion':'failure'}, {'run_attempt':0}):
            data=self.evidence(); data[2]={**data[2],**changes}
            with self.subTest(changes=changes), patch.object(home,'github_api',side_effect=data):
                with self.assertRaises(ValueError): home.require_main_ci(INFO['rev'])
        for index in (1,3):
            data=self.evidence(); data[index]['total_count']=101
            with patch.object(home,'github_api',side_effect=data):
                with self.assertRaises(ValueError): home.require_main_ci(INFO['rev'])
        data=self.evidence(); data[3]['jobs'][0]['head_sha']='b'*40
        with patch.object(home,'github_api',side_effect=data):
            with self.assertRaises(ValueError): home.require_main_ci(INFO['rev'])
        data=self.evidence(); data[1]['workflow_runs'].append({**data[2],'id':2,'run_number':3}); data[1]['total_count']=2
        data[2]={**data[2],'id':2,'run_number':3,'conclusion':'failure'}
        with patch.object(home,'github_api',side_effect=data):
            with self.assertRaises(ValueError): home.require_main_ci(INFO['rev'])

    def test_rerun_or_status_change_after_attempt_jobs_rejects_stale_success(self):
        for changes in ({'run_attempt':2}, {'status':'in_progress'}, {'conclusion':'failure'}):
            data=self.evidence(); data[4].update(changes)
            with patch.object(home,'github_api',side_effect=data):
                with self.assertRaisesRegex(ValueError,'changed while checking jobs'):
                    home.require_main_ci(INFO['rev'])

    def test_candidate_requires_same_current_successful_proof(self):
        evidence={'runId':1,'runAttempt':1}
        info={**INFO,'upstreamCI':evidence}
        with patch.object(home,'require_main_ci',return_value=evidence):
            home.revalidate_candidate(info)
        for replacement in ({'runId':1,'runAttempt':2},{'runId':2,'runAttempt':1}):
            with patch.object(home,'require_main_ci',return_value=replacement):
                with self.assertRaisesRegex(ValueError,'changed during preparation'):
                    home.revalidate_candidate(info)
        with patch.object(home,'require_main_ci') as qualify:
            with self.assertRaises(ValueError): home.revalidate_candidate(INFO)
            qualify.assert_not_called()

    def test_main_resolved_once_then_read_by_immutable_revision(self):
        locked={**{k:INFO[k] for k in ('rev','narHash','lastModified')},**home.foundation_reference('main')}
        data={**INFO,'metadata':{k:INFO[k] for k in ('schema','compatibility','version')},'lock':LOCK}
        with patch.object(home,'capture',side_effect=[json.dumps({'locked':locked}),json.dumps(data)]) as capture, patch.object(home,'require_main_ci',return_value={'runId':1,'runAttempt':1}) as ci:
            self.assertEqual(home.main_data(),({**INFO,"upstreamCI":{"runId":1,"runAttempt":1}},LOCK))
        self.assertIn('--refresh',capture.call_args_list[0].args[0])
        self.assertIn('/'+INFO['rev'],capture.call_args_list[1].args[0][-1])
        ci.assert_called_once_with(INFO['rev'])
        with patch.object(home,'capture',side_effect=[json.dumps({'locked':locked}),json.dumps({**data,'narHash':'sha256-'+'B'*43+'='})]), patch.object(home,'require_main_ci'):
            with self.assertRaisesRegex(ValueError,'differs'): home.main_data()

    def test_same_version_new_revision_updates_but_backward_history_does_not(self):
        candidate={**INFO,'rev':'b'*40}
        with patch.object(home,'installed_info',return_value=INFO), patch.object(home,'foundation_source',return_value={}), patch.object(home,'main_data',return_value=(candidate,LOCK)):
            with patch.object(home,'github_api',return_value={'status':'ahead','merge_base_commit':{'sha':INFO['rev']}}):
                self.assertEqual(home.available(None)[1],candidate)
            for status in ('behind','diverged','identical'):
                with patch.object(home,'github_api',return_value={'status':status,'merge_base_commit':{'sha':INFO['rev']}}):
                    with self.assertRaises(ValueError): home.available(None)


if __name__=='__main__': unittest.main()
