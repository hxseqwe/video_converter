class VideoConverter {
    constructor() {
        this.form = document.getElementById('conversionForm');
        this.progressSection = document.getElementById('progressSection');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        this.downloadSection = document.getElementById('downloadSection');
        this.downloadLink = document.getElementById('downloadLink');
        this.errorSection = document.getElementById('errorSection');
        this.errorText = document.getElementById('errorText');
        this.convertBtn = document.getElementById('convertBtn');
        
        this.initEventListeners();
    }
    
    initEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(this.form);
        const fileInput = document.getElementById('file');
        
        if (!fileInput.files[0]) {
            this.showError('Пожалуйста, выберите файл');
            return;
        }
        
        this.showProgress();
        this.hideError();
        this.convertBtn.disabled = true;
        this.convertBtn.textContent = 'Конвертация...';
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Ошибка при загрузке файла');
            }
            
            const data = await response.json();
            this.monitorProgress(data.task_id);
            
        } catch (error) {
            this.showError(error.message);
            this.hideProgress();
            this.convertBtn.disabled = false;
            this.convertBtn.textContent = 'Конвертировать';
        }
    }
    
    async monitorProgress(taskId) {
        const checkProgress = async () => {
            try {
                const response = await fetch(`/task/${taskId}`);
                const data = await response.json();
                
                this.updateProgress(data);
                
                if (data.status === 'PROGRESS' || data.status === 'PENDING') {
                    setTimeout(checkProgress, 1000);
                } else if (data.status === 'SUCCESS') {
                    this.showDownloadLink(data.download_url);
                } else if (data.status === 'FAILURE') {
                    this.showError(data.error_message || 'Ошибка при конвертации');
                }
                
            } catch (error) {
                this.showError('Ошибка при проверке статуса');
            }
        };
        
        checkProgress();
    }
    
    updateProgress(data) {
        const progress = data.progress || 0;
        this.progressFill.style.width = `${progress}%`;
        this.progressText.textContent = `Конвертация: ${progress}%`;
    }
    
    showProgress() {
        this.progressSection.classList.remove('hidden');
        this.progressFill.style.width = '0%';
        this.progressText.textContent = 'Подготовка...';
        this.downloadSection.classList.add('hidden');
    }
    
    hideProgress() {
        this.progressSection.classList.add('hidden');
    }
    
    showDownloadLink(downloadUrl) {
        this.progressText.textContent = 'Конвертация завершена!';
        this.downloadLink.href = downloadUrl;
        this.downloadLink.textContent = 'Скачать конвертированный файл';
        this.downloadSection.classList.remove('hidden');
        this.convertBtn.disabled = false;
        this.convertBtn.textContent = 'Конвертировать другой файл';
    }
    
    showError(message) {
        this.errorText.textContent = message;
        this.errorSection.classList.remove('hidden');
    }
    
    hideError() {
        this.errorSection.classList.add('hidden');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new VideoConverter();
});