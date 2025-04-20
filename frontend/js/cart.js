// cart.js
class CartItem {
    constructor(pid, name, price, quantity = 1) {
        this.pid = pid;
        this.name = name;
        this.price = price;
        this.quantity = quantity;
    }
}

class ShoppingCart {
    constructor() {
        this.items = new Map();
        this.load();
    }

    load() {
        const saved = localStorage.getItem('cart');
        if (saved) {
            JSON.parse(saved).forEach(item => {
                this.items.set(item.pid, new CartItem(
                    item.pid,
                    item.name,
                    item.price,
                    item.quantity
                ));
            });
        }
    }

    save() {
        localStorage.setItem('cart', JSON.stringify([...this.items.values()]));
    }

    // 添加商品
    async addProduct(pid) {
        if (this.items.has(pid)) {
            this.items.get(pid).quantity++
        } else {
            const product = await this.fetchProductDetails(pid)
            this.items.set(pid, new CartItem(
                pid,
                product.name,
                product.price
            ))
        }
        this.save()
    }

    // 获取商品详情
    async fetchProductDetails(pid) {
        const response = await fetch(`/api/products/${pid}`)
        if (!response.ok) throw new Error('Product not found')
        return response.json()
    }

    // 更新数量
    updateQuantity(pid, newQuantity) {
        if (newQuantity < 1) return this.removeProduct(pid)

        const item = this.items.get(pid)
        if (item) {
            item.quantity = newQuantity
            this.save()
        }
    }

    // 移除商品
    removeProduct(pid) {
        this.items.delete(pid)
        this.save()
    }

    // 计算总价
    calculateTotal() {
        return [...this.items.values()].reduce(
            (total, item) => total + (item.price * item.quantity), 0
        )
    }
}

// 导出单例实例
export const cart = new ShoppingCart();

// 通用渲染方法
export function updateCartDisplay() {
    const cartList = document.querySelector(".shopping-cart ul");
    const totalElement = document.querySelector(".shopping-cart h2");

    if (!cartList || !totalElement) return;

    cartList.innerHTML = "";
    let itemNumber = 1;

    cart.items.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `
            <span class="name">${item.name}</span>
            <span class="price">@$${item.price.toFixed(2)}</span>
            <input type="hidden" name="item_name_${itemNumber}" value="${item.name}">
            <input type="hidden" name="amount_${itemNumber}" value="${item.price.toFixed(2)}">
            <input type="hidden" name="quantity_${itemNumber}" value="${item.quantity}">
        `;
        li.append(createQuantityControls(item.pid, item.quantity));
        cartList.appendChild(li);
        itemNumber++;
    });

    const total = cart.calculateTotal();
    totalElement.textContent = `Shopping Cart ($${total.toFixed(2)})`;
}

function createQuantityControls(pid, quantity) {
    const container = document.createElement("div")
    container.className = "quantity-controls"

    // 减量按钮
    const decrement = document.createElement("button")
    decrement.textContent = "-"
    decrement.addEventListener("click", () => {
        cart.updateQuantity(pid, quantity - 1)
        updateCartDisplay()
    })

    // 数量输入
    const input = document.createElement("input")
    input.type = "number"
    input.value = quantity
    input.min = 1
    input.addEventListener("change", (e) => {
        cart.updateQuantity(pid, parseInt(e.target.value))
        updateCartDisplay()
    })

    // 增量按钮
    const increment = document.createElement("button")
    increment.textContent = "+"
    increment.addEventListener("click", () => {
        cart.updateQuantity(pid, quantity + 1)
        updateCartDisplay()
    })

    // 删除按钮
    const remove = document.createElement("button")
    remove.textContent = "×"
    remove.className = "remove"
    remove.addEventListener("click", () => {
        cart.removeProduct(pid)
        updateCartDisplay()
    })

    container.append(decrement, input, increment, remove)
    return container
}
