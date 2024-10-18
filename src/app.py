from flask import Flask
from data_finder import find_data_by_type, find_data_by_id

app = Flask("dnd_core_api")

@app.get("/data/<namespace>/<resource_type>")
def get_data_by_type(namespace, resource_type):
    return find_data_by_type(str(namespace), str(resource_type))

@app.get("/data/<data_id>")
def get_data_by_id(data_id):
    return find_data_by_id(data_id)
