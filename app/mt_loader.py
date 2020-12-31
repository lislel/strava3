import yaml
import os
from app.models import Mountain

cwd = os.getcwd()
# Use for loading locally
with open(f"{cwd}/app/mountains.yml", 'r') as stream:
	mt_yaml = yaml.safe_load(stream)

# Use for loading into heroku
with open("app/mountains.yml", 'r') as stream:
	mt_yaml = yaml.safe_load(stream)

existing = Mountain.query.all()
existing_names = []

for mt in existing:
	existing_names.append(mt.name)

for key in mt_yaml.keys():
	result = mt_yaml[key]
	if result['mt_name'] not in existing_names:
		new_m = Mountain(name=result['mt_name'], lat = result['lat'], lon = result['lon'])
		db.session.add(new_m)
		db.session.commit()
