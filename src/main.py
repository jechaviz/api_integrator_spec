from src.infrastructure.services.oas_mapper import OasToApiIntegratorMapper
from pathlib import Path
import yaml

def main():
    # Definir las rutas de los archivos
    input_file = Path(__file__).parent.parent / 'infrastructure/config/openapi_spec.yaml'
    
    # Generar el nombre del archivo de salida
    output_file = input_file.with_name(input_file.stem + '_ai.yaml')

    # Asegurarse de que el directorio de salida exista
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Crear el mapper y generar la configuración
    mapper = OasToApiIntegratorMapper(str(input_file))
    config = mapper.map_to_api_integrator_config()

    # Guardar la configuración en el archivo de salida
    with open(output_file, 'w') as f:
        yaml.dump(config.to_dict(), f, default_flow_style=False)

    print(f"API Integrator configuration has been saved to {output_file}")

if __name__ == '__main__':
    main()
