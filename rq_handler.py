from helper import cfg
from flask import request
from os import path as px


def process_req(req):
    query_parameters = params_from_req(req)
    file_bytes, filetype, filename = process_file_req(req, query_parameters)
    return file_bytes, filetype, filename


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
            filetype = file2filetype(req.files["file"])
            return file_bytes, filetype, filename

    filename = query_parameters.get('file')
    filetype = filename2filetype(filename)
    file_bytes = filepath2file(filename)

    return file_bytes, filetype, filename


def file2filetype(file):
    ct = file.content_type
    if "pdf" in ct:
        return "pdf"
    if "image" in ct:
        return "image"
    return "doc"


def filename2filetype(filename):
    if ".pdf" in filename:
        return "pdf"
    for ext in cfg["tesseract"]["img_ext"]:
        if ext in filename:
            return "image"
    return "doc"


def filepath2file(filepath):
    if px.exists(filepath):
        with open(filepath, "rb") as f:
            file_bytes = f.read()
        return file_bytes
    else:
        return None
