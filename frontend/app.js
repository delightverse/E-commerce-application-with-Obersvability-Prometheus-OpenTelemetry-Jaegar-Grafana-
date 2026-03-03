const API_BASE = 'http://localhost:8000';
let products = [];
let cart = [];

async function loadProducts() {
    try {
        const response = await fetch(`${API_BASE}/products/`);
        products = await response.json();
        displayProducts();
    } catch (error) {
        document.getElementById('productsLoading').textContent = 'Error loading products. Is the backend running?';
        console.error('Error loading products:', error);
    }
}

function displayProducts() {
    const grid = document.getElementById('productsGrid');
    const loading = document.getElementById('productsLoading');
    loading.style.display = 'none';
    
    grid.innerHTML = products.map(product => `
        <div class="product-card">
            <h4>${product.name}</h4>
            <div class="price">$${product.price.toFixed(2)}</div>
            <div class="stock">Stock: ${product.stock}</div>
            <div>
                <input type="number" id="qty-${product.id}" value="1" min="1" max="${product.stock}">
                <button onclick="addToCart(${product.id})">Add to Cart</button>
            </div>
        </div>
    `).join('');
}

function addToCart(productId) {
    const product = products.find(p => p.id === productId);
    const quantity = parseInt(document.getElementById(`qty-${productId}`).value);
    
    if (quantity > product.stock) {
        alert('Not enough stock!');
        return;
    }
    
    const existingItem = cart.find(item => item.product_id === productId);
    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            product_id: productId,
            product: product,
            quantity: quantity
        });
    }
    
    updateCart();
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.product_id !== productId);
    updateCart();
}

function updateCart() {
    const cartItemsDiv = document.getElementById('cartItems');
    const cartTotalDiv = document.getElementById('cartTotal');
    const checkoutBtn = document.getElementById('checkoutBtn');
    
    if (cart.length === 0) {
        cartItemsDiv.innerHTML = '<p style="text-align:center;color:#999;padding:20px;">Cart is empty</p>';
        cartTotalDiv.innerHTML = '';
        checkoutBtn.disabled = true;
        return;
    }
    
    let total = 0;
    cartItemsDiv.innerHTML = cart.map(item => {
        const subtotal = item.product.price * item.quantity;
        total += subtotal;
        return `
            <div class="cart-item">
                <div>
                    <strong>${item.product.name}</strong><br>
                    <small>$${item.product.price} × ${item.quantity} = $${subtotal.toFixed(2)}</small>
                </div>
                <button onclick="removeFromCart(${item.product_id})" style="background:#f44336;color:white;border:none;padding:5px 10px;border-radius:4px;cursor:pointer;">Remove</button>
            </div>
        `;
    }).join('');
    
    cartTotalDiv.innerHTML = `Total: $${total.toFixed(2)}`;
    checkoutBtn.disabled = false;
}

async function checkout() {
    const checkoutBtn = document.getElementById('checkoutBtn');
    const successMsg = document.getElementById('successMessage');
    const errorMsg = document.getElementById('errorMessage');
    
    successMsg.style.display = 'none';
    errorMsg.style.display = 'none';
    
    checkoutBtn.disabled = true;
    checkoutBtn.textContent = 'Processing Order...';
    
    try {
        const orderData = {
            user_id: Math.floor(Math.random() * 1000) + 1,
            items: cart.map(item => ({
                product_id: item.product_id,
                quantity: item.quantity
            }))
        };
        
        const response = await fetch(`${API_BASE}/orders/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(orderData)
        });
        
        if (response.ok) {
            const order = await response.json();
            successMsg.innerHTML = `✅ Order #${order.id} placed successfully! Total: $${order.total_amount.toFixed(2)}<br><small>Check Jaeger for distributed traces!</small>`;
            successMsg.style.display = 'block';
            
            cart = [];
            updateCart();
            
            await loadProducts();
        } else {
            const error = await response.json();
            errorMsg.textContent = `❌ Order failed: ${error.detail}`;
            errorMsg.style.display = 'block';
        }
    } catch (error) {
        errorMsg.textContent = `❌ Error: ${error.message}`;
        errorMsg.style.display = 'block';
        console.error('Checkout error:', error);
    } finally {
        checkoutBtn.disabled = false;
        checkoutBtn.textContent = 'Place Order (Generates Traces!)';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('checkoutBtn').addEventListener('click', checkout);
    loadProducts();
});
