import yaml
import os

filepath = '/home/gabriel/Documentos/UNIFEI/IC - DataOps/docker-compose.yaml'
with open(filepath, 'r') as f:
    data = yaml.safe_load(f)

# Reduce Broker resources
data['services']['broker']['deploy']['resources']['limits']['cpus'] = '1.0'
data['services']['broker']['deploy']['resources']['limits']['memory'] = '1024M'
data['services']['broker']['environment']['JAVA_OPTS'] = '-Xms256m -Xmx512m -XX:MaxDirectMemorySize=512m -Duser.timezone=America/Sao_Paulo'

# Reduce Historical resources
data['services']['historical']['deploy']['resources']['limits']['cpus'] = '1.0'
data['services']['historical']['deploy']['resources']['limits']['memory'] = '1024M'
data['services']['historical']['environment']['JAVA_OPTS'] = '-Xms256m -Xmx512m -XX:MaxDirectMemorySize=512m -Duser.timezone=America/Sao_Paulo'

# Reduce Superset resources
data['services']['superset']['deploy']['resources']['limits']['cpus'] = '1.0'
data['services']['superset']['deploy']['resources']['limits']['memory'] = '1024M'

# Add Dagster Volume
if 'dagster_data' not in data.get('volumes', {}):
    if not 'volumes' in data: data['volumes'] = {}
    data['volumes']['dagster_data'] = {}

# Add Dagster Service
if 'dagster' not in data['services']:
    data['services']['dagster'] = {
        'image': 'dagster/dagster:latest',
        'container_name': 'dagster',
        'ports': ['3000:3000'],
        'volumes': [
            './src:/opt/dagster/app/src',
            'dagster_data:/opt/dagster/dagster_home',
            './data:/opt/dagster/app/data'
        ],
        'environment': {
            'DAGSTER_HOME': '/opt/dagster/dagster_home',
            'TZ': 'America/Sao_Paulo',
            'PYTHONPATH': '/opt/dagster/app'
        },
        'working_dir': '/opt/dagster/app',
        'command': ['dagster', 'dev', '-h', '0.0.0.0', '-p', '3000', '-m', 'src.orchestration.repo'],
        'networks': ['druid-net'],
        'deploy': {
            'resources': {
                'limits': {
                    'cpus': '0.75',
                    'memory': '512M'
                }
            }
        }
    }

with open(filepath, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print("Docker compose modified.")
