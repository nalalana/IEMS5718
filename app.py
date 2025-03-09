import os
import uuid
from shutil import copyfileobj

from fastapi import FastAPI, File, UploadFile, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from database import SessionLocal, Category, Product

app = FastAPI()


app.mount("/static", StaticFiles(directory="frontend"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def root():
    # 返回 frontend/index.html 文件
    file_path = os.path.join(os.getcwd(), 'frontend', 'index.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

@app.get("/admin/categories", response_class=HTMLResponse)
def category_form():
    file_path = os.path.join(os.getcwd(), 'frontend', 'category_form.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content


@app.get("/admin/products", response_class=HTMLResponse)
def product_form():
    file_path = os.path.join(os.getcwd(), 'frontend', 'product_form.html')
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return content


@app.get("/products/{pid}", response_class=HTMLResponse)
def get_product_details(pid: int, db: Session = Depends(get_db)):
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


@app.post("/api/categories/")
def create_category(name: str = Form(...), db: Session = Depends(get_db)):
    db_category = Category(name=name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@app.get("/api/categories/")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@app.post("/api/products/")
async def create_product(
        catid: int = Form(...),
        name: str = Form(...),
        price: float = Form(...),
        description: str = Form(...),
        image: UploadFile = File(...),
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
        db: Session = Depends(get_db)
):
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



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
