# -*- coding: utf-8 -*-

import base64
import time
from io import BytesIO
from pprint import pprint

import requests
from flask import Flask, g, make_response, render_template, request, url_for, current_app
from PIL import Image

app = Flask(__name__)
url = 'http://challenges.thecatch.cz:10001/'


@app.after_request
def add_header(response):
    # Both chrome & firefox cached the shown image
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/')
def selection():
        current_app.start = time.time()
    r = requests.get(url=url)
    image = bytearray(r.content)
    size = Image.open(BytesIO(image)).size
    with open(app.static_folder + "/smiley.png", 'wb') as f:
        f.write(image)

    n_piece_w = size[0] / 4
    n_piece_h = size[1] / 4

    phpsessid = r.cookies['PHPSESSID']
    current_app.phpsessid = phpsessid

    # Let's do the jinja magic, continue in templates/select.html
    resp = make_response(render_template(
        'select.html', map_n_w=n_piece_w, map_n_h=n_piece_h, url_for=url_for))

    # GLOBALS ARE EVIL, so carry the sessid in our cookies
    # ...how to store variable across flask's requests ? g?
    resp.set_cookie('PHPSESSID', value=phpsessid)
    return resp


@app.route('/process')
def process():
    js_data = []
    for arg in request.args:
        data = base64.b64decode(request.args.get(arg)).decode().strip("('')") # yep
        boxdata = [int(float(x)) for x in data.split(',')]
        js_data.append(boxdata)

    i = Image.open(app.static_folder+'/smiley.png', 'r')
    # i.show()

    params = {'r': 0, 'g': 0, 'b': 0}
    for n in range(3):
        # Cut my image into pieces
        piece_i = i.crop(js_data[n])
        colors = piece_i.getextrema()
        print(f"Colors of smiley {n} are {colors}")

        params['r'] = params['r'] ^ colors[0][1]
        params['g'] = params['g'] ^ colors[1][1]
        params['b'] = params['b'] ^ colors[2][1]

    cookies = {'PHPSESSID': current_app.phpsessid}

    print(f"Sending... {params} {cookies}")
    return_request = requests.post(url=url, cookies=cookies, params=params, data=params)
    print(f"Status: {return_request.status_code}\n", return_request.text)

    print("Finished in ", time.time() - current_app.start, "secs.\n")
    return return_request.text


if __name__ == '__main__':
    app.run(debug=True)
