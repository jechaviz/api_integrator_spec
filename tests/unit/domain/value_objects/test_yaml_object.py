import unittest

from api_integrator_spec.domain.value_objects.yaml_object import YamlObject


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
