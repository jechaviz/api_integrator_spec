from api_integrator_spec.domain.services.api_parser_new import ApiParserNew

def main():
    values = {
        'asset': 'usd',
        'price': 5,
        'duration': 1,
        'direction': 2,
        'is_demo': 1
    }
    api = ApiParserNew('api_parser_conf.yml')
    class_code = api.generate_class()
    print(class_code)

if __name__ == '__main__':
    main()
