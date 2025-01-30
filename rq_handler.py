from os import path as px


def process_req(req):
    query_parameters = params_from_req(req)
    file_bytes, filename = process_file_req(req, query_parameters)
    return file_bytes, filename


def process_req_test(req, fields=["text"]):
    query_parameters = params_from_req(req)
    return [query_parameters[x] for x in fields]


def params_from_req(req):
    query_parameters = req.args
    if len(query_parameters) == 0:
        query_parameters = req.form
    return query_parameters


def process_file_req(req, query_parameters):
    if "file" in req.files:
        file_bytes = req.files["file"].read()
        filename = req.files["file"].filename
        if filename != "":
            return file_bytes, filename
        
    filename = query_parameters.get('file')
    file_bytes = filepath2file(filename)

    return file_bytes, filename


def filepath2file(filepath):
    if px.exists(filepath):
        with open(filepath, "rb") as f:
            file_bytes = f.read()
        return file_bytes
    else:
        return None
