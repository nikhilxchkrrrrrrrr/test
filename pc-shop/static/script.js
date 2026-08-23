// Countdown timer (10 minutes from page load)
let timeLeft = 600;
const countdownEl = document.getElementById('countdown');

function updateCountdown() {
    if (!countdownEl) return;
    const mins = Math.floor(timeLeft / 60);
    const secs = timeLeft % 60;
    countdownEl.textContent = `⏱️ ${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    if (timeLeft > 0) {
        timeLeft--;
        setTimeout(updateCountdown, 1000);
    }
}
updateCountdown();

// Payment form handling
const form = document.getElementById('payment-form');
if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const btn = form.querySelector('.pay-btn');
        btn.disabled = true;
        btn.textContent = 'Processing...';
        
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/process-payment', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('order-id').textContent = result.order_id;
                document.getElementById('payment-result').style.display = 'block';
                form.style.display = 'none';
            }
        } catch (error) {
            alert('Payment failed. Please try again.');
            btn.disabled = false;
            btn.textContent = 'Pay $' + formData.get('amount');
        }
    });
}

// Card number formatting
const cardInput = document.querySelector('input[name="card_number"]');
if (cardInput) {
    cardInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        value = value.match(/.{1,4}/g)?.join(' ') || value;
        e.target.value = value;
    });
}

// Expiry formatting
const expiryInput = document.querySelector('input[name="expiry"]');
if (expiryInput) {
    expiryInput.addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length >= 2) {
            value = value.slice(0, 2) + '/' + value.slice(2);
        }
        e.target.value = value;
    });
}

// CVV length limit
const cvvInput = document.querySelector('input[name="cvv"]');
if (cvvInput) {
    cvvInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/\D/g, '').slice(0, 4);
    });
}

// Thumbnail click
document.querySelectorAll('.thumbnails img').forEach(img => {
    img.addEventListener('click', () => {
        const main = document.querySelector('.main-image');
        if (main) {
            main.src = img.src;
        }
    });
});