// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });

    // Add animation to cards when they come into view
    const animateOnScroll = function() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(function(card) {
            const cardPosition = card.getBoundingClientRect();
            if (cardPosition.top < window.innerHeight && cardPosition.bottom > 0) {
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }
        });
    };

    // Initialize card animations
    const cards = document.querySelectorAll('.card');
    cards.forEach(function(card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    });

    // Run animation on page load and scroll
    animateOnScroll();
    window.addEventListener('scroll', animateOnScroll);

    // Handle tag input in forms
    const tagInput = document.getElementById('tags');
    if (tagInput) {
        tagInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const value = this.value.trim();
                if (value.endsWith(',')) {
                    this.value = value.slice(0, -1);
                } else {
                    this.value = value + ', ';
                }
            }
        });
    }

    // Preview images before upload
    const imageInput = document.getElementById('images');
    const previewContainer = document.createElement('div');
    previewContainer.className = 'row mt-2';
    
    if (imageInput) {
        imageInput.after(previewContainer);
        
        imageInput.addEventListener('change', function() {
            previewContainer.innerHTML = '';
            
            if (this.files) {
                Array.from(this.files).forEach(function(file) {
                    if (!file.type.match('image.*')) {
                        return;
                    }
                    
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const previewCol = document.createElement('div');
                        previewCol.className = 'col-md-3 mb-2';
                        
                        const previewCard = document.createElement('div');
                        previewCard.className = 'card';
                        
                        const previewImg = document.createElement('img');
                        previewImg.className = 'card-img-top';
                        previewImg.src = e.target.result;
                        previewImg.alt = 'صورة معاينة';
                        
                        previewCard.appendChild(previewImg);
                        previewCol.appendChild(previewCard);
                        previewContainer.appendChild(previewCol);
                    };
                    
                    reader.readAsDataURL(file);
                });
            }
        });
    }

    // Responsive table handling for mobile
    const tables = document.querySelectorAll('.table-responsive');
    if (window.innerWidth < 768) {
        tables.forEach(function(table) {
            table.style.maxHeight = '400px';
            table.style.overflowY = 'auto';
        });
    }
});
