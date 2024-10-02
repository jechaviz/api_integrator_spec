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


class TestYamlObject(unittest.TestCase):
    def test_access_nested_data(self):
        data = {
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
        yaml_object = YamlObject(data)

        self.assertEqual(yaml_object.a, 1)
        self.assertEqual(yaml_object.b.c, 2)
        self.assertEqual(yaml_object.b.d, 3)
        self.assertEqual(yaml_object.e[0].f, 4)
        self.assertEqual(yaml_object.e[1], 5)

    def test_access_non_existent_data(self):
        data = {"a": 1}
        yaml_object = YamlObject(data)

        with self.assertRaises(AttributeError) as context:
            yaml_object.b

        self.assertEqual(str(context.exception), "'YamlObject' object has no attribute 'b'")

    def test_to_dict(self):
        data = {"a": 1}
        yaml_object = YamlObject(data)
        self.assertEqual(yaml_object.to_dict(), data)

        data = {"a": 1, "b": {"c": 2}}
        yaml_object = YamlObject(data)
        self.assertEqual(yaml_object.to_dict(), data)

        data = {"a": 1, "b": [{"c": 2}, 3]}
        yaml_object = YamlObject(data)
        self.assertEqual(yaml_object.to_dict(), data)
