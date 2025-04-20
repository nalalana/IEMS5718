import os
import secrets
import uuid
from shutil import copyfileobj

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Response, Cookie
from fastapi import Form
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

from database import Category, Product, UserCreate, User, get_password_hash, UserLogin, verify_password
from database import SessionLocal


from fastapi.responses import FileResponse
from fastapi import Request, Depends
from fastapi.responses import RedirectResponse

app = FastAPI()


app.mount("/static", StaticFiles(directory="frontend"), name="static")

csrf_tokens = {}

def generate_csrf_token(session_token: str):
    token = secrets.token_urlsafe(32)
    csrf_tokens[session_token] = token
    return token

def validate_csrf_token(session_token: str, submitted_token: str):
    return csrf_tokens.get(session_token) == submitted_token

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 获取当前用户信息（用于后续 admin 权限控制）
def get_current_user(session_token: str = Cookie(None)):
    if session_token and session_token in session_store:
        return session_store[session_token]
    return None

@app.get("/", response_class=HTMLResponse)
def root(request: Request, user=Depends(get_current_user)):
    username = user["email"] if user else "guest"
    is_admin = user["is_admin"] if user else False
    admin_links = """<a href="/admin/products">管理商品</a><a href="/admin/categories">管理目录</a>""" if is_admin else ""
    file_path = os.path.join(os.getcwd(), 'frontend', 'index.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace("{{ username }}", username)
    content = content.replace("{{ admin_links }}", admin_links)

    return content

@app.get("/admin/categories", response_class=HTMLResponse)
def category_form(request: Request, user=Depends(get_current_user)):
    """
    管理员访问页面，用于管理目录，例如添加新目录
    :return:
    """
    token_key = user["email"] if user else "guest"
    csrf_token = generate_csrf_token(token_key)
    if not user or not user.get("is_admin"):
        return RedirectResponse(url="/login")
    file_path = os.path.join(os.getcwd(), 'frontend', 'category_form.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace("{{ csrf_token }}", csrf_token)
    return content


@app.get("/admin/products", response_class=HTMLResponse)
def product_form(request: Request, user=Depends(get_current_user)):
    """
    管理员访问页面，管理每个目录中的商品
    :return:
    """
    token_key = user["email"] if user else "guest"
    csrf_token = generate_csrf_token(token_key)
    if not user or not user.get("is_admin"):
        return RedirectResponse(url="/login")

    file_path = os.path.join(os.getcwd(), 'frontend', 'product_form.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace("{{ csrf_token }}", csrf_token)
    return content


@app.get("/products/{pid}", response_class=HTMLResponse)
def get_product_details(pid: int, db: Session = Depends(get_db)):
    """
    前端，商品详情页面
    :param pid:
    :param db:
    :return:
    """
    product = db.query(Product).filter(Product.pid == pid).first()
    current_category = db.query(Category).filter(Category.catid == product.catid).first()
    if product:
        # product =  {
        #     "name": product.name,
        #     "catid": product.catid
        #     "price": product.price,
        #     "description": product.description,
        #     "image": product.image
        # }
        file_path = os.path.join(os.getcwd(), 'frontend', 'product.html')
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        content = content.replace("{{ current.category }}", current_category.name)
        content = content.replace("{{ product.name }}", product.name)
        content = content.replace("{{ product.price }}", str(product.price))
        content = content.replace("{{ product.description }}", product.description)
        content = content.replace("{{ product.image }}", product.image)
        return content
    return {"error": "Product not found"}

@app.get("/register", response_class=HTMLResponse)
def serve_register(user=Depends(get_current_user)):
    token_key = user["email"] if user else "guest"
    csrf_token = generate_csrf_token(token_key)
    file_path = os.path.join(os.getcwd(), 'frontend', 'register.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace("{{ csrf_token }}", csrf_token)
    return content

@app.get("/login", response_class=HTMLResponse)
def serve_login(user=Depends(get_current_user)):
    token_key = user["email"] if user else "guest"
    csrf_token = generate_csrf_token(token_key)
    file_path = os.path.join(os.getcwd(), 'frontend', 'login.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    content = content.replace("{{ csrf_token }}", csrf_token)
    return content


@app.get("/change-password", response_class=HTMLResponse)
def serve_change_password(user=Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/login")

    token_key = user["email"]
    csrf_token = generate_csrf_token(token_key)

    file_path = os.path.join(os.getcwd(), 'frontend', 'change_password.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    content = content.replace("{{ csrf_token }}", csrf_token)
    return content



@app.post("/api/categories/")
def create_category(name: str = Form(...), csrf_token: str = Form(...),
    session_token: str = Cookie(None),db: Session = Depends(get_db)):
    """
    后端接口，创建目录
    :param name:
    :param db:
    :return:
    """

    user_info = session_store.get(session_token)
    token_key = user_info["email"] if user_info else "guest"
    if not validate_csrf_token(token_key or "guest", csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    db_category = Category(name=name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/api/categories/")
def get_categories(db: Session = Depends(get_db)):
    """
    后端接口，查看目录
    :param db:
    :return:
    """
    return db.query(Category).all()


@app.post("/api/products/")
async def create_product(
        catid: int = Form(...),
        name: str = Form(...),
        price: float = Form(...),
        description: str = Form(...),
        image: UploadFile = File(...),
        csrf_token: str = Form(...),
        session_token: str = Cookie(None),
        db: Session = Depends(get_db)
):
    """
    创建新产品
    :param catid:
    :param name:
    :param price:
    :param description:
    :param image:
    :param db:
    :return:
    """
    # 创建存储上传图片的目录，如果目录不存在
    user_info = session_store.get(session_token)
    token_key = user_info["email"] if user_info else "guest"
    if not validate_csrf_token(token_key or "guest", csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


    images_dir = os.path.join("frontend", "images")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Store the uploaded file with a unique name
    file_ext = os.path.splitext(image.filename)[1]
    unique_filename = str(uuid.uuid4()) + file_ext
    file_path = os.path.join("frontend", "images", unique_filename)

    with open(file_path, "wb") as buffer:
        copyfileobj(image.file, buffer)

    # Create the product record in the database
    db_product = Product(catid=catid, name=name, price=price, description=description, image=unique_filename)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.post("/api/products/{pid}")
async def update_product(
        pid: int,
        name: str = Form(...),
        price: float = Form(...),
        description: str = Form(...),
        image: UploadFile = File(None),  # Make image optional for update
        csrf_token: str = Form(...),
        session_token: str = Cookie(None),
        db: Session = Depends(get_db)
):
    user_info = session_store.get(session_token)
    token_key = user_info["email"] if user_info else "guest"
    if not validate_csrf_token(token_key or "guest", csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


    db_product = db.query(Product).filter(Product.pid == pid).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update product fields
    db_product.name = name
    db_product.price = price
    db_product.description = description

    # If a new image is provided, update the image
    # 处理上传图片（只有在提供新图片时才更新）
    if image and image.filename:  # 检查 image 是否存在并且有文件名
        file_ext = os.path.splitext(image.filename)[1]

        # 确保文件扩展名合法
        if file_ext.lower() not in [".jpg", ".jpeg", ".png", ".gif"]:
            raise HTTPException(status_code=400, detail="Invalid image format")

        unique_filename = str(uuid.uuid4()) + file_ext
        file_path = os.path.join("frontend", "images", unique_filename)

        # 保存新图片
        with open(file_path, "wb") as buffer:
            copyfileobj(image.file, buffer)

        # 删除旧图片（如果存在）
        if db_product.image:
            old_image_path = os.path.join("frontend", "images", db_product.image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        # 更新数据库中的图片字段
        db_product.image = unique_filename

    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/api/products/{pid}")
def delete_product(pid: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.pid == pid).first()

    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    if db_product.image:
        old_image_path = os.path.join("frontend", "images", db_product.image)
        if os.path.exists(old_image_path):
            os.remove(old_image_path)

    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}

@app.get("/api/products/{pid}")
def get_details(pid: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.pid == pid).first()
    # current_category = db.query(Category).filter(Category.catid == product.catid).first()
    if product:
        return  {
            "pid": product.pid,
            "name": product.name,
            "catid": product.catid,
            "price": product.price,
            "description": product.description,
            "image": product.image
        }
    return {"error": "Product not found"}

@app.get("/api/products/category/{catid}")
def get_products_by_category(catid: int, db: Session = Depends(get_db)):
    return db.query(Product).filter(Product.catid == catid).all()


# 简易 session 存储：建议后期替换为 Redis 或数据库
session_store = {}

@app.post("/api/register")
async def register(
            request: Request,  # 改为接收 JSON
             session_token: str = Cookie(None),
             db: Session = Depends(get_db),
             ):
    data = await request.json()
    print("data", data)
    # 手动验证字段
    if not all(key in data for key in ["email", "password", "csrf_token"]):
        raise HTTPException(status_code=400)
    csrf_token = data.get("csrf_token")
    user = UserCreate(email=data["email"], password=data["password"])
    user_info = session_store.get(session_token)
    token_key = user_info["email"] if user_info else "guest"
    if not validate_csrf_token(token_key or "guest", csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    if db.query(User).filter(User.email == user.email).first():
        return {"error": "Email already registered"}

    hashed_pwd = get_password_hash(user.password)
    db_user = User(email=user.email, password=hashed_pwd)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    db.close()
    return {"message": "User registered successfully"}

@app.post("/api/login")
async def login(request: Request, response: Response,
    session_token: str = Cookie(None),db: Session = Depends(get_db)):
    data = await request.json()
    if not all(key in data for key in ["email", "password", "csrf_token"]):
        raise HTTPException(status_code=400)
    csrf_token = data.get("csrf_token")
    user = UserCreate(email=data["email"], password=data["password"])
    user_info = session_store.get(session_token)
    token_key = user_info["email"] if user_info else "guest"
    if not validate_csrf_token(token_key or 'guest', csrf_token):
        raise HTTPException(status_code=403, detail='Invalid CSRF token')

    db_user = db.query(User).filter(User.email == user.email).first()
    db.close()

    if not db_user or not verify_password(user.password, db_user.password):
        return {"error": "Invalid email or password"}

    session_token = str(uuid.uuid4())
    session_store[session_token] = {"email": user.email, "is_admin": db_user.is_admin}
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="session_token", value=session_token, httponly=True)
    return response

@app.get("/api/logout")
def logout(response: Response):
    response = RedirectResponse(url="/")
    response.delete_cookie("session_token")
    # response.delete_cookie("session_token")
    return response


@app.post("/api/change-password")
def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    csrf_token: str = Form(...),
    session_token: str = Cookie(None),
    response: Response = None,
    db: Session = Depends(get_db)
):
    user_info = session_store.get(session_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not validate_csrf_token(user_info['email'], csrf_token):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    db_user = db.query(User).filter(User.email == user_info["email"]).first()
    if not db_user or not verify_password(old_password, db_user.password):
        raise HTTPException(status_code=403, detail="Incorrect current password")

    db_user.password = get_password_hash(new_password)
    db.commit()

    # 清除登录态，强制重新登录
    session_store.pop(session_token)
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    return response


@app.post("/api/orders/create")
async def create_order(
    request: Request,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not user:
        raise HTTPException(status_code=401, detail="Please login first")
        
    data = await request.json()
    items = data.get("items", [])
    
    # 验证商品并计算总价
    total_price = 0
    order_items = []
    
    for item in items:
        product = db.query(Product).filter(Product.pid == item["pid"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item['pid']} not found")
            
        order_items.append({
            "pid": product.pid,
            "quantity": item["quantity"],
            "price": product.price
        })
        total_price += product.price * item["quantity"]
    
    # 生成订单摘要
    salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    order_data = {
        "merchant_email": "sb-61qba40343014@business.example.com",
        "currency": "USD",
        "items": order_items,
        "total_price": total_price
    }
    
    digest = generate_order_digest(order_data, salt)
    
    # 创建订单
    order = Order(
        userid=user["id"],
        total_price=total_price,
        digest=f"{salt}:{digest}"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # 创建订单项
    for item in order_items:
        order_item = OrderItem(
            orderid=order.orderid,
            pid=item["pid"],
            quantity=item["quantity"],
            price=item["price"]
        )
        db.add(order_item)
    
    db.commit()
    
    return {
        "orderid": order.orderid,
        "digest": order.digest,
        "total_price": total_price
    }

@app.post("/api/paypal/webhook")
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """处理 PayPal IPN 通知"""
    data = await request.form()
    
    # 验证 PayPal 通知的真实性
    verify_url = "https://www.sandbox.paypal.com/cgi-bin/webscr"
    async with httpx.AsyncClient() as client:
        verify_data = dict(data)
        verify_data["cmd"] = "_notify-validate"
        response = await client.post(verify_url, data=verify_data)
        
        if response.text != "VERIFIED":
            raise HTTPException(status_code=400, detail="Invalid PayPal notification")
    
    # 解析订单信息
    custom = data.get("custom", "")
    transaction_id = data.get("txn_id")
    payment_status = data.get("payment_status")
    
    if not custom or ":" not in custom:
        raise HTTPException(status_code=400, detail="Invalid order digest")
    
    salt, stored_digest = custom.split(":", 1)
    
    # 查找并更新订单
    order = db.query(Order).filter(Order.digest == custom).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if order.status != "pending":
        return {"message": "Order already processed"}
    
    # 更新订单状态
    if payment_status == "Completed":
        order.status = "paid"
        order.paypal_transaction_id = transaction_id
        db.commit()
        
    return {"message": "Payment processed successfully"}


def generate_order_digest(order_data, salt):
    """生成订单摘要"""
    data = f"{order_data['merchant_email']}{order_data['currency']}{salt}"
    for item in order_data['items']:
        data += f"{item['pid']}{item['quantity']}{item['price']}"
    data += str(order_data['total_price'])
    
    return hmac.new(
        salt.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
