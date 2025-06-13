import os
import io
from PIL import Image
from flask import Flask, render_template_string, request, send_file, jsonify

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>S&S Enterprises - AI Image Processing</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            padding-top: 130px; /* navbar (60px) + title bar (10vh) spacing */
        }
        .page-title-bar {
            height: 5vh;
            background-color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            border-bottom: 1px solid #ccc;
            
        }
        .image-preview {
            max-width: 100%;
            margin-top: 1rem;
        }
        .section-divider {
            border-left: 1px solid #ccc;
        }
        .announcement {
            background-color: #ffc107;
            color: #000;
            text-align: center;
            padding: 0.5rem;
            font-weight: 500;
        }
    </style>
</head>
<body>

<!-- Fixed Navbar -->
<nav class="navbar navbar-expand-lg navbar-dark bg-dark fixed-top">
    <div class="container-fluid">
        <a class="navbar-brand" href="#">S&amp;S Enterprises</a>
    </div>
</nav>

<!-- Announcement Banner -->
<div class="announcement fixed-top mt-5">
    🚀 New Feature Launched: AI Background Removal is now faster and more accurate!
</div>

<!-- Page Title Bar -->
<div class="page-title-bar">
    <h1 class="h4 mb-0">AI Image Processing Tool</h1>
</div>

<!-- Main Content -->
<div class="container-fluid">
    <div class="row">
        <!-- Left Panel -->
        <div class="col-md-6">
            <h2 class="mb-4">Choose Your Operation</h2>
            <form id="imageForm" action="/process" method="post" enctype="multipart/form-data" class="needs-validation" novalidate>
                <div class="mb-3">
                    <label for="imageInput" class="form-label">Upload an image:</label>
                    <input type="file" class="form-control" name="image" id="imageInput" required>
                </div>

                <div class="mb-3">
                    <label class="form-label">Choose operation:</label>
                    <select class="form-select" name="operation">
                        <option value="resize">Resize by Dimensions</option>
                        <option value="aspect">Resize by Aspect Ratio</option>
                        <option value="compress">Compress to Target File Size</option>
                        <option value="resolution">Change DPI</option>
                        <option value="grayscale">Convert to Grayscale</option>
                        <option value="crop">Crop Image</option>
                        <option value="removebg">Remove Background (AI)</option>
                    </select>
                </div>

                <div class="mb-3">
                    <label>Width:</label>
                    <input type="number" class="form-control" name="width">
                    <label>Height:</label>
                    <input type="number" class="form-control" name="height">
                </div>

                <div class="mb-3">
                    <label>Target File Size (KB):</label>
                    <input type="number" class="form-control" name="filesize">
                </div>

                <div class="mb-3">
                    <label>DPI (e.g. 72,150):</label>
                    <input type="text" class="form-control" name="dpi">
                </div>

                <div class="mb-3">
                    <label>Crop (x, y, width, height):</label>
                    <input type="text" class="form-control" name="crop" placeholder="e.g. 10,10,200,200">
                </div>

                <button type="submit" class="btn btn-primary mt-3">Submit</button>
            </form>
        </div>

        <!-- Right Panel -->
        <div class="col-md-6 section-divider ps-4">
            <h3>Image Preview & Properties</h3>
            <div id="imageInfo" class="mt-3 mb-2"></div>
            <img id="preview" class="image-preview border rounded" />
        </div>
    </div>
</div>

<script>
    const imageInput = document.getElementById('imageInput');
    const preview = document.getElementById('preview');
    const info = document.getElementById('imageInfo');

    imageInput.addEventListener('change', () => {
        const file = imageInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);

        const reader = new FileReader();
        reader.onload = e => preview.src = e.target.result;
        reader.readAsDataURL(file);

        fetch('/preview', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                info.innerHTML = `
                    <p><strong>Filename:</strong> ${data.filename}</p>
                    <p><strong>Dimensions:</strong> ${data.width} × ${data.height} px</p>
                    <p><strong>Format:</strong> ${data.format}</p>
                    <p><strong>Mode:</strong> ${data.mode}</p>
                    <p><strong>DPI:</strong> ${data.dpi} dpi</p>
                    <p><strong>File size:</strong> ${data.size_kb} KB</p>
                `;
            });
    });
</script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/preview', methods=['POST'])
def preview():
    file = request.files['image']
    image = Image.open(file.stream)
    dpi = image.info.get('dpi', (72, 72))
    if isinstance(dpi, tuple):
        if len(dpi) == 2:
            dpi_str = f"{dpi[0]} × {dpi[1]}"
        elif len(dpi) == 1:
            dpi_str = f"{dpi[0]}"
        else:
            dpi_str = "N/A"
    else:
        dpi_str = "N/A"
    file.seek(0, os.SEEK_END)
    size_kb = round(file.tell() / 1024, 2)

    return jsonify({
        'filename': file.filename,
        'width': image.width,
        'height': image.height,
        'format': image.format,
        'mode': image.mode,
        'dpi': dpi_str,
        'size_kb': size_kb
    })

@app.route('/process', methods=['POST'])
def process():
    file = request.files['image']
    operation = request.form['operation']
    image = Image.open(file.stream)

    output = io.BytesIO()
    filename = f"processed_{operation}.png"

    if operation == 'resize':
        width = int(request.form.get('width', 0))
        height = int(request.form.get('height', 0))
        if width > 0 and height > 0:
            image = image.resize((width, height), Image.LANCZOS)
            image.save(output, format='PNG')

    elif operation == 'aspect':
        new_width = int(request.form.get('width', 0))
        if new_width > 0:
            w_percent = (new_width / float(image.size[0]))
            new_height = int((float(image.size[1]) * float(w_percent)))
            image = image.resize((new_width, new_height), Image.LANCZOS)
            image.save(output, format='PNG')

    elif operation == 'compress':
        target_kb = int(request.form.get('filesize', 0))
        quality = 95
        while quality > 10:
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=quality)
            if buffer.tell() / 1024 <= target_kb:
                output = buffer
                break
            quality -= 5

    elif operation == 'resolution':
        dpi_text = request.form.get('dpi', '72')
        dpi = tuple(map(int, dpi_text.split(',')))
        image.save(output, format='PNG', dpi=dpi)

    elif operation == 'grayscale':
        image = image.convert('L')
        image.save(output, format='PNG')

    elif operation == 'crop':
        crop_vals = request.form.get('crop', '')
        try:
            x, y, w, h = map(int, crop_vals.split(','))
            image = image.crop((x, y, x + w, y + h))
            image.save(output, format='PNG')
        except:
            return 'Invalid crop values', 400

    elif operation == 'removebg':
        if not REMBG_AVAILABLE:
            return 'Background removal requires the rembg module. Please install with: pip install rembg', 500
        image = image.convert("RGBA")
        image_data = io.BytesIO()
        image.save(image_data, format='PNG')
        image_data.seek(0)
        result = remove(image_data.read())
        output.write(result)

    output.seek(0)
    return send_file(output, as_attachment=True, download_name=filename, mimetype='image/png')

if __name__ == '__main__':

    app.run(debug=True)