import tempfile
import os
import base64
import glob
import numpy as np
from flask import Flask, request, redirect, send_file
from skimage import io

app = Flask(__name__)

emoji_map = {
    "carita_feliz": "carita_feliz",
    "corazon": "corazon",
    "carita_neutral": "carita_neutral",
    "carita_sorprendido": "carita_sorprendido"
}

main_html = """
<html>
<head></head>
<script>
  var mousePressed = false;
  var lastX, lastY;
  var ctx;

  function getRndInteger(min, max) {
    return Math.floor(Math.random() * (max - min) ) + min;
  }

  function InitThis() {
      ctx = document.getElementById('myCanvas').getContext("2d");

      emoji = ["carita_feliz", "corazon", "carita_neutral", "carita_sorprendido"];
      emojis_visuales = {
        "carita_feliz": "🙂",
        "corazon": "❤️",
        "carita_neutral": "😐",
        "carita_sorprendido": "😮"
      };

      random = Math.floor(Math.random() * emoji.length);
      aleatorio = emoji[random];

      document.getElementById('mensaje').innerHTML = 'Dibuja: ' + emojis_visuales[aleatorio] + ' (' + aleatorio + ')';
      document.getElementById('numero').value = aleatorio;

      $('#myCanvas').mousedown(function (e) {
          mousePressed = true;
          Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, false);
      });

      $('#myCanvas').mousemove(function (e) {
          if (mousePressed) {
              Draw(e.pageX - $(this).offset().left, e.pageY - $(this).offset().top, true);
          }
      });

      $('#myCanvas').mouseup(function (e) {
          mousePressed = false;
      });

      $('#myCanvas').mouseleave(function (e) {
          mousePressed = false;
      });
  }

  function Draw(x, y, isDown) {
      if (isDown) {
          ctx.beginPath();
          ctx.strokeStyle = 'black';
          ctx.lineWidth = 11;
          ctx.lineJoin = "round";
          ctx.moveTo(lastX, lastY);
          ctx.lineTo(x, y);
          ctx.closePath();
          ctx.stroke();
      }
      lastX = x; lastY = y;
  }

  function clearArea() {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  }

  function prepareImg() {
     var canvas = document.getElementById('myCanvas');
     document.getElementById('myImage').value = canvas.toDataURL();
  }
</script>
<body onload="InitThis();">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js" type="text/javascript"></script>
    <div align="left">
      <img src="https://upload.wikimedia.org/wikipedia/commons/f/f7/Uni-logo_transparente_granate.png" width="300"/>
    </div>
    <div align="center">
        <h1 id="mensaje">Dibujando...</h1>
        <canvas id="myCanvas" width="200" height="200" style="border:2px solid black"></canvas>
        <br/><br/>
        <button onclick="javascript:clearArea();return false;">Borrar</button>
    </div>
    <div align="center">
      <form method="post" action="upload" onsubmit="javascript:prepareImg();" enctype="multipart/form-data">
        <input id="numero" name="numero" type="hidden" value="">
        <input id="myImage" name="myImage" type="hidden" value="">
        <input id="bt_upload" type="submit" value="Enviar">
      </form>
    </div>
</body>
</html>
"""

@app.route("/")
def main():
    return main_html

@app.route('/upload', methods=['POST'])
def upload():
    try:
        img_data = request.form.get('myImage').replace("data:image/png;base64,", "")
        aleatorio = request.form.get('numero')

        folder_name = emoji_map.get(aleatorio)
        if folder_name is None:
            raise ValueError(f"Etiqueta no permitida: {aleatorio}")

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Guardar con nombre único
        filename = f"{base64.urlsafe_b64encode(os.urandom(6)).decode('utf-8')}.png"
        filepath = os.path.join(folder_name, filename)

        with open(filepath, "wb") as fh:
            fh.write(base64.b64decode(img_data))
            print(f"Archivo guardado en: {filepath}")

    except Exception as err:
        print("Error al subir imagen:", err)

    return redirect("/", code=302)

@app.route('/prepare', methods=['GET'])
def prepare_dataset():
    images = []
    labels = []
    for label in emoji_map.values():
        filelist = glob.glob(f'{label}/*.png')
        if not filelist:
            continue
        images_read = io.concatenate_images(io.imread_collection(filelist))
        images_read = images_read[:, :, :, 3]  # canal alfa
        label_array = np.array([label] * images_read.shape[0])
        images.append(images_read)
        labels.append(label_array)

    if images:
        X = np.vstack(images)
        y = np.concatenate(labels)
        np.save('X.npy', X)
        np.save('y.npy', y)
        return "Dataset generado con éxito"
    else:
        return "No hay imágenes para procesar"

@app.route('/X.npy', methods=['GET'])
def download_X():
    return send_file('./X.npy')

@app.route('/y.npy', methods=['GET'])
def download_y():
    return send_file('./y.npy')

if __name__ == "__main__":
    for folder in emoji_map.values():
        os.makedirs(folder, exist_ok=True)
    app.run()
