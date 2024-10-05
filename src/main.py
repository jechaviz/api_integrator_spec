from src.infrastructure.services.oas_mapper import map_oas_to_api_integrator
from pathlib import Path

def main():
    # Definir las rutas de los archivos
    input_file = Path(__file__).parent.parent / 'infrastructure/config/openapi_spec.yaml'
    
    # Generar el nombre del archivo de salida
    output_file = input_file.with_name(input_file.stem + '_ai.yaml')

    # Asegurarse de que el directorio de salida exista
    output_file.parent.mkdir(parents=True, exist_ok=True)

    map_oas_to_api_integrator(str(input_file), str(output_file))
    print(f"API Integrator configuration has been saved to {output_file}")

if __name__ == '__main__':
    main()
