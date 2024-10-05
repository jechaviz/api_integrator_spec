from src.infrastructure.services.oas_mapper import map_oas_to_api_integrator
import argparse

def main():
    parser = argparse.ArgumentParser(description='Convert OAS to API Integrator format')
    parser.add_argument('input_file', help='Path to the input OAS file')
    parser.add_argument('output_file', help='Path to save the output API Integrator YAML file')
    args = parser.parse_args()

    map_oas_to_api_integrator(args.input_file, args.output_file)
    print(f"API Integrator configuration has been saved to {args.output_file}")

if __name__ == '__main__':
    main()
