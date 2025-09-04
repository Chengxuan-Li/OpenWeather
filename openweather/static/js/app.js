// Additional JavaScript functionality for OpenWeather

// Utility functions
const OpenWeather = {
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },

    // Validate email
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Validate WKT
    validateWKT: function(wkt) {
        if (!wkt || typeof wkt !== 'string') return false;
        
        // Basic WKT validation
        const wktPatterns = [
            /^POINT\s*\(\s*-?\d+\.?\d*\s+-?\d+\.?\d*\s*\)$/i,
            /^POLYGON\s*\(\s*\(\s*(?:-?\d+\.?\d*\s+-?\d+\.?\d*\s*,?\s*)+\)\s*\)$/i,
            /^MULTIPOLYGON\s*\(\s*(?:\(\s*\(\s*(?:-?\d+\.?\d*\s+-?\d+\.?\d*\s*,?\s*)+\)\s*\)\s*,?\s*)+\)$/i
        ];
        
        return wktPatterns.some(pattern => pattern.test(wkt.trim()));
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 notification-${type}`;
        
        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-black',
            info: 'bg-blue-500 text-white'
        };
        
        notification.className += ` ${colors[type]}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    },

    // Copy to clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showNotification('Copied to clipboard!', 'success');
        }).catch(() => {
            this.showNotification('Failed to copy to clipboard', 'error');
        });
    },

    // Download file
    downloadFile: function(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form[hx-post="/run"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            const wkt = document.getElementById('wkt').value;
            const apiKey = document.getElementById('api_key').value;
            const email = document.getElementById('email').value;
            
            let errors = [];
            
            // Validate WKT
            if (!OpenWeather.validateWKT(wkt)) {
                errors.push('Invalid WKT geometry format');
            }
            
            // Validate API key
            if (!apiKey || apiKey.trim().length === 0) {
                errors.push('API key is required');
            }
            
            // Validate email
            if (!OpenWeather.validateEmail(email)) {
                errors.push('Invalid email format');
            }
            
            if (errors.length > 0) {
                e.preventDefault();
                errors.forEach(error => {
                    OpenWeather.showNotification(error, 'error');
                });
            }
        });
    }
});

// Copy buttons
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('copy-btn')) {
        const text = e.target.getAttribute('data-copy');
        if (text) {
            OpenWeather.copyToClipboard(text);
        }
    }
});

// File download tracking
document.addEventListener('click', function(e) {
    if (e.target.tagName === 'A' && e.target.href.includes('/api/download-file/')) {
        const filename = e.target.textContent.trim();
        console.log(`Downloading file: ${filename}`);
        
        // You could add analytics tracking here
        // analytics.track('file_download', { filename: filename });
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Enter to submit form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const form = document.querySelector('form[hx-post="/run"]');
        if (form && document.activeElement.closest('form') === form) {
            form.submit();
        }
    }
    
    // Escape to clear map
    if (e.key === 'Escape') {
        const clearBtn = document.getElementById('clear-map');
        if (clearBtn) {
            clearBtn.click();
        }
    }
});

// HTMX event handlers
document.body.addEventListener('htmx:beforeRequest', function() {
    // Show loading state
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="animate-spin mr-2">⏳</span>Processing...';
    }
});

document.body.addEventListener('htmx:afterRequest', function() {
    // Reset loading state
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Download Weather Data';
    }
});

document.body.addEventListener('htmx:responseError', function() {
    OpenWeather.showNotification('Request failed. Please try again.', 'error');
});

// Export for use in other scripts
window.OpenWeather = OpenWeather;
