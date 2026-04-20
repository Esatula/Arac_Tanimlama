document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    const uploadBox = document.getElementById('uploadBox');
    const resultsContainer = document.getElementById('resultsContainer');
    const previewImage = document.getElementById('previewImage');
    const boundingBoxes = document.querySelectorAll('.bounding-box');
    const trFormatToggle = document.getElementById('trFormatToggle');

    // Settings panel collapse
    document.getElementById('settingsToggleHeader').addEventListener('click', () => {
        const body = document.getElementById('settingsBody');
        const arrow = document.getElementById('settingsArrow');
        const isOpen = body.style.display !== 'none';
        body.style.display = isOpen ? 'none' : 'flex';
        arrow.classList.toggle('open', !isOpen);
    });

    // Drag & Drop behaviors
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.classList.add('dragover');
    });

    uploadBox.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.classList.remove('dragover');
        
        if(e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Submitting via File Input
    fileInput.addEventListener('change', function() {
        if(this.files && this.files[0]) {
            handleFile(this.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.type.match('image.*')) {
            alert('Lütfen sadece resim dosyası yükleyin.');
            return;
        }

        const reader = new FileReader();
        
        reader.onload = function(e) {
            previewImage.src = e.target.result;
            
            // Hide upload, simulate analysis
            uploadBox.style.display = 'none';
            resultsContainer.style.display = 'none';
            
            // Simulate processing time
            let loader = document.createElement('div');
            loader.innerHTML = '<div style="text-align:center; padding: 40px;"><i class="fa-solid fa-spinner fa-spin fa-3x" style="color:#00d2ff;"></i><p style="margin-top:20px; color:#94a3b8;">Yapay Zeka Analiz Ediyor...</p></div>';
            loader.id = "tempLoader";
            uploadBox.parentNode.insertBefore(loader, uploadBox.nextSibling);

            // Ayar parametresini ekle
            const formData = new FormData();
            formData.append('file', file);
            formData.append('tr_format', trFormatToggle.checked ? '1' : '0');
            
            fetch('http://127.0.0.1:5000/analyze', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('tempLoader').remove();
                
                if(data.error) {
                    alert("Hata: " + data.error);
                    uploadBox.style.display = 'block';
                    return;
                }
                
                // Show actual results
                resultsContainer.style.display = 'block';
                
                // Set the real annotated image from backend
                previewImage.src = data.image;
                
                // Hide mock bounding boxes completely since backend draws them
                boundingBoxes.forEach(box => {
                    box.style.display = 'none';
                });
                
                // Update plate list
                const plateList = document.getElementById('plateList');
                plateList.innerHTML = '';
                
                const texts = data.texts.split('|');
                texts.forEach(txt => {
                    const li = document.createElement('li');
                    li.className = 'plate-item';
                    if (txt.trim() === "Plaka tespit edilemedi.") {
                        li.innerHTML = `<div class="plate-text" style="color: #ff4757;">Bulunamadı</div>`;
                    } else if (txt.trim() === "Okunamadi") {
                         li.innerHTML = `<div class="plate-text" style="color: #f59e0b;">Plaka Görseli Zayıf</div>`;
                    } else {
                        li.innerHTML = `<div class="plate-text">${txt.trim()}</div><div class="plate-conf">Gerçek Analiz Sonucu</div>`;
                    }
                    plateList.appendChild(li);
                });
                
                document.getElementById('vehicleCount').innerText = data.vehicle_count !== undefined ? data.vehicle_count : "0";
            })
            .catch(error => {
                console.error('Error:', error);
                document.getElementById('tempLoader').remove();
                uploadBox.style.display = 'block';
                alert("Analiz sırasında bir hata oluştu.");
            });
        }
        
        reader.readAsDataURL(file);
    }
});
