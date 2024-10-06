from src.infrastructure.services.oas_mapper import OasToApiIntegratorMapper
from pathlib import Path
import yaml

def main():
    # Define the input file path (relative to oas_specs directory)
    input_file = 'ingram/api1.json'
    
    # Create the mapper and generate the configuration
    mapper = OasToApiIntegratorMapper(input_file)
    config = mapper.map_to_api_integrator_config()

    # Generate the output file name
    output_file = Path(__file__).parent / 'infrastructure/config' / (Path(input_file).stem + '_ai.yaml')

    # Ensure the output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save the configuration to the output file
    with open(output_file, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)

    print(f"API Integrator configuration has been saved to {output_file}")

if __name__ == '__main__':
    main()
