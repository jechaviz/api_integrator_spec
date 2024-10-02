import pytest

from api_integrator_spec.domain.value_objects.yaml_object import YamlObject


@pytest.fixture
def yaml_object_data():
    return {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3,
        },
        "e": [
            {"f": 4},
            5,
        ],
    }


@pytest.fixture
def yaml_object(yaml_object_data):
    return YamlObject(yaml_object_data)


def test_access_nested_data(yaml_object):
    assert yaml_object.a == 1
    assert yaml_object.b.c == 2
    assert yaml_object.b.d == 3
    assert yaml_object.e[0].f == 4
    assert yaml_object.e[1] == 5


def test_access_non_existent_data(yaml_object_data):
    yaml_object = YamlObject(yaml_object_data)
    with pytest.raises(AttributeError) as excinfo:
        yaml_object.b
    assert str(excinfo.value) == "'YamlObject' object has no attribute 'b'"


def test_to_dict(yaml_object_data):
    yaml_object = YamlObject(yaml_object_data)
    assert yaml_object.to_dict() == yaml_object_data