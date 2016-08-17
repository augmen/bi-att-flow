import shutil
from collections import OrderedDict
import http.server
import socketserver
import argparse
import json
import os
import numpy as np

from jinja2 import Environment, FileSystemLoader


def bool_(string):
    if string == 'True':
        return True
    elif string == 'False':
        return False
    else:
        raise Exception()

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default='basic')
    parser.add_argument("--data_type", type=str, default='dev')
    parser.add_argument("--step", type=int, default=5000)
    parser.add_argument("--template_name", type=str, default="visualizer.html")
    parser.add_argument("--num_per_page", type=int, default=100)
    parser.add_argument("--data_dir", type=str, default="data/squad")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--open", type=str, default='False')
    parser.add_argument("--run_id", type=str, default="0")

    args = parser.parse_args()
    return args


def _decode(decoder, sent):
    return " ".join(decoder[idx] for idx in sent)


def accuracy2_visualizer(args):
    model_name = args.model_name
    data_type = args.data_type
    num_per_page = args.num_per_page
    data_dir = args.data_dir
    run_id = args.run_id.zfill(2)
    step = args.step

    eval_path =os.path.join("out", model_name, run_id, "eval", "{}-{}.json".format(data_type, str(step).zfill(6)))
    eval_ = json.load(open(eval_path, 'r'))

    _id = 0
    html_dir = "/tmp/list_results%d" % _id
    while os.path.exists(html_dir):
        _id += 1
        html_dir = "/tmp/list_results%d" % _id

    if os.path.exists(html_dir):
        shutil.rmtree(html_dir)
    os.mkdir(html_dir)

    cur_dir = os.path.dirname(os.path.realpath(__file__))
    templates_dir = os.path.join(cur_dir, 'templates')
    env = Environment(loader=FileSystemLoader(templates_dir))
    env.globals.update(zip=zip, reversed=reversed)
    template = env.get_template(args.template_name)

    data_path = os.path.join(data_dir, "data_{}.json".format(data_type))
    shared_path = os.path.join(data_dir, "shared_{}.json".format(data_type))
    data = json.load(open(data_path, 'r'))
    shared = json.load(open(shared_path, 'r'))
    cv = shared['cv']
    idx2char_dict = {idx: char for char, idx in cv.items()}

    rows = []
    for i, (idx, yi, y2i, ypi, yp2i) in enumerate(zip(*[eval_[key] for key in ('idxs', 'y', 'y2', 'yp', 'yp2')])):
        id_, cq, rcx, a = (data[key][idx] for key in ('ids', 'cq', '*cx', 'a'))
        cx = shared['cx'][rcx[0]][rcx[1]]
        ques = ["".join(idx2char_dict[idx] for idx in word) for word in cq]
        para = [["".join(idx2char_dict[idx] for idx in word) for word in sent] for sent in cx]
        row = {
            'id': id_,
            'title': "Hello world!",
            'ques': ques,
            'para': para,
            'y': yi,
            'y2': y2i,
            'yp': ypi,
            'yp2': yp2i,
            'a': a
               }
        rows.append(row)

        if i % num_per_page == 0:
            html_path = os.path.join(html_dir, "%s.html" % str(i).zfill(8))

        if (i + 1) % num_per_page == 0 or (i + 1) == len(eval_['y']):
            var_dict = {'title': "Accuracy Visualization",
                        'rows': rows
                        }
            with open(html_path, "wb") as f:
                f.write(template.render(**var_dict).encode('UTF-8'))
            rows = []

    os.chdir(html_dir)
    port = args.port
    host = args.host
    # Overriding to suppress log message
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
    handler = MyHandler
    httpd = socketserver.TCPServer((host, port), handler)
    if args.open == 'True':
        os.system("open http://%s:%d" % (args.host, args.port))
    print("serving at %s:%d" % (host, port))
    httpd.serve_forever()


if __name__ == "__main__":
    ARGS = get_args()
    accuracy2_visualizer(ARGS)