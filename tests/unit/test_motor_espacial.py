from unittest.mock import patch
from src.config.constants import NOT_INFORMED

# Importamos com patch para evitar que MotorEspacial tente ler arquivos estáticos (GeoJSON) gigantes.
@patch('src.spatial.motor_espacial.SpatialLayer')
def test_motor_espacial_coordenadas_invalidas(mock_spatial_layer):
    """
    Testa se o Motor Espacial retorna chaves vazias ou zeros quando
    a coordenada for nitidamente espúria ou defeituosa.
    """
    from src.spatial.motor_espacial import MotorEspacial

    # O Mock garante que não iremos instanciar arquivos grandes locais
    motor = MotorEspacial()

    # Cenário: Coordenada no meio do Oceano Atlântico vazia ou nula
    resultado = motor.analisar_todas_ameacas(0.0, 0.0)

    # Verificações de Blindagem
    assert resultado['foco_em_municipio_mapeado'] == 0
    assert resultado['codigo_ibge_espacial'] == NOT_INFORMED
    assert resultado['faixa_distancia_linha'] == "SEM_DISTANCIA"
    assert resultado['distancia_hospital_km'] is None
    
@patch('src.spatial.motor_espacial.SpatialLayer')
def test_motor_espacial_coordenadas_letras(mock_spatial_layer):
    """
    Testa a injeção de texto na classe de conversão de ponto flutuante 
    da latitude e longitude
    """
    from src.spatial.motor_espacial import MotorEspacial
    motor = MotorEspacial()

    resultado = motor.analisar_todas_ameacas("ABC", "DEF")
    assert resultado['codigo_ti'] == NOT_INFORMED
    assert resultado['faixa_distancia_subestacao'] == "SEM_DISTANCIA"
