import pytest
from pydantic import ValidationError
from powerspec.catalog import validate, ConfigurationError
from powerspec.models import ConsumerConfig, Variables


@pytest.mark.parametrize('kind,data', [
    ('profile', {'global': 'true'}),
    ('profile', {'scope': 'user', 'typo': []}),
    ('trait', {'hooks': ['sessionStart'], 'body': 12}),
    ('context', {'attach': {'context': [{'body': 'x', 'id': 7}]}}),
    ('context', {'compiletime': [{'id': 'x', 'type': 'integer', 'default': True}]}),
    ('context', {'compiletime': [{'id': 'x', 'type': 'string', 'choices': [7]}]}),
    ('context', {'compiletime': [{'id': 'x', 'type': 'string', 'choices': ['a'], 'default': 'b'}]}),
])
def test_strict_configuration_boundary(kind, data):
    with pytest.raises(ConfigurationError):
        validate(kind, data)


def test_arbitrary_variable_names_and_values_remain_data():
    validate('profile', {'vars': {'when': 'missing_callback()', 'which': False, 'nested': {'a': [1]}}})


def test_consumer_aliases_and_temporal_boundary():
    data = {'profile': '@builtin/example', 'exclude-profiles': ['@builtin/other'],
            'vars': {'language': 'python'}, '_change': {'one': {'choice': False}}}
    config = ConsumerConfig.model_validate(data)
    assert config.changes == {'one': {'choice': False}}
    assert config.exclude_profiles == ['@builtin/other']
    assert config.model_dump(by_alias=True, exclude_unset=True) == data
    with pytest.raises(ValidationError):
        Variables.model_validate(data)
    with pytest.raises(ValidationError):
        ConsumerConfig.model_validate({'vars': [], 'extra': True})
