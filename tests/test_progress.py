import threading

import pytest

from powerspec.utils.progress import Progress


def test_events_record_real_outcome_and_elapsed_time():
    events = []
    clock = [10.0]
    with Progress(events.append, clock=lambda: clock[0]) as progress:
        with progress.stage('export') as task:
            clock[0] = 12.5
            task.result('reused', 'same digest')
    assert [(e.label, e.state) for e in events] == [('export', 'started'), ('export', 'reused')]
    assert events[-1].elapsed == 2.5
    assert events[-1].detail == 'same digest'


def test_waits_follow_innermost_stage_and_stop_after_exit():
    events = []
    waiting = threading.Event()
    def observe(event):
        events.append(event)
        if event.state == 'waiting':
            waiting.set()
    before = set(threading.enumerate())
    with Progress(observe, interval=.02) as progress:
        with progress.stage('backup'):
            with progress.stage('upload'):
                assert waiting.wait(2)
            waiting.clear()
            assert waiting.wait(2)
    waits = [event for event in events if event.state == 'waiting']
    assert waits[0].label == 'upload'
    assert waits[-1].label == 'backup'
    assert all(event.elapsed >= .02 for event in waits)
    assert not any(thread.name == 'operation-progress' for thread in set(threading.enumerate()) - before)
    for name in ('upload', 'backup'):
        states = [event.state for event in events if event.label == name]
        assert states[0] == 'started' and states[-1] == 'done'


@pytest.mark.parametrize('failure,expected', [(ValueError('network unavailable'), 'failed'),
                                           (KeyboardInterrupt(), 'cancelled')])
def test_failure_propagates_and_stops_observer(failure, expected):
    events = []
    with pytest.raises(type(failure)):
        with Progress(events.append, interval=.01) as progress:
            with progress.stage('upload'):
                raise failure
    assert events[-1].state == expected
    assert events[-1].label == 'upload'
    assert not any(thread.name == 'operation-progress' for thread in threading.enumerate())


def test_broken_observer_cannot_change_operation_result():
    def broken(event):
        raise OSError('closed log')
    with Progress(broken) as progress:
        with progress.stage('write archive'):
            result = 'archive saved'
    assert result == 'archive saved'


@pytest.mark.parametrize('interval', [0, -1, float('inf'), float('nan')])
def test_invalid_cadence_rejected(interval):
    with pytest.raises(ValueError):
        Progress(interval=interval)


def test_no_observer_starts_no_thread(capsys):
    before = set(threading.enumerate())
    with Progress() as progress:
        with progress.stage('offline'):
            assert set(threading.enumerate()) == before
    assert capsys.readouterr() == ('', '')


def test_paused_observation_suppresses_waits_until_resumed():
    import time
    events = []
    resumed = threading.Event()
    def observe(event):
        events.append(event)
        if event.state == 'waiting':
            resumed.set()
    with Progress(observe, interval=.02) as progress:
        with progress.stage('confirm'):
            with progress.paused():
                time.sleep(.1)
                assert not any(event.state == 'waiting' for event in events)
            assert resumed.wait(2)
    assert [event.state for event in events][-1] == 'done'
