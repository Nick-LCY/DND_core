from flask import Flask
from flask_cors import CORS
from .data_finder import find_data_by_type, find_data_by_id

app = Flask("dnd_core_api")
cors = CORS(app, resources={r"/data/*": {"origins": ["https://dnd5e.nicklin.work"]}})

@app.get("/data/<namespace>/<resource_type>")
def get_data_by_type(namespace, resource_type):
    return find_data_by_type(str(namespace), str(resource_type))

@app.get("/data/<data_id>")
def get_data_by_id(data_id):
    return find_data_by_id(data_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0")